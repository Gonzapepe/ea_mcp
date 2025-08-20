#!/usr/bin/env python3
import sys
import os
import pytest
import logging
from unittest.mock import patch, MagicMock

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server import create_class_diagram, create_sequence_diagram
from ea_connector import EAConnector
from exceptions import EAConnectorError

@pytest.fixture
def mock_connector():
    """Fixture to mock the server's connector."""
    with patch('server.connector') as mock_conn:
        yield mock_conn

@pytest.fixture(autouse=True)
def configure_caplog(caplog):
    """Configure caplog to capture INFO level logs."""
    caplog.set_level(logging.INFO)

def test_server_tool_logging_success(mock_connector, caplog):
    """Test that tool execution success is logged correctly."""
    mock_connector.create_diagram.return_value = {"guid": "test-guid-123"}
    
    args = {
        "package_guid": "pkg-guid-456",
        "name": "TestClassDiagram",
        "classes": []
    }
    
    result = create_class_diagram(args)
    
    assert result['status'] == 'success'
    
    assert "Executing tool: create_class_diagram" in caplog.text
    assert "Tool create_class_diagram executed successfully." in caplog.text
    assert "error" not in caplog.text.lower()

def test_server_tool_logging_error(mock_connector, caplog):
    """Test that tool execution errors are logged correctly."""
    mock_connector.connect.side_effect = EAConnectorError("Connection failed", details="COM object not found")
    
    args = {
        "package_guid": "pkg-guid-789",
        "name": "TestSequenceDiagram"
    }
    
    result = create_sequence_diagram(args)
    
    assert result['status'] == 'error'
    
    assert "Executing tool: create_sequence_diagram" in caplog.text
    assert "Error in create_sequence_diagram: Connection failed - Details: COM object not found" in caplog.text
    assert "executed successfully" not in caplog.text

@patch('win32com.client.Dispatch')
def test_ea_connector_logging_connect_success(mock_dispatch, caplog):
    """Test logging on successful EA connection."""
    mock_ea_app = MagicMock()
    mock_dispatch.return_value = mock_ea_app
    
    connector = EAConnector()
    
    # Mock the repository and OpenFile method
    mock_repo = MagicMock()
    mock_ea_app.Repository = mock_repo
    
    with patch.dict(os.environ, {"EA_FILE_PATH": "C:/test.eapx"}):
        connector.connect()

    assert "Attempting to connect to Enterprise Architect COM interface." in caplog.text
    assert "Connected to EA successfully." in caplog.text
    assert "Opening EA file: C:/test.eapx" in caplog.text
    assert "Successfully opened EA file: C:/test.eapx" in caplog.text

@patch('win32com.client.Dispatch')
def test_ea_connector_logging_create_diagram_error(mock_dispatch, caplog):
    """Test logging when creating a diagram fails."""
    mock_ea_app = MagicMock()
    mock_dispatch.return_value = mock_ea_app
    
    connector = EAConnector()
    
    # Mock the repository to raise an error
    mock_repo = MagicMock()
    mock_repo.GetPackageByGuid.side_effect = Exception("Test COM error")
    mock_ea_app.Repository = mock_repo
    
    with patch.dict(os.environ, {"EA_FILE_PATH": "C:/test.eapx"}):
        connector.connect()

    # The create_diagram method should raise EAConnectorError when it catches Exception
    with pytest.raises(EAConnectorError):
        connector.create_diagram("guid-123", "TestDiagram", "Sequence")

    # Check that the log message was captured (this is the main test requirement)
    assert "Creating diagram 'TestDiagram' of type 'Sequence' in package 'guid-123'." in caplog.text
