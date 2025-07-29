import logging
import re
from unittest.mock import patch
from uuid import UUID

from workflow_server.server import create_app


def test_version_route():
    flask_app = create_app()

    with flask_app.test_client() as test_client:
        response = test_client.get("/workflow/version")
        assert response.status_code == 200
        assert re.match(r"[0-9]*\.[0-9]*\.[0-9]*", response.json["sdk_version"])
        assert response.json["server_version"] == "local"


def test_version_route__with_single_node_file(tmp_path):
    # GIVEN a temporary custom_nodes directory with a test node
    custom_nodes_dir = tmp_path / "vellum_custom_nodes"
    custom_nodes_dir.mkdir()

    node_file = custom_nodes_dir / "test_node.py"
    node_file.write_text(
        """
from vellum.workflows.nodes import BaseNode

class TestNode(BaseNode):
    \"""A test node for processing data.

    This is a detailed description of what the node does.
    \"""
    label = "Test Node"
"""
    )

    flask_app = create_app()

    # WHEN we make a request to the version route
    with patch("os.getcwd", return_value=str(tmp_path)), flask_app.test_client() as test_client:
        response = test_client.get("/workflow/version")

    # THEN we should get a successful response
    assert response.status_code == 200

    # AND we should find exactly one node
    nodes = response.json["nodes"]
    assert len(nodes) == 1

    # AND the node should have the correct metadata
    node = nodes[0]
    assert UUID(node["id"])
    assert node["module"] == "vellum_custom_nodes"
    assert node["name"] == "TestNode"
    assert node["label"] == "Test Node"
    assert "A test node for processing data." in node["description"]
    assert "This is a detailed description" in node["description"]


def test_version_route__with_nodes_in_multiple_files(tmp_path):
    # GIVEN a temporary custom_nodes directory
    custom_nodes_dir = tmp_path / "vellum_custom_nodes"
    custom_nodes_dir.mkdir()

    # AND a first node file
    first_node_file = custom_nodes_dir / "first_node.py"
    first_node_file.write_text(
        """
from vellum.workflows.nodes import BaseNode

class SomeNode(BaseNode):
    \"""This is Some Node.\"""
    label = "Some node"
"""
    )

    # AND a second node file
    second_node_file = custom_nodes_dir / "second_node.py"
    second_node_file.write_text(
        """
from vellum.workflows.nodes import BaseNode

class SomeOtherNode(BaseNode):
    \"""This is Some Other Node.\"""
    label = "Some other node"
"""
    )

    flask_app = create_app()

    # WHEN we make a request to the version route
    with patch("os.getcwd", return_value=str(tmp_path)), flask_app.test_client() as test_client:
        response = test_client.get("/workflow/version")

    # THEN we should get a successful response
    assert response.status_code == 200

    # AND we should find both nodes
    nodes = response.json["nodes"]
    assert len(nodes) == 2

    # AND the first node should have correct metadata
    some_node = nodes[0]
    assert some_node["label"] == "Some node"
    assert some_node["description"] == "This is Some Node."
    assert UUID(some_node["id"])
    assert some_node["module"] == "vellum_custom_nodes"

    # AND the second node should have correct metadata
    some_other_node = nodes[1]
    assert some_other_node["label"] == "Some other node"
    assert some_other_node["description"] == "This is Some Other Node."
    assert UUID(some_other_node["id"])
    assert some_other_node["module"] == "vellum_custom_nodes"


def test_version_route__no_custom_nodes_dir(tmp_path):
    # GIVEN a Flask application and an empty temp directory
    flask_app = create_app()

    # WHEN we make a request to the version route
    with patch("os.getcwd", return_value=str(tmp_path)), flask_app.test_client() as test_client:
        response = test_client.get("/workflow/version")

    # THEN we should get a successful response
    assert response.status_code == 200

    # AND the nodes list should be empty
    assert response.json["nodes"] == []


def test_version_route__with_multiple_nodes_in_file(tmp_path):
    # Create a temporary custom_nodes directory with multiple nodes in one file
    custom_nodes_dir = tmp_path / "vellum_custom_nodes"
    custom_nodes_dir.mkdir()

    # Create a test node file with multiple nodes
    node_file = custom_nodes_dir / "multiple_nodes.py"
    node_file.write_text(
        """
from vellum.workflows.nodes import BaseNode

class ProcessingNode(BaseNode):
    \"""Processes input data.\"""
    label = "Processing Node"

class TransformationNode(BaseNode):
    \"""Transforms data format.\"""
    label = "Transformation Node"

# This class should not be discovered
class HelperClass:
    pass
"""
    )

    flask_app = create_app()

    # Mock the current working directory to point to our temp directory
    with patch("os.getcwd", return_value=str(tmp_path)), flask_app.test_client() as test_client:
        response = test_client.get("/workflow/version")

        assert response.status_code == 200
        nodes = response.json["nodes"]
        assert len(nodes) == 2

        # Nodes should be discovered regardless of their order in the file
        node_names = {node["name"] for node in nodes}
        assert node_names == {"ProcessingNode", "TransformationNode"}


def test_version_route__with_invalid_node_file(tmp_path, caplog):
    caplog.set_level(logging.WARNING)

    # GIVEN a temporary custom_nodes directory
    custom_nodes_dir = tmp_path / "vellum_custom_nodes"
    custom_nodes_dir.mkdir()

    # AND a valid node file
    valid_node_file = custom_nodes_dir / "valid_node.py"
    valid_node_file.write_text(
        """
from vellum.workflows.nodes import BaseNode

class SomeNode(BaseNode):
    \"\"\"This is Some Node.\"\"\"
    label = "Some node"
"""
    )

    # AND an invalid node file with syntax error of missing colon in the class
    invalid_node_file = custom_nodes_dir / "invalid_node.py"
    invalid_node_file.write_text(
        """
from vellum.workflows.nodes import BaseNode

class BrokenNode(BaseNode)
    \"\"\"This node has a syntax error.\"\"\"
    label = "Broken Node"
"""
    )

    flask_app = create_app()

    # WHEN we make a request to the version route
    with patch("os.getcwd", return_value=str(tmp_path)), flask_app.test_client() as test_client:
        response = test_client.get("/workflow/version")

    # THEN we should get a successful response
    assert response.status_code == 200

    # AND we should find only the valid node
    nodes = response.json["nodes"]
    assert len(nodes) == 1

    # AND the valid node should have correct metadata
    valid_node = nodes[0]
    assert valid_node["label"] == "Some node"
    assert valid_node["description"] == "This is Some Node."
    assert UUID(valid_node["id"])
    assert valid_node["module"] == "vellum_custom_nodes"

    # AND the error should be logged with full traceback
    assert len(caplog.records) > 0
    error_message = caplog.records[0].message
    assert "Failed to load node from module invalid_node" in error_message
    assert "invalid_node.py, line 4" in error_message
