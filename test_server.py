#!/usr/bin/env python3
import unittest
from unittest.mock import MagicMock, patch
from ea_mcp.server import EAServer, DIAGRAM_TYPES, ELEMENT_TYPES
from ea_mcp.ea_connector import EAConnector

class TestEAServer(unittest.TestCase):
    def setUp(self):
        self.server = EAServer()
        # Mock the EA connector to avoid actual EA calls
        self.server.connector = MagicMock(spec=EAConnector)

    def test_sequence_diagram_creation(self):
        """Test sequence diagram creation"""
        # Setup mock return values
        self.server.connector.create_diagram.return_value = {
            "guid": "test-guid-123",
            "name": "Test Sequence",
            "type": DIAGRAM_TYPES["sequence"]
        }
        
        # Test data
        test_args = {
            "package_guid": "test-pkg-123",
            "name": "Test Sequence",
            "elements": [
                {"name": "User", "type": "Actor"},
                {"name": "System", "type": "Boundary"}
            ]
        }

        # Call the method
        result = self.server.create_sequence_diagram(test_args)

        # Verify results
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["diagram_guid"], "test-guid-123")
        self.server.connector.create_diagram.assert_called_once_with(
            "test-pkg-123", 
            "Test Sequence", 
            DIAGRAM_TYPES["sequence"]
        )

    def test_class_diagram_creation(self):
        """Test class diagram creation"""
        self.server.connector.create_diagram.return_value = {
            "guid": "test-guid-456",
            "name": "Test Classes",
            "type": DIAGRAM_TYPES["class"]
        }

        test_args = {
            "package_guid": "test-pkg-123",
            "name": "Test Classes",
            "classes": [
                {
                    "name": "User",
                    "attributes": ["username", "password"],
                    "methods": ["login()", "logout()"]
                }
            ]
        }

        result = self.server.create_class_diagram(test_args)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["diagram_guid"], "test-guid-456")

    def test_use_case_diagram_creation(self):
        """Test use case diagram creation"""
        self.server.connector.create_diagram.return_value = {
            "guid": "test-guid-789",
            "name": "Test Use Cases",
            "type": DIAGRAM_TYPES["use_case"]
        }

        test_args = {
            "package_guid": "test-pkg-123",
            "name": "Test Use Cases",
            "actors": ["User", "Admin"],
            "use_cases": ["Login", "Logout"]
        }

        result = self.server.create_use_case_diagram(test_args)
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["actors"]), 2)
        self.assertEqual(len(result["use_cases"]), 2)

    def test_activity_diagram_creation(self):
        """Test activity diagram creation"""
        self.server.connector.create_diagram.return_value = {
            "guid": "test-guid-abc",
            "name": "Test Activities",
            "type": DIAGRAM_TYPES["activity"]
        }

        test_args = {
            "package_guid": "test-pkg-123",
            "name": "Test Activities",
            "activities": ["Start", "Process", "End"],
            "decisions": ["Valid?"]
        }

        result = self.server.create_activity_diagram(test_args)
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["activities"]), 3)
        self.assertEqual(len(result["decisions"]), 1)

@patch('ea_mcp.server.EAConnector')
def test_server_integration(mock_connector):
    """Integration test for the MCP server"""
    # Setup mock connector
    mock_connector.return_value.connect.return_value = True
    
    # Create and run server
    server = EAServer()
    server.connector = mock_connector.return_value
    
    # Verify server starts
    try:
        server.run()
    except Exception as e:
        assert False, f"Server failed to run: {str(e)}"

if __name__ == "__main__":
    unittest.main()
