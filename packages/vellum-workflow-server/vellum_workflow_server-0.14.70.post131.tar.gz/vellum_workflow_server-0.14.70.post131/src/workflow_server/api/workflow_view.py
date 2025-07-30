from datetime import datetime
import importlib
import inspect
import json
import logging
from multiprocessing import Queue, set_start_method
import os
import pkgutil
from queue import Empty
import sys
import time
import traceback
from uuid import uuid4
from typing import Generator, Iterator, Union

from flask import Blueprint, Response, current_app as app, request, stream_with_context
from pydantic import ValidationError

from vellum.workflows.nodes import BaseNode
from workflow_server.config import MEMORY_LIMIT_MB
from workflow_server.core.events import (
    STREAM_FINISHED_EVENT,
    VEMBDA_EXECUTION_FULFILLED_EVENT_NAME,
    VembdaExecutionFulfilledBody,
    VembdaExecutionFulfilledEvent,
    VembdaExecutionInitiatedBody,
    VembdaExecutionInitiatedEvent,
)
from workflow_server.core.executor import stream_node_pebble_timeout, stream_workflow_process_timeout
from workflow_server.core.workflow_executor_context import (
    DEFAULT_TIMEOUT_SECONDS,
    NodeExecutorContext,
    WorkflowExecutorContext,
)
from workflow_server.utils.oom_killer import get_is_oom_killed
from workflow_server.utils.system_utils import (
    get_active_process_count,
    increment_process_count,
    wait_for_available_process,
)
from workflow_server.utils.utils import convert_json_inputs_to_vellum, get_version

bp = Blueprint("exec", __name__)

set_start_method("fork", force=True)

logger = logging.getLogger(__name__)

CUSTOM_NODES_DIRECTORY = "vellum_custom_nodes"


