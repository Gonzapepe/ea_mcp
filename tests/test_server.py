#!/usr/bin/env python3
from unittest.mock import patch
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from server import create_sequence_diagram, create_class_diagram, create_use_case_diagram, create_activity_diagram, DIAGRAM_TYPES, ELEMENT_TYPES
from ea_connector import EAConnector

@patch('server.connector')
def test_sequence_diagram_creation(mock_connector):
    """Test sequence diagram creation"""
    mock_connector.connect.return_value = True
    mock_connector.create_diagram.return_value = {
        "guid": "test-guid-123",
    }
    mock_connector.add_element_to_diagram.return_value = {
        "guid": "element-guid-1"
    }
    mock_connector.auto_layout_diagram.return_value = True

    test_args = {
        "package_guid": "test-pkg-123",
        "name": "Test Sequence",
        "elements": [
            {"name": "User", "type": "Actor"},
        ]
    }

    result = create_sequence_diagram(test_args)

    assert result["status"] == "success"
    assert result["diagram_guid"] == "test-guid-123"
    mock_connector.create_diagram.assert_called_once()
    mock_connector.add_element_to_diagram.assert_called_once()
    mock_connector.auto_layout_diagram.assert_called_once()

@patch('server.connector')
def test_class_diagram_creation(mock_connector):
    """Test class diagram creation"""
    mock_connector.connect.return_value = True
    mock_connector.create_diagram.return_value = {"guid": "test-guid-456"}
    mock_connector.add_element_to_diagram.return_value = {"guid": "class-guid-1"}
    mock_connector.auto_layout_diagram.return_value = True

    test_args = {
        "package_guid": "test-pkg-123",
        "name": "Test Classes",
        "classes": [{"name": "User"}]
    }

    result = create_class_diagram(test_args)
    assert result["status"] == "success"
    assert result["diagram_guid"] == "test-guid-456"

@patch('server.connector')
def test_use_case_diagram_creation(mock_connector):
    """Test use case diagram creation"""
    mock_connector.connect.return_value = True
    mock_connector.create_diagram.return_value = {"guid": "test-guid-789"}
    mock_connector.add_element_to_diagram.side_effect = [{"guid": "actor-guid-1"}, {"guid": "uc-guid-1"}]
    mock_connector.auto_layout_diagram.return_value = True

    test_args = {
        "package_guid": "test-pkg-123",
        "name": "Test Use Cases",
        "actors": ["User"],
        "use_cases": ["Login"]
    }

    result = create_use_case_diagram(test_args)
    assert result["status"] == "success"
    assert len(result["actors"]) == 1
    assert len(result["use_cases"]) == 1

@patch('server.connector')
def test_activity_diagram_creation(mock_connector):
    """Test activity diagram creation"""
    mock_connector.connect.return_value = True
    mock_connector.create_diagram.return_value = {"guid": "test-guid-abc"}
    mock_connector.add_element_to_diagram.side_effect = [{"guid": "activity-guid-1"}, {"guid": "decision-guid-1"}]
    mock_connector.auto_layout_diagram.return_value = True

    test_args = {
        "package_guid": "test-pkg-123",
        "name": "Test Activities",
        "activities": ["Start"],
        "decisions": ["Valid?"]
    }

    result = create_activity_diagram(test_args)
    assert result["status"] == "success"
    assert len(result["activities"]) == 1
    assert len(result["decisions"]) == 1

@patch('server.connector')
def test_sequence_diagram_creation_connection_fails(mock_connector):
    """Test sequence diagram creation when EA connection fails"""
    mock_connector.connect.return_value = False

    test_args = {
        "package_guid": "test-pkg-123",
        "name": "Test Sequence",
        "elements": [{"name": "User", "type": "Actor"}]
    }

    result = create_sequence_diagram(test_args)

    assert result["status"] == "error"
    assert "Failed to connect to Enterprise Architect" in result["message"]
    mock_connector.create_diagram.assert_not_called()

@patch('server.connector')
def test_sequence_diagram_creation_diagram_fails(mock_connector):
    """Test sequence diagram creation when the diagram itself fails to be created"""
    mock_connector.connect.return_value = True
    mock_connector.create_diagram.return_value = None  # Simulate diagram creation failure

    test_args = {
        "package_guid": "test-pkg-123",
        "name": "Test Sequence",
        "elements": [{"name": "User", "type": "Actor"}]
    }

    result = create_sequence_diagram(test_args)

    assert result["status"] == "error"
    assert result["message"] == "Failed to create diagram"
    mock_connector.add_element_to_diagram.assert_not_called()
