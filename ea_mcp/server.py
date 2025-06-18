#!/usr/bin/env python3
from datetime import datetime

from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, List
import json
import logging
from .ea_connector import EAConnector

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
    "actor": "Actor",
    "use_case": "UseCase",
    "activity": "Activity",
    "decision": "Decision"
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

def create_sequence_diagram(args: Dict[str, Any]) -> Dict[str, Any]:
    """Create sequence diagram in EA"""
    if not connector.connect():
        return {"error": "Failed to connect to Enterprise Architect"}
        
    try:
        # Create the diagram
        diagram = connector.create_diagram(
            args["package_guid"],
            args["name"],
            DIAGRAM_TYPES["sequence"]
        )
        if not diagram:
            return {"error": "Failed to create diagram"}
        
        # Add elements to diagram
        elements = []
        for i, element in enumerate(args.get("elements", [])):
            el = connector.add_element_to_diagram(
                diagram["guid"],
                element["name"],
                element.get("type", "Object"),
                element.get("stereotype", ""),
                x=100 + (i * 200),
                y=100
            )
            if el:
                elements.append(el)
        
        return {
            "status": "success",
            "diagram_guid": diagram["guid"],
            "elements": elements
        }
    except Exception as e:
        logger.error(f"Error creating sequence diagram: {str(e)}")
        return {"error": str(e)}
        
def create_class_diagram(args: Dict[str, Any]) -> Dict[str, Any]:
    """Create class diagram in EA"""
    if not connector.connect():
        return {"error": "Failed to connect to Enterprise Architect"}
        
    try:
        # Create the diagram
        diagram = connector.create_diagram(
            args["package_guid"],
            args["name"],
            DIAGRAM_TYPES["class"]
        )
        if not diagram:
            return {"error": "Failed to create diagram"}
        
        # Add classes to diagram
        classes = []
        for i, cls in enumerate(args.get("classes", [])):
            el = connector.add_element_to_diagram(
                diagram["guid"],
                cls["name"],
                ELEMENT_TYPES["class"],
                x=100 + (i * 300),
                y=100
            )
            if el:
                classes.append(el)
        
        return {
            "status": "success",
            "diagram_guid": diagram["guid"],
            "classes": classes
        }
    except Exception as e:
        logger.error(f"Error creating class diagram: {str(e)}")
        return {"error": str(e)}
        
def create_use_case_diagram(args: Dict[str, Any]) -> Dict[str, Any]:
    """Create use case diagram in EA"""
    if not connector.connect():
        return {"error": "Failed to connect to Enterprise Architect"}
        
    try:
        # Create the diagram
        diagram = connector.create_diagram(
            args["package_guid"],
            args["name"],
            DIAGRAM_TYPES["use_case"]
        )
        if not diagram:
            return {"error": "Failed to create diagram"}
        
        # Add actors and use cases
        actors = []
        use_cases = []
        
        # Position actors on left, use cases on right
        for i, actor in enumerate(args.get("actors", [])):
            el = connector.add_element_to_diagram(
                diagram["guid"],
                actor,
                ELEMENT_TYPES["actor"],
                x=50,
                y=100 + (i * 150)
            )
            if el:
                actors.append(el)
        
        for i, use_case in enumerate(args.get("use_cases", [])):
            el = connector.add_element_to_diagram(
                diagram["guid"],
                use_case,
                ELEMENT_TYPES["use_case"],
                x=300,
                y=100 + (i * 150)
            )
            if el:
                use_cases.append(el)
        
        return {
            "status": "success",
            "diagram_guid": diagram["guid"],
            "actors": actors,
            "use_cases": use_cases
        }
    except Exception as e:
        logger.error(f"Error creating use case diagram: {str(e)}")
        return {"error": str(e)}
        
def create_activity_diagram(args: Dict[str, Any]) -> Dict[str, Any]:
    """Create activity diagram in EA"""
    if not connector.connect():
        return {"error": "Failed to connect to Enterprise Architect"}
        
    try:
        # Create the diagram
        diagram = connector.create_diagram(
            args["package_guid"],
            args["name"],
            DIAGRAM_TYPES["activity"]
        )
        if not diagram:
            return {"error": "Failed to create diagram"}
        
        # Add activities and decisions
        activities = []
        decisions = []
        
        # Position elements in a flow
        for i, activity in enumerate(args.get("activities", [])):
            el = connector.add_element_to_diagram(
                diagram["guid"],
                activity,
                ELEMENT_TYPES["activity"],
                x=100 + (i * 200),
                y=100
            )
            if el:
                activities.append(el)
        
        for i, decision in enumerate(args.get("decisions", [])):
            el = connector.add_element_to_diagram(
                diagram["guid"],
                decision,
                ELEMENT_TYPES["decision"],
                x=100 + (i * 200),
                y=200
            )
            if el:
                decisions.append(el)
        
        return {
            "status": "success",
            "diagram_guid": diagram["guid"],
            "activities": activities,
            "decisions": decisions
        }
    except Exception as e:
        logger.error(f"Error creating activity diagram: {str(e)}")
        return {"error": str(e)}

# Clean up complete - all old class methods removed