@bp.route("/stream", methods=["POST"])
def stream_workflow_route() -> Response:
    data = request.get_json()

    try:
        context = get_workflow_request_context(data)
    except ValidationError as e:
        error_message = e.errors()[0]["msg"]
        error_location = e.errors()[0]["loc"]

        return Response(
            json.dumps({"detail": f"Invalid context: {error_message} at {error_location}"}),
            status=400,
            content_type="application/json",
        )

    logger.info(
        f"Starting workflow stream, execution ID: {context.execution_id}, "
        f"process count: {get_active_process_count()}"
    )

    # Create this event up here so timestamps are fully from the start to account for any unknown overhead
    vembda_initiated_event = VembdaExecutionInitiatedEvent(
        id=uuid4(),
        timestamp=datetime.now(),
        trace_id=context.trace_id,
        span_id=context.execution_id,
        body=VembdaExecutionInitiatedBody.model_validate(get_version()),
        parent=None,
    )

    process_output_queue: Queue[dict] = Queue()

    # We can exceed the concurrency count currently with long running workflows due to a knative issue. So here
    # if we detect a memory problem just exit us early
    if not wait_for_available_process():
        return Response(
            stream_with_context(
                startup_error_generator(
                    context=context,
                    message=f"Workflow server concurrent request rate exceeded. "
                    f"Process count: {get_active_process_count()}",
                    vembda_initiated_event=vembda_initiated_event,
                )
            ),
            status=200,
            content_type='application/x-ndjson"',
            headers={
                "X-Vellum-SDK-Version": vembda_initiated_event.body.sdk_version,
                "X-Vellum-Server-Version": vembda_initiated_event.body.server_version,
            },
        )

    try:
        process = stream_workflow_process_timeout(
            executor_context=context,
            queue=process_output_queue,
        )
        increment_process_count(1)
    except Exception as e:
        logger.exception(e)

        vembda_fulfilled_event = VembdaExecutionFulfilledEvent(
            id=uuid4(),
            timestamp=datetime.now(),
            trace_id=context.trace_id,
            span_id=context.execution_id,
            body=VembdaExecutionFulfilledBody(
                exit_code=-1,
                stderr=traceback.format_exc(),
                container_overhead_latency=context.container_overhead_latency,
            ),
            parent=None,
        )
        process_output_queue.put(vembda_fulfilled_event.model_dump(mode="json"))

    def process_events(queue: Queue) -> Iterator[Union[str, dict]]:
        event: Union[str, dict]
        loops = 0

        while True:
            loops += 1
            # Check if we timed out and kill the process if so. Set the timeout a little under what
            # the default is (30m) since the connection limit is 30m and otherwise we may not receive
            # the timeout event.
            if min(context.timeout, DEFAULT_TIMEOUT_SECONDS - 90) < (
                (time.time_ns() - context.request_start_time) / 1_000_000_000
            ):
                logger.error("Workflow timed out")

                if process and process.is_alive():
                    process.kill()

                if process:
                    increment_process_count(-1)

                yield VembdaExecutionFulfilledEvent(
                    id=uuid4(),
                    timestamp=datetime.now(),
                    trace_id=context.trace_id,
                    span_id=context.execution_id,
                    body=VembdaExecutionFulfilledBody(
                        exit_code=-1,
                        container_overhead_latency=context.container_overhead_latency,
                        timed_out=True,
                    ),
                    parent=None,
                ).model_dump(mode="json")

                break

            if get_is_oom_killed():
                logger.warning("Workflow stream OOM Kill event")

                yield VembdaExecutionFulfilledEvent(
                    id=uuid4(),
                    timestamp=datetime.now(),
                    trace_id=context.trace_id,
                    span_id=context.execution_id,
                    body=VembdaExecutionFulfilledBody(
                        exit_code=-1,
                        container_overhead_latency=context.container_overhead_latency,
                        stderr=f"Organization Workflow server has exceeded {MEMORY_LIMIT_MB}MB memory limit.",
                    ),
                    parent=None,
                ).model_dump(mode="json")

                if process and process.is_alive():
                    process.kill()
                if process:
                    increment_process_count(-1)

                break

            try:
                item = queue.get(timeout=0.1)
                event = item
            except Empty:
                # Emit waiting event if were just sitting around to attempt to keep the line
                # open to trick knative
                if loops % 20 == 0:
                    yield "WAITING"

                    if process and not process.is_alive():
                        logger.error("Workflow process exited abnormally")

                        yield VembdaExecutionFulfilledEvent(
                            id=uuid4(),
                            timestamp=datetime.now(),
                            trace_id=context.trace_id,
                            span_id=context.execution_id,
                            body=VembdaExecutionFulfilledBody(
                                exit_code=-1,
                                container_overhead_latency=context.container_overhead_latency,
                                stderr="Internal Server Error, Workflow process exited abnormally",
                            ),
                            parent=None,
                        ).model_dump(mode="json")

                        break

                continue
            except Exception as e:
                logger.exception(e)
                break

            if event == STREAM_FINISHED_EVENT:
                break
            yield event

    workflow_events = process_events(process_output_queue)

    def generator() -> Generator[str, None, None]:
        try:
            yield "\n"
            yield vembda_initiated_event.model_dump_json()
            yield "\n"
            for index, row in enumerate(workflow_events):
                yield "\n"
                if isinstance(row, dict):
                    dump = json.dumps(row)
                    yield dump
                else:
                    yield row
                yield "\n"
            # Sometimes the connections get hung after they finish with the vembda fulfilled event
            # if it happens during a knative scale down event. So we emit an END string so that
            # we don't have to do string compares on all the events for performance.
            yield "\n"
            yield "END"
            yield "\n"

            logger.info(
                f"Workflow stream completed, execution ID: {context.execution_id}, "
                f"process count: {get_active_process_count()}"
            )
        except GeneratorExit:
            app.logger.error("Client disconnected in the middle of the stream")
            return
        finally:
            try:
                if process and process.is_alive():
                    process.kill()
                if process:
                    increment_process_count(-1)
            except Exception as e:
                logger.error("Failed to kill process", e)

    resp = Response(
        stream_with_context(generator()),
        status=200,
        content_type='application/x-ndjson"',
        headers={
            "X-Vellum-SDK-Version": vembda_initiated_event.body.sdk_version,
            "X-Vellum-Server-Version": vembda_initiated_event.body.server_version,
        },
    )
    return resp


