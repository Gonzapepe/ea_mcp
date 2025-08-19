#!/usr/bin/env python3
from unittest.mock import patch, MagicMock
import sys
import os
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from server import (
    create_sequence_diagram, create_class_diagram, 
    create_use_case_diagram, create_activity_diagram,
    _create_lifeline, create_actor_lifeline, create_boundary_lifeline,
    create_control_lifeline, create_entity_lifeline,
    create_database_lifeline, create_use_case_lifeline
)
from exceptions import EAConnectorError

@pytest.fixture
def mock_connector():
    """Fixture to mock the server's connector."""
    with patch('server.connector') as mock_conn:
        yield mock_conn

def test_sequence_diagram_creation(mock_connector):
    """Test sequence diagram creation"""
    mock_connector.create_diagram.return_value = {"guid": "test-guid-123"}
    mock_connector.add_element_to_diagram.return_value = {"guid": "element-guid-1"}

    test_args = {
        "package_guid": "test-pkg-123",
        "name": "Test Sequence",
        "elements": [{"name": "User", "type": "Actor"}]
    }
    result = create_sequence_diagram(test_args)

    assert result["status"] == "success"
    assert result["data"]["diagram_guid"] == "test-guid-123"
    mock_connector.create_diagram.assert_called_once()
    mock_connector.add_element_to_diagram.assert_called_once()
    mock_connector.auto_layout_diagram.assert_called_once()

def test_class_diagram_creation_no_classes(mock_connector):
    """Test class diagram creation with no classes."""
    mock_connector.create_diagram.return_value = {"guid": "test-guid-456"}

    test_args = {
        "package_guid": "test-pkg-123",
        "name": "Test Classes",
        "classes": []
    }
    result = create_class_diagram(test_args)

    assert result["status"] == "success"
    assert result["data"]["diagram_guid"] == "test-guid-456"
    mock_connector.add_element_to_diagram.assert_not_called()

def test_use_case_diagram_creation_element_fails(mock_connector):
    """Test use case diagram creation when adding an element fails."""
    mock_connector.create_diagram.return_value = {"guid": "test-guid-789"}
    mock_connector.add_element_to_diagram.side_effect = EAConnectorError("Element creation failed")

    test_args = {
        "package_guid": "test-pkg-123",
        "name": "Test Use Cases",
        "actors": ["User"],
        "use_cases": ["Login"]
    }
    result = create_use_case_diagram(test_args)

    assert result["status"] == "error"
    assert "Element creation failed" in result["message"]

def test_activity_diagram_creation(mock_connector):
    """Test activity diagram creation"""
    mock_connector.create_diagram.return_value = {"guid": "test-guid-abc"}
    mock_connector.add_element_to_diagram.side_effect = [{"guid": "activity-guid-1"}, {"guid": "decision-guid-1"}]

    test_args = {
        "package_guid": "test-pkg-123",
        "name": "Test Activities",
        "activities": ["Start"],
        "decisions": ["Valid?"]
    }
    result = create_activity_diagram(test_args)

    assert result["status"] == "success"
    assert len(result["data"]["activities"]) == 1
    assert len(result["data"]["decisions"]) == 1

def test_sequence_diagram_creation_connection_fails(mock_connector):
    """Test sequence diagram creation when EA connection fails"""
    mock_connector.connect.side_effect = EAConnectorError("Connection failed")

    test_args = {
        "package_guid": "test-pkg-123",
        "name": "Test Sequence"
    }
    result = create_sequence_diagram(test_args)

    assert result["status"] == "error"
    assert "Connection failed" in result["message"]
    mock_connector.create_diagram.assert_not_called()

def test_sequence_diagram_creation_diagram_fails(mock_connector):
    """Test sequence diagram creation when the diagram itself fails to be created"""
    mock_connector.create_diagram.side_effect = EAConnectorError("Diagram creation failed")

    test_args = {
        "package_guid": "test-pkg-123",
        "name": "Test Sequence"
    }
    result = create_sequence_diagram(test_args)

    assert result["status"] == "error"
    assert "Diagram creation failed" in result["message"]
    mock_connector.add_element_to_diagram.assert_not_called()

def test_create_lifeline_success(mock_connector):
    """Test the internal _create_lifeline helper."""
    mock_connector.add_element_to_diagram.return_value = {"guid": "lifeline-guid"}

    result = _create_lifeline("diag-guid", "TestLifeline", "actor")
    
    assert result["status"] == "success"
    assert result["data"]["element_guid"] == "lifeline-guid"
    mock_connector.add_element_to_diagram.assert_called_with("diag-guid", "TestLifeline", "Object", "actor")

def test_create_lifeline_fails(mock_connector):
    """Test _create_lifeline when element creation fails."""
    mock_connector.add_element_to_diagram.side_effect = EAConnectorError("Element creation failed")

    result = _create_lifeline("diag-guid", "TestLifeline", "boundary")

    assert result["status"] == "error"
    assert "Element creation failed" in result["message"]

@pytest.mark.parametrize("lifeline_func,lifeline_type", [
    (create_actor_lifeline, "actor"),
    (create_boundary_lifeline, "boundary"),
    (create_control_lifeline, "control"),
    (create_entity_lifeline, "entity"),
    (create_database_lifeline, "database"),
    (create_use_case_lifeline, "use_case"),
])
def test_all_lifeline_creation_tools(mock_connector, lifeline_func, lifeline_type):
    """Test all public lifeline creation tools."""
    with patch('server._create_lifeline') as mock_create_lifeline:
        mock_create_lifeline.return_value = {"status": "success"}
        
        args = {"diagram_guid": "diag-123", "name": f"Test {lifeline_type}"}
        result = lifeline_func(args)
        
        assert result["status"] == "success"
        mock_create_lifeline.assert_called_once_with(args["diagram_guid"], args["name"], lifeline_type)

def test_create_lifeline_fails(mock_connector):
    """Test _create_lifeline when element creation fails."""
    mock_connector.add_element_to_diagram.side_effect = EAConnectorError("Element creation failed")

    result = _create_lifeline("diag-guid", "TestLifeline", "boundary")

    assert result["status"] == "error"
    assert "Element creation failed" in result["message"]

@pytest.mark.parametrize("lifeline_func,lifeline_type", [
    (create_actor_lifeline, "actor"),
    (create_boundary_lifeline, "boundary"),
    (create_control_lifeline, "control"),
    (create_entity_lifeline, "entity"),
    (create_database_lifeline, "database"),
    (create_use_case_lifeline, "use_case"),
])
def test_all_lifeline_creation_tools(mock_connector, lifeline_func, lifeline_type):
    """Test all public lifeline creation tools."""
    with patch('server._create_lifeline') as mock_create_lifeline:
        mock_create_lifeline.return_value = {"status": "success"}
        
        args = {"diagram_guid": "diag-123", "name": f"Test {lifeline_type}"}
        result = lifeline_func(args)
        
        assert result["status"] == "success"
        mock_create_lifeline.assert_called_once_with(args["diagram_guid"], args["name"], lifeline_type)
