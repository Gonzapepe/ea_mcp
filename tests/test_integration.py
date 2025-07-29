import pytest
import os
import sys
import pythoncom
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from server import (
    create_class_diagram, create_sequence_diagram, create_use_case_diagram,
    create_activity_diagram, create_actor_lifeline
)
from ea_connector import EAConnector

@pytest.fixture(scope="module")
def connector():
    """Fixture to provide a connected EAConnector instance for integration tests."""
    conn = EAConnector()
    # Correct the path format for Windows
    test_project_path = os.path.abspath("D:/proyectos/Python/ea_mcp/tests/test_project.eapx")
    assert conn.connect(test_project_path), "Failed to connect to the test EA project"
    yield conn
    conn.repository.CloseFile()
    # Setting to None is important for COM object cleanup
    conn.repository = None 
    pythoncom.CoUninitialize()

def test_create_class_diagram_integration(connector):
    """
    Integration test to create a class diagram in a real EA project.
    """
    root_package = connector.repository.Models.GetAt(0)
    assert root_package is not None, "Could not find a root package in the test project"

    test_args = {
        "package_guid": root_package.PackageGUID,
        "name": "MyIntegrationTestClassDiagram",
        "classes": [{"name": "TestClass"}]
    }

    result = create_class_diagram(test_args, connector.repository.ConnectionString)

    assert result["status"] == "success"
    assert "diagram_guid" in result

    created_diagram = connector.repository.GetDiagramByGuid(result["diagram_guid"])
    assert created_diagram is not None
    assert created_diagram.Name == "MyIntegrationTestClassDiagram"

    package = connector.repository.GetPackageByGuid(root_package.PackageGUID)
    for i in range(package.Diagrams.Count):
        if package.Diagrams.GetAt(i).DiagramGUID == result["diagram_guid"]:
            package.Diagrams.Delete(i)
            package.Diagrams.Refresh()
            break

def test_create_sequence_diagram_integration(connector):
    """
    Integration test to create a sequence diagram in a real EA project.
    """
    root_package = connector.repository.Models.GetAt(0)
    assert root_package is not None, "Could not find a root package in the test project"

    test_args = {
        "package_guid": root_package.PackageGUID,
        "name": "MyIntegrationTestSequenceDiagram",
        "elements": [{"name": "TestLifeline", "type": "Object", "stereotype": "actor"}]
    }

    result = create_sequence_diagram(test_args, connector.repository.ConnectionString)

    assert result["status"] == "success"
    assert "diagram_guid" in result

    created_diagram = connector.repository.GetDiagramByGuid(result["diagram_guid"])
    assert created_diagram is not None
    assert created_diagram.Name == "MyIntegrationTestSequenceDiagram"

    package = connector.repository.GetPackageByGuid(root_package.PackageGUID)
    for i in range(package.Diagrams.Count):
        if package.Diagrams.GetAt(i).DiagramGUID == result["diagram_guid"]:
            package.Diagrams.Delete(i)
            package.Diagrams.Refresh()
            break

def test_create_use_case_diagram_integration(connector):
    """
    Integration test to create a use case diagram in a real EA project.
    """
    root_package = connector.repository.Models.GetAt(0)
    assert root_package is not None, "Could not find a root package in the test project"

    test_args = {
        "package_guid": root_package.PackageGUID,
        "name": "MyIntegrationTestUseCaseDiagram",
        "actors": ["TestActor"],
        "use_cases": ["TestUseCase"]
    }

    result = create_use_case_diagram(test_args, connector.repository.ConnectionString)

    assert result["status"] == "success"
    assert "diagram_guid" in result

    created_diagram = connector.repository.GetDiagramByGuid(result["diagram_guid"])
    assert created_diagram is not None
    assert created_diagram.Name == "MyIntegrationTestUseCaseDiagram"

    package = connector.repository.GetPackageByGuid(root_package.PackageGUID)
    for i in range(package.Diagrams.Count):
        if package.Diagrams.GetAt(i).DiagramGUID == result["diagram_guid"]:
            package.Diagrams.Delete(i)
            package.Diagrams.Refresh()
            break

def test_create_activity_diagram_integration(connector):
    """
    Integration test to create an activity diagram in a real EA project.
    """
    root_package = connector.repository.Models.GetAt(0)
    assert root_package is not None, "Could not find a root package in the test project"

    test_args = {
        "package_guid": root_package.PackageGUID,
        "name": "MyIntegrationTestActivityDiagram",
        "activities": ["TestActivity"],
        "decisions": ["TestDecision"]
    }

    result = create_activity_diagram(test_args, connector.repository.ConnectionString)

    assert result["status"] == "success"
    assert "diagram_guid" in result

    created_diagram = connector.repository.GetDiagramByGuid(result["diagram_guid"])
    assert created_diagram is not None
    assert created_diagram.Name == "MyIntegrationTestActivityDiagram"

    package = connector.repository.GetPackageByGuid(root_package.PackageGUID)
    for i in range(package.Diagrams.Count):
        if package.Diagrams.GetAt(i).DiagramGUID == result["diagram_guid"]:
            package.Diagrams.Delete(i)
            package.Diagrams.Refresh()
            break

def test_create_actor_lifeline_integration(connector):
    """
    Integration test to create an actor lifeline in a real EA project.
    """
    root_package = connector.repository.Models.GetAt(0)
    assert root_package is not None, "Could not find a root package in the test project"

    # First, create a sequence diagram to add the lifeline to
    diagram_args = {
        "package_guid": root_package.PackageGUID,
        "name": "LifelineTestDiagram"
    }
    diagram_result = create_sequence_diagram(diagram_args, connector.repository.ConnectionString)
    assert diagram_result["status"] == "success"
    diagram_guid = diagram_result["diagram_guid"]

    lifeline_args = {
        "diagram_guid": diagram_guid,
        "name": "MyIntegrationTestActorLifeline"
    }

    result = create_actor_lifeline(lifeline_args, connector.repository.ConnectionString)

    assert result["status"] == "success"
    assert "element_guid" in result

    # Cleanup
    package = connector.repository.GetPackageByGuid(root_package.PackageGUID)
    for i in range(package.Diagrams.Count):
        if package.Diagrams.GetAt(i).DiagramGUID == diagram_guid:
            package.Diagrams.Delete(i)
            package.Diagrams.Refresh()
            break