@bp.route("/stream-node", methods=["POST"])
def stream_node_route() -> Response:
    data = request.get_json()

    try:
        context = get_node_request_context(data)
    except ValidationError as e:
        error_message = e.errors()[0]["msg"]
        error_location = e.errors()[0]["loc"]
        return Response(
            json.dumps({"detail": f"Invalid context: {error_message} at {error_location}"}),
            status=400,
            content_type="application/json",
        )

    # Create this event up here so timestamps are fully from the start to account for any unknown overhead
    vembda_initiated_event = VembdaExecutionInitiatedEvent(
        id=uuid4(),
        timestamp=datetime.now(),
        trace_id=context.trace_id,
        span_id=context.execution_id,
        body=VembdaExecutionInitiatedBody.model_validate(get_version()),
        parent=None,
    )

    app.logger.debug(f"Node stream received {data.get('execution_id')}")

    pebble_queue: Queue[dict] = Queue()
    stream_future = stream_node_pebble_timeout(
        executor_context=context,
        queue=pebble_queue,
    )

    def node_events() -> Iterator[dict]:
        while True:
            try:
                event = pebble_queue.get(timeout=context.timeout)

            except Empty:
                if stream_future.exception() is not None:
                    # This happens when theres a problem with the stream function call
                    # itself not the workflow runner
                    vembda_fulfilled_event = VembdaExecutionFulfilledEvent(
                        id=uuid4(),
                        timestamp=datetime.now(),
                        trace_id=context.trace_id,
                        span_id=context.execution_id,
                        body=VembdaExecutionFulfilledBody(
                            exit_code=-1,
                            stderr="Internal Server Error",
                            container_overhead_latency=context.container_overhead_latency,
                        ),
                        parent=None,
                    )
                    yield vembda_fulfilled_event.model_dump(mode="json")
                    app.logger.exception(stream_future.exception())
                    break
                else:
                    continue

            yield event
            if event.get("name") == VEMBDA_EXECUTION_FULFILLED_EVENT_NAME:
                break

    def generator() -> Generator[str, None, None]:
        yield json.dumps(vembda_initiated_event.model_dump(mode="json"))

        for index, row in enumerate(node_events()):
            yield "\n"
            yield json.dumps(row)

    resp = Response(
        stream_with_context(generator()),
        status=200,
        content_type='application/x-ndjson"',
        headers={
            "X-Vellum-SDK-Version": vembda_initiated_event.body.sdk_version,
            "X-Vellum-Server-Version": vembda_initiated_event.body.server_version,
        },
    )
    return resp


@bp.route("/version", methods=["GET"])
def get_version_route() -> tuple[dict, int]:
    resp = get_version()

    try:
        # Discover nodes in the container
        nodes = []

        # Look for custom_nodes directory in the container
        custom_nodes_path = os.path.join(os.getcwd(), CUSTOM_NODES_DIRECTORY)
        if os.path.exists(custom_nodes_path):
            # Add the custom_nodes directory to Python path so we can import from it
            sys.path.append(os.path.dirname(custom_nodes_path))

            # Import all Python files in the custom_nodes directory
            for _, name, _ in pkgutil.iter_modules([custom_nodes_path]):
                try:
                    module = importlib.import_module(f"{CUSTOM_NODES_DIRECTORY}.{name}")
                    for _, obj in inspect.getmembers(module):
                        # Look for classes that inherit from BaseNode
                        if inspect.isclass(obj) and obj != BaseNode and issubclass(obj, BaseNode):
                            nodes.append(
                                {
                                    "id": str(uuid4()),
                                    "module": CUSTOM_NODES_DIRECTORY,
                                    "name": obj.__name__,
                                    "label": obj().label if hasattr(obj, "label") else obj.__name__,  # type: ignore
                                    "description": inspect.getdoc(obj) or "",
                                }
                            )
                except Exception as e:
                    logger.warning(f"Failed to load node from module {name}: {str(e)}", exc_info=True)

        resp["nodes"] = nodes
    except Exception as e:
        logger.exception(f"Failed to discover nodes: {str(e)}")
        resp["nodes"] = []

    return resp, 200


def get_workflow_request_context(data: dict) -> WorkflowExecutorContext:
    # not sure if this is the filter we want to pass forward?
    context_data = {
        **data,
        "inputs": convert_json_inputs_to_vellum(data.get("inputs") or []),
        "trace_id": uuid4(),
        "request_start_time": time.time_ns(),
    }

    return WorkflowExecutorContext.model_validate(context_data)


def get_node_request_context(data: dict) -> NodeExecutorContext:
    context_data = {
        **data,
        "inputs": convert_json_inputs_to_vellum(data["inputs"]),
        "trace_id": uuid4(),
        "request_start_time": time.time_ns(),
    }

    return NodeExecutorContext.model_validate(context_data)


def startup_error_generator(
    vembda_initiated_event: VembdaExecutionInitiatedEvent, message: str, context: WorkflowExecutorContext
) -> Generator[str, None, None]:
    try:
        yield "\n"
        yield vembda_initiated_event.model_dump_json()
        yield "\n"
        yield VembdaExecutionFulfilledEvent(
            id=uuid4(),
            timestamp=datetime.now(),
            trace_id=context.trace_id,
            span_id=context.execution_id,
            body=VembdaExecutionFulfilledBody(
                exit_code=-1,
                container_overhead_latency=context.container_overhead_latency,
                stderr=message,
            ),
            parent=None,
        ).model_dump_json()
        yield "\n"
        yield "END"
        yield "\n"

        logger.error("Workflow stream could not start from resource constraints")
    except GeneratorExit:
        app.logger.error("Client disconnected in the middle of the stream")
        return
