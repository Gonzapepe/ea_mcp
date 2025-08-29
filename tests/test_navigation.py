#!/usr/bin/env python3
import pytest
from unittest.mock import MagicMock, patch
from ea_connector import EAConnector
from exceptions import EAConnectorError

@pytest.fixture
def mock_repository():
    """Fixture for a mocked EA Repository object."""
    return MagicMock()

@pytest.fixture
def ea_connector(mock_repository):
    """Fixture for an EAConnector with a mocked repository."""
    with patch('win32com.client.Dispatch'):
        connector = EAConnector()
        connector.repository = mock_repository
        return connector

def test_get_element_by_guid_success(ea_connector, mock_repository):
    mock_element = MagicMock()
    mock_element.ElementGUID = "{123}"
    mock_element.Name = "TestElement"
    mock_element.Type = "Class"
    mock_element.Stereotype = "Stereo"
    mock_element.Notes = "Notes"
    mock_repository.GetElementByGuid.return_value = mock_element

    element = ea_connector.get_element_by_guid("{123}")
    assert element["name"] == "TestElement"
    assert element["type"] == "Class"

def test_get_element_by_guid_not_found(ea_connector, mock_repository):
    mock_repository.GetElementByGuid.return_value = None
    with pytest.raises(EAConnectorError, match="Element with GUID '\{456\}' not found\."):
        ea_connector.get_element_by_guid("{456}")

def test_find_elements_success(ea_connector, mock_repository):
    mock_element = MagicMock()
    mock_element.ElementGUID = "{123}"
    mock_element.Name = "TestElement"
    mock_element.Type = "Class"
    mock_element.Stereotype = "Stereo"
    
    mock_results = MagicMock()
    mock_results.__iter__.return_value = [mock_element]
    mock_repository.GetElementSet.return_value = mock_results

    elements = ea_connector.find_elements("Test")
    assert len(elements) == 1
    assert elements[0]["name"] == "TestElement"
