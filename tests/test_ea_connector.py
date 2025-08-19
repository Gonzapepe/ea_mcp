import pytest
from unittest.mock import MagicMock, patch
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ea_connector import EAConnector
from exceptions import EAConnectorError
import os

@pytest.fixture
def mock_win32com(mocker):
    """Fixture to mock win32com.client."""
    return mocker.patch('win32com.client.Dispatch')

@pytest.fixture
def mock_ea_app(mocker):
    """Fixture to create a mock EA Application object."""
    mock_app = MagicMock()
    mock_app.Repository = MagicMock()
    return mock_app

@pytest.fixture
def connector(mock_win32com, mock_ea_app):
    """Fixture to provide an EAConnector instance with a mocked EA App."""
    mock_win32com.return_value = mock_ea_app
    return EAConnector()

def test_connect_success(mocker, connector, mock_win32com, mock_ea_app):
    """Test successful connection to an EA repository."""
    mocker.patch.dict(os.environ, {"EA_FILE_PATH": "dummy_path"})
    result = connector.connect("dummy_path")
    mock_win32com.assert_called_once_with('EA.App')
    mock_ea_app.Repository.OpenFile.assert_called_once_with('dummy_path')
    assert result is None

def test_connect_failure_no_env_var(mocker, connector):
    """Test connection failure when EA_FILE_PATH is not set."""
    mocker.patch.dict(os.environ, {}, clear=True)
    mocker.patch('dotenv.load_dotenv')
    with pytest.raises(EAConnectorError, match="EA_FILE_PATH environment variable not set"):
        connector.connect()

def test_connect_failure_ea_exception(mocker, connector, mock_win32com, mock_ea_app):
    """Test connection failure due to an exception from EA."""
    mocker.patch.dict(os.environ, {"EA_FILE_PATH": "dummy_path"})
    mock_ea_app.Repository.OpenFile.side_effect = Exception("Connection failed")
    with pytest.raises(EAConnectorError, match="Failed to connect to EA repository"):
        connector.connect("dummy_path")
    mock_win32com.assert_called_once_with('EA.App')

def test_create_diagram_success(mocker, connector, mock_win32com, mock_ea_app):
    """Test successful diagram creation."""
    mocker.patch.dict(os.environ, {"EA_FILE_PATH": "dummy_path"})
    connector.connect()

    mock_package = MagicMock()
    mock_diagram = MagicMock()
    mock_diagram.DiagramGUID = "test_guid"
    mock_diagram.Name = "TestDiagram"
    mock_diagram.Type = "Sequence"
    mock_package.Diagrams.AddNew.return_value = mock_diagram
    
    mock_ea_app.Repository.GetPackageByGuid.return_value = mock_package
    
    diagram = connector.create_diagram("pkg_guid", "TestDiagram", "Sequence")
    
    assert diagram is not None
    assert diagram["name"] == "TestDiagram"
    mock_package.Diagrams.AddNew.assert_called_with("TestDiagram", "Sequence")

def test_add_element_to_diagram_success(mocker, connector, mock_win32com, mock_ea_app):
    """Test successful lifeline creation."""
    mocker.patch.dict(os.environ, {"EA_FILE_PATH": "dummy_path"})
    connector.connect()

    mock_diagram = MagicMock()
    mock_diagram.PackageID = 1
    mock_diagram.DiagramObjects = MagicMock()
    
    mock_element = MagicMock()
    mock_element.ElementGUID = "elem_guid"
    mock_element.Name = "TestLifeline"
    mock_element.Type = "Boundary"
    
    mock_package = MagicMock()
    mock_package.Elements.AddNew.return_value = mock_element
    
    mock_ea_app.Repository.GetDiagramByGuid.return_value = mock_diagram
    mock_ea_app.Repository.GetPackageByID.return_value = mock_package
    
    element = connector.add_element_to_diagram("diag_guid", "TestLifeline", "Boundary", "boundary")
    
    assert element is not None
    assert element["name"] == "TestLifeline"
    mock_package.Elements.AddNew.assert_called_with("TestLifeline", "Boundary")
    assert mock_element.Stereotype == "boundary"

