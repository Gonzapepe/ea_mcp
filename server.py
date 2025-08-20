#!/usr/bin/env python3
from datetime import datetime
from mcp.server.fastmcp import FastMCP
from typing import Dict, Any
import logging
import functools
from ea_connector import EAConnector
from exceptions import EAConnectorError
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

# --- Helper Functions ---
def _handle_error(e: Exception, tool_name: str) -> Dict[str, Any]:
    """Unified error handling for tools."""
    if isinstance(e, EAConnectorError):
        logger.error(f"Error in {tool_name}: {e.args[0]} - Details: {e.details}")
        return {"status": "error", "message": e.args[0], "details": e.details}
    
    logger.error(f"An unexpected error occurred in {tool_name}: {str(e)}", exc_info=True)
    return {"status": "error", "message": "An unexpected error occurred.", "details": str(e)}

def _validate_args(args: Dict[str, Any], required_fields: list) -> None:
    """Validate presence of required fields in arguments."""
    for field in required_fields:
        if field not in args or not args[field]:
            raise ValueError(f"Missing required argument: '{field}'")

def tool_handler(func):
    """Decorator to handle tool execution logging and error handling."""
    @functools.wraps(func)
    def wrapper(args: Dict[str, Any], ea_file_path: str = None) -> Dict[str, Any]:
        tool_name = func.__name__
        logger.info(f"Executing tool: {tool_name} with args: {args}")
        try:
            result = func(args, ea_file_path)
            logger.info(f"Tool {tool_name} executed successfully.")
            return result
        except (EAConnectorError, ValueError) as e:
            return _handle_error(e, tool_name)
        except Exception as e:
            return _handle_error(e, tool_name)
    return wrapper

# --- Tool Implementations ---
@mcp.tool(
    name="create_sequence_diagram",
    description="Creates a sequence diagram in Enterprise Architect.",
)
@tool_handler
def create_sequence_diagram(args: Dict[str, Any], ea_file_path: str = None) -> Dict[str, Any]:
    """Create sequence diagram in EA"""
    _validate_args(args, ["package_guid", "name"])
    connector.connect(ea_file_path)
    
    diagram = connector.create_diagram(
        args["package_guid"],
        args["name"],
        DIAGRAM_TYPES["sequence"]
    )
    
    elements = []
    for element in args.get("elements", []):
        _validate_args(element, ["name", "type"])
        el = connector.add_element_to_diagram(
            diagram["guid"],
            element["name"],
            element.get("type", "Object"),
            element.get("stereotype", "")
        )
        elements.append(el["guid"])
    
    connector.auto_layout_diagram(diagram["guid"])
    
    return {
        "status": "success",
        "data": {
            "diagram_guid": diagram["guid"],
            "elements": elements
        }
    }

@mcp.tool(
    name="create_class_diagram",
    description="Creates a class diagram in Enterprise Architect.",
)
@tool_handler
def create_class_diagram(args: Dict[str, Any], ea_file_path: str = None) -> Dict[str, Any]:
    """Create class diagram in EA"""
    _validate_args(args, ["package_guid", "name"])
    connector.connect(ea_file_path)
    
    diagram = connector.create_diagram(
        args["package_guid"],
        args["name"],
        DIAGRAM_TYPES["class"]
    )
    
    classes = []
    for cls in args.get("classes", []):
        _validate_args(cls, ["name"])
        el = connector.add_element_to_diagram(
            diagram["guid"],
            cls["name"],
            ELEMENT_TYPES["class"]
        )
        classes.append(el["guid"])
    
    connector.auto_layout_diagram(diagram["guid"])
    
    return {
        "status": "success",
        "data": {
            "diagram_guid": diagram["guid"],
            "classes": classes
        }
    }

@mcp.tool(
    name="create_use_case_diagram",
    description="Creates a use case diagram in Enterprise Architect.",
)
@tool_handler
def create_use_case_diagram(args: Dict[str, Any], ea_file_path: str = None) -> Dict[str, Any]:
    """Create use case diagram in EA"""
    _validate_args(args, ["package_guid", "name"])
    connector.connect(ea_file_path)
    
    diagram = connector.create_diagram(
        args["package_guid"],
        args["name"],
        DIAGRAM_TYPES["use_case"]
    )
    
    actors = []
    for actor_name in args.get("actors", []):
        el = connector.add_element_to_diagram(diagram["guid"], actor_name, "Actor")
        actors.append(el["guid"])
        
    use_cases = []
    for uc_name in args.get("use_cases", []):
        el = connector.add_element_to_diagram(diagram["guid"], uc_name, "UseCase")
        use_cases.append(el["guid"])
    
    connector.auto_layout_diagram(diagram["guid"])
    
    return {
        "status": "success",
        "data": {
            "diagram_guid": diagram["guid"],
            "actors": actors,
            "use_cases": use_cases
        }
    }