# Register tools using decorators
@mcp.tool(
    name="create_sequence_diagram",
    description="Creates a sequence diagram in Enterprise Architect",
    annotations={"input_schema": SEQUENCE_DIAGRAM_SCHEMA}
)
def create_sequence_diagram(args: Dict[str, Any]) -> Dict[str, Any]:
    """Create sequence diagram in EA"""
    if not connector.connect():
        return {"error": "Failed to connect to Enterprise Architect"}
        
    try:
        # Create the diagram
        diagram = connector.create_diagram(
            args["package_guid"],
            args["name"],
            DIAGRAM_TYPES["sequence"]
        )
        if not diagram:
            return {"error": "Failed to create diagram"}
        
        # Add elements to diagram
        elements = []
        for i, element in enumerate(args.get("elements", [])):
            el = connector.add_element_to_diagram(
                diagram["guid"],
                element["name"],
                element.get("type", "Object"),
                element.get("stereotype", ""),
                x=100 + (i * 200),
                y=100
            )
            if el:
                elements.append(el)
        
        return {
            "status": "success",
            "diagram_guid": diagram["guid"],
            "elements": elements
        }
    except Exception as e:
        logger.error(f"Error creating sequence diagram: {str(e)}")
        return {"error": str(e)}

@mcp.tool(
    name="create_class_diagram",
    description="Creates a class diagram in Enterprise Architect",
    annotations={"input_schema": CLASS_DIAGRAM_SCHEMA}
)
def create_class_diagram(args: Dict[str, Any]) -> Dict[str, Any]:
    """Create class diagram in EA"""
    if not connector.connect():
        return {"error": "Failed to connect to Enterprise Architect"}
        
    try:
        # Create the diagram
        diagram = connector.create_diagram(
            args["package_guid"],
            args["name"],
            DIAGRAM_TYPES["class"]
        )
        if not diagram:
            return {"error": "Failed to create diagram"}
        
        # Add classes to diagram
        classes = []
        for i, cls in enumerate(args.get("classes", [])):
            el = connector.add_element_to_diagram(
                diagram["guid"],
                cls["name"],
                ELEMENT_TYPES["class"],
                x=100 + (i * 300),
                y=100
            )
            if el:
                classes.append(el)
        
        return {
            "status": "success",
            "diagram_guid": diagram["guid"],
            "classes": classes
        }
    except Exception as e:
        logger.error(f"Error creating class diagram: {str(e)}")
        return {"error": str(e)}

@mcp.tool(
    name="create_use_case_diagram",
    description="Creates a use case diagram in Enterprise Architect",
    annotations={"input_schema": USE_CASE_DIAGRAM_SCHEMA}
)
def create_use_case_diagram(args: Dict[str, Any]) -> Dict[str, Any]:
    """Create use case diagram in EA"""
    if not connector.connect():
        return {"error": "Failed to connect to Enterprise Architect"}
        
    try:
        # Create the diagram
        diagram = connector.create_diagram(
            args["package_guid"],
            args["name"],
            DIAGRAM_TYPES["use_case"]
        )
        if not diagram:
            return {"error": "Failed to create diagram"}
        
        # Add actors and use cases
        actors = []
        use_cases = []
        
        # Position actors on left, use cases on right
        for i, actor in enumerate(args.get("actors", [])):
            el = connector.add_element_to_diagram(
                diagram["guid"],
                actor,
                ELEMENT_TYPES["actor"],
                x=50,
                y=100 + (i * 150)
            )
            if el:
                actors.append(el)
        
        for i, use_case in enumerate(args.get("use_cases", [])):
            el = connector.add_element_to_diagram(
                diagram["guid"],
                use_case,
                ELEMENT_TYPES["use_case"],
                x=300,
                y=100 + (i * 150)
            )
            if el:
                use_cases.append(el)
        
        return {
            "status": "success",
            "diagram_guid": diagram["guid"],
            "actors": actors,
            "use_cases": use_cases
        }
    except Exception as e:
        logger.error(f"Error creating use case diagram: {str(e)}")
        return {"error": str(e)}

@mcp.tool(
    name="create_activity_diagram",
    description="Creates an activity diagram in Enterprise Architect",
    annotations={"input_schema": ACTIVITY_DIAGRAM_SCHEMA}
)
def create_activity_diagram(args: Dict[str, Any]) -> Dict[str, Any]:
    """Create activity diagram in EA"""
    if not connector.connect():
        return {"error": "Failed to connect to Enterprise Architect"}
        
    try:
        # Create the diagram
        diagram = connector.create_diagram(
            args["package_guid"],
            args["name"],
            DIAGRAM_TYPES["activity"]
        )
        if not diagram:
            return {"error": "Failed to create diagram"}
        
        # Add activities and decisions
        activities = []
        decisions = []
        
        # Position elements in a flow
        for i, activity in enumerate(args.get("activities", [])):
            el = connector.add_element_to_diagram(
                diagram["guid"],
                activity,
                ELEMENT_TYPES["activity"],
                x=100 + (i * 200),
                y=100
            )
            if el:
                activities.append(el)
        
        for i, decision in enumerate(args.get("decisions", [])):
            el = connector.add_element_to_diagram(
                diagram["guid"],
                decision,
                ELEMENT_TYPES["decision"],
                x=100 + (i * 200),
                y=200
            )
            if el:
                decisions.append(el)
        
        return {
            "status": "success",
            "diagram_guid": diagram["guid"],
            "activities": activities,
            "decisions": decisions
        }
    except Exception as e:
        logger.error(f"Error creating activity diagram: {str(e)}")
        return {"error": str(e)}

if __name__ == "__main__":
    print(f"Enterprise Architect MCP server starting at {datetime.now().isoformat()}")
    print(f"Server name: enterprise-architect")
    mcp.run()
