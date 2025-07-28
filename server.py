#!/usr/bin/env python3
from datetime import datetime

from mcp.server.fastmcp import FastMCP
from typing import Dict, Any
import logging
from ea_connector import EAConnector
from dotenv import load_dotenv
from lifeline_types import LIFELINE_STEREOTYPES

# Load environment variables from .env file
load_dotenv()

# EA Diagram Types
DIAGRAM_TYPES = {
    "sequence": "Sequence",
    "class": "Class",
    "use_case": "UseCase",
    "activity": "Activity"
}

# EA Element Types
ELEMENT_TYPES = {
    "class": "Class",
    "activity": "Activity",
    "decision": "Decision",
    **LIFELINE_STEREOTYPES
}

# EA Connector Types
CONNECTOR_TYPES = {
    "association": "Association",
    "generalization": "Generalization",
    "dependency": "Dependency",
    "message": "Sequence"
}

# Create MCP server instance
mcp = FastMCP("enterprise-architect")
connector = EAConnector()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define tool schemas
SEQUENCE_DIAGRAM_SCHEMA = {
    "type": "object",
    "properties": {
        "package_guid": {"type": "string", "description": "GUID of parent package"},
        "name": {"type": "string", "description": "Diagram name"},
        "elements": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"type": "string"},
                    "stereotype": {"type": "string"}
                }
            }
        }
    },
    "required": ["package_guid", "name"]
}

CLASS_DIAGRAM_SCHEMA = {
    "type": "object",
    "properties": {
        "package_guid": {"type": "string", "description": "GUID of parent package"},
        "name": {"type": "string", "description": "Diagram name"},
        "classes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "attributes": {"type": "array", "items": {"type": "string"}},
                    "methods": {"type": "array", "items": {"type": "string"}}
                }
            }
        }
    },
    "required": ["package_guid", "name"]
}