@mcp.tool(
    name="create_activity_diagram",
    description="Creates an activity diagram in Enterprise Architect.",
)
@tool_handler
def create_activity_diagram(args: Dict[str, Any], ea_file_path: str = None) -> Dict[str, Any]:
    """Create activity diagram in EA"""
    _validate_args(args, ["package_guid", "name"])
    connector.connect(ea_file_path)
    
    diagram = connector.create_diagram(
        args["package_guid"],
        args["name"],
        DIAGRAM_TYPES["activity"]
    )
    
    activities = []
    for activity_name in args.get("activities", []):
        el = connector.add_element_to_diagram(diagram["guid"], activity_name, "Activity")
        activities.append(el["guid"])
        
    decisions = []
    for decision_name in args.get("decisions", []):
        el = connector.add_element_to_diagram(diagram["guid"], decision_name, "Decision")
        decisions.append(el["guid"])
        
    connector.auto_layout_diagram(diagram["guid"])
    
    return {
        "status": "success",
        "data": {
            "diagram_guid": diagram["guid"],
            "activities": activities,
            "decisions": decisions
        }
    }

def _create_lifeline(diagram_guid: str, element_name: str, lifeline_type: str) -> Dict[str, Any]:
    """Internal helper to create a lifeline element on a diagram."""
    tool_name = f"create_{lifeline_type}_lifeline"
    try:
        element = connector.add_element_to_diagram(
            diagram_guid,
            element_name,
            "Object",
            lifeline_type
        )
        connector.auto_layout_diagram(diagram_guid)
        return {
            "status": "success",
            "data": {"element_guid": element["guid"]}
        }
    except EAConnectorError as e:
        return _handle_error(e, tool_name)
    except Exception as e:
        return _handle_error(e, tool_name)

# --- Lifeline Tools ---
@mcp.tool(
    name="create_actor_lifeline",
    description="Creates an actor lifeline on a sequence diagram.",
)
@tool_handler
def create_actor_lifeline(args: Dict[str, Any], ea_file_path: str = None) -> Dict[str, Any]:
    _validate_args(args, ["diagram_guid", "name"])
    connector.connect(ea_file_path)
    return _create_lifeline(args["diagram_guid"], args["name"], "actor")

@mcp.tool(
    name="create_boundary_lifeline",
    description="Creates a boundary lifeline on a sequence diagram.",
)
@tool_handler
def create_boundary_lifeline(args: Dict[str, Any], ea_file_path: str = None) -> Dict[str, Any]:
    _validate_args(args, ["diagram_guid", "name"])
    connector.connect(ea_file_path)
    return _create_lifeline(args["diagram_guid"], args["name"], "boundary")

@mcp.tool(
    name="create_control_lifeline",
    description="Creates a control lifeline on a sequence diagram.",
)
@tool_handler
def create_control_lifeline(args: Dict[str, Any], ea_file_path: str = None) -> Dict[str, Any]:
    _validate_args(args, ["diagram_guid", "name"])
    connector.connect(ea_file_path)
    return _create_lifeline(args["diagram_guid"], args["name"], "control")

@mcp.tool(
    name="create_entity_lifeline",
    description="Creates an entity lifeline on a sequence diagram.",
)
@tool_handler
def create_entity_lifeline(args: Dict[str, Any], ea_file_path: str = None) -> Dict[str, Any]:
    _validate_args(args, ["diagram_guid", "name"])
    connector.connect(ea_file_path)
    return _create_lifeline(args["diagram_guid"], args["name"], "entity")

@mcp.tool(
    name="create_database_lifeline",
    description="Creates a database lifeline on a sequence diagram.",
)
@tool_handler
def create_database_lifeline(args: Dict[str, Any], ea_file_path: str = None) -> Dict[str, Any]:
    _validate_args(args, ["diagram_guid", "name"])
    connector.connect(ea_file_path)
    return _create_lifeline(args["diagram_guid"], args["name"], "database")

@mcp.tool(
    name="create_use_case_lifeline",
    description="Creates a use case lifeline on a sequence diagram.",
)
@tool_handler
def create_use_case_lifeline(args: Dict[str, Any], ea_file_path: str = None) -> Dict[str, Any]:
    _validate_args(args, ["diagram_guid", "name"])
    connector.connect(ea_file_path)
    return _create_lifeline(args["diagram_guid"], args["name"], "use_case")


if __name__ == "__main__":
    logger.info(f"Enterprise Architect MCP server starting at {datetime.now().isoformat()}")
    logger.info(f"Server name: enterprise-architect")
    print(f"Enterprise Architect MCP server starting at {datetime.now().isoformat()}")
    print(f"Server name: enterprise-architect")
    mcp.run()