USE_CASE_DIAGRAM_SCHEMA = {
    "type": "object",
    "properties": {
        "package_guid": {"type": "string", "description": "GUID of parent package"},
        "name": {"type": "string", "description": "Diagram name"},
        "actors": {"type": "array", "items": {"type": "string"}},
        "use_cases": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["package_guid", "name"]
}

ACTIVITY_DIAGRAM_SCHEMA = {
    "type": "object",
    "properties": {
        "package_guid": {"type": "string", "description": "GUID of parent package"},
        "name": {"type": "string", "description": "Diagram name"},
        "activities": {"type": "array", "items": {"type": "string"}},
        "decisions": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["package_guid", "name"]
}

LIFELINE_SCHEMA = {
    "type": "object",
    "properties": {
        "diagram_guid": {"type": "string", "description": "GUID of the diagram"},
        "name": {"type": "string", "description": "Name of the lifeline element"}
    },
    "required": ["diagram_guid", "name"]
}

# Clean up complete - all old class methods removed
def _create_lifeline(diagram_guid: str, element_name: str, lifeline_type: str) -> Dict[str, Any]:
    """Internal helper to create a lifeline element on a diagram."""
    if not connector.connect():
        return {"status": "error", "message": "Failed to connect to Enterprise Architect"}
        
    try:
        # In EA, lifelines on sequence diagrams are 'Object' elements with a specific stereotype
        element = connector.add_element_to_diagram(
            diagram_guid,
            element_name,
            "Object",
            lifeline_type
        )
        if not element:
            return {"status": "error", "message": f"Failed to create {lifeline_type} lifeline"}
        
        # Auto-layout the diagram to accommodate the new element
        connector.auto_layout_diagram(diagram_guid)

        return {
            "status": "success",
            "element_guid": element["guid"]
        }
    except Exception as e:
        logger.error(f"Error creating {lifeline_type} lifeline: {str(e)}")
        return {"status": "error", "message": str(e)}

# Register tools using decorators
@mcp.tool(
    name="create_sequence_diagram",
    description="Creates a sequence diagram in Enterprise Architect",
    annotations={"input_schema": SEQUENCE_DIAGRAM_SCHEMA}
)
def create_sequence_diagram(args: Dict[str, Any]) -> Dict[str, Any]:
    """Create sequence diagram in EA"""
    if not connector.connect():
        return {"status": "error", "message": "Failed to connect to Enterprise Architect"}
        
    try:
        # Create the diagram
        diagram = connector.create_diagram(
            args["package_guid"],
            args["name"],
            DIAGRAM_TYPES["sequence"]
        )
        if not diagram:
            return {"status": "error", "message": "Failed to create diagram"}
        
        # Add elements to diagram
        elements = []
        for i, element in enumerate(args.get("elements", [])):
            el = connector.add_element_to_diagram(
                diagram["guid"],
                element["name"],
                element.get("type", "Object"),
                element.get("stereotype", "")
            )
            if el:
                elements.append(el["guid"])
        
        # Auto-layout the diagram
        connector.auto_layout_diagram(diagram["guid"])
        
        return {
            "status": "success",
            "diagram_guid": diagram["guid"],
            "elements": elements
        }
    except Exception as e:
        logger.error(f"Error creating sequence diagram: {str(e)}")
        return {"status": "error", "message": str(e)}

@mcp.tool(
    name="create_class_diagram",
    description="Creates a class diagram in Enterprise Architect",
    annotations={"input_schema": CLASS_DIAGRAM_SCHEMA}
)
def create_class_diagram(args: Dict[str, Any]) -> Dict[str, Any]:
    """Create class diagram in EA"""
    if not connector.connect():
        return {"status": "error", "message": "Failed to connect to Enterprise Architect"}
        
    try:
        # Create the diagram
        diagram = connector.create_diagram(
            args["package_guid"],
            args["name"],
            DIAGRAM_TYPES["class"]
        )
        if not diagram:
            return {"status": "error", "message": "Failed to create diagram"}
        
        # Add classes to diagram
        classes = []
        for _, cls in enumerate(args.get("classes", [])):
            el = connector.add_element_to_diagram(
                diagram["guid"],
                cls["name"],
                ELEMENT_TYPES["class"]
            )
            if el:
                classes.append(el["guid"])
        
        # Auto-layout the diagram
        connector.auto_layout_diagram(diagram["guid"])
        
        return {
            "status": "success",
            "diagram_guid": diagram["guid"],
            "classes": classes
        }
    except Exception as e:
        logger.error(f"Error creating class diagram: {str(e)}")
        return {"status": "error", "message": str(e)}

@mcp.tool(
    name="create_use_case_diagram",
    description="Creates a use case diagram in Enterprise Architect",
    annotations={"input_schema": USE_CASE_DIAGRAM_SCHEMA}
)
def create_use_case_diagram(args: Dict[str, Any]) -> Dict[str, Any]:
    """Create use case diagram in EA"""
    if not connector.connect():
        return {"status": "error", "message": "Failed to connect to Enterprise Architect"}
        
    try:
        # Create the diagram
        diagram = connector.create_diagram(
            args["package_guid"],
            args["name"],
            DIAGRAM_TYPES["use_case"]
        )
        if not diagram:
            return {"status": "error", "message": "Failed to create diagram"}
        
        # Add actors and use cases
        actors = []
        use_cases = []
        
        # Position actors on left, use cases on right
        for i, actor in enumerate(args.get("actors", [])):
            el = connector.add_element_to_diagram(
                diagram["guid"],
                actor,
                ELEMENT_TYPES["actor"]
            )
            if el:
                actors.append(el["guid"])
        
        for _, use_case in enumerate(args.get("use_cases", [])):
            el = connector.add_element_to_diagram(
                diagram["guid"],
                use_case,
                ELEMENT_TYPES["use_case"]
            )
            if el:
                use_cases.append(el["guid"])
        
        # Auto-layout the diagram
        connector.auto_layout_diagram(diagram["guid"])
        
        return {
            "status": "success",
            "diagram_guid": diagram["guid"],
            "actors": actors,
            "use_cases": use_cases
        }
    except Exception as e:
        logger.error(f"Error creating use case diagram: {str(e)}")
        return {"status": "error", "message": str(e)}

@mcp.tool(
    name="create_activity_diagram",
    description="Creates an activity diagram in Enterprise Architect",
    annotations={"input_schema": ACTIVITY_DIAGRAM_SCHEMA}
)
def create_activity_diagram(args: Dict[str, Any]) -> Dict[str, Any]:
    """Create activity diagram in EA"""
    if not connector.connect():
        return {"status": "error", "message": "Failed to connect to Enterprise Architect"}
        
    try:
        # Create the diagram
        diagram = connector.create_diagram(
            args["package_guid"],
            args["name"],
            DIAGRAM_TYPES["activity"]
        )
        if not diagram:
            return {"status": "error", "message": "Failed to create diagram"}
        
        # Add activities and decisions
        activities = []
        decisions = []
        
        # Position elements in a flow
        for i, activity in enumerate(args.get("activities", [])):
            el = connector.add_element_to_diagram(
                diagram["guid"],
                activity,
                ELEMENT_TYPES["activity"]
            )
            if el:
                activities.append(el["guid"])
        
        for i, decision in enumerate(args.get("decisions", [])):
            el = connector.add_element_to_diagram(
                diagram["guid"],
                decision,
                ELEMENT_TYPES["decision"]
            )
            if el:
                decisions.append(el["guid"])
        
        # Auto-layout the diagram
        connector.auto_layout_diagram(diagram["guid"])
        
        return {
            "status": "success",
            "diagram_guid": diagram["guid"],
            "activities": activities,
            "decisions": decisions
        }
    except Exception as e:
        logger.error(f"Error creating activity diagram: {str(e)}")
        return {"status": "error", "message": str(e)}

@mcp.tool(
    name="create_actor_lifeline",
    description="Creates an actor lifeline on a sequence diagram.",
    annotations={"input_schema": LIFELINE_SCHEMA}
)
def create_actor_lifeline(args: Dict[str, Any]) -> Dict[str, Any]:
    """Create an actor lifeline in EA"""
    return _create_lifeline(args["diagram_guid"], args["name"], "actor")

@mcp.tool(
    name="create_boundary_lifeline",
    description="Creates a boundary lifeline on a sequence diagram.",
    annotations={"input_schema": LIFELINE_SCHEMA}
)
def create_boundary_lifeline(args: Dict[str, Any]) -> Dict[str, Any]:
    """Create a boundary lifeline in EA"""
    return _create_lifeline(args["diagram_guid"], args["name"], "boundary")

@mcp.tool(
    name="create_control_lifeline",
    description="Creates a control lifeline on a sequence diagram.",
    annotations={"input_schema": LIFELINE_SCHEMA}
)
def create_control_lifeline(args: Dict[str, Any]) -> Dict[str, Any]:
    """Create a control lifeline in EA"""
    return _create_lifeline(args["diagram_guid"], args["name"], "control")

@mcp.tool(
    name="create_entity_lifeline",
    description="Creates an entity lifeline on a sequence diagram.",
    annotations={"input_schema": LIFELINE_SCHEMA}
)
def create_entity_lifeline(args: Dict[str, Any]) -> Dict[str, Any]:
    """Create an entity lifeline in EA"""
    return _create_lifeline(args["diagram_guid"], args["name"], "entity")

@mcp.tool(
    name="create_database_lifeline",
    description="Creates a database lifeline on a sequence diagram.",
    annotations={"input_schema": LIFELINE_SCHEMA}
)
def create_database_lifeline(args: Dict[str, Any]) -> Dict[str, Any]:
    """Create a database lifeline in EA"""
    return _create_lifeline(args["diagram_guid"], args["name"], "database")

@mcp.tool(
    name="create_use_case_lifeline",
    description="Creates a use case lifeline on a sequence diagram.",
    annotations={"input_schema": LIFELINE_SCHEMA}
)
def create_use_case_lifeline(args: Dict[str, Any]) -> Dict[str, Any]:
    """Create a use case lifeline in EA"""
    return _create_lifeline(args["diagram_guid"], args["name"], "use_case")

if __name__ == "__main__":
    print(f"Enterprise Architect MCP server starting at {datetime.now().isoformat()}")
    print(f"Server name: enterprise-architect")
    mcp.run()
