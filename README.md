# Enterprise Architect MCP Server

Python MCP server for interacting with Sparx Systems Enterprise Architect via COM interface. Provides tools for creating and managing UML diagrams.

## Features

- Create sequence diagrams with lifelines and messages
- Generate class diagrams with classes, attributes and methods
- Build use case diagrams with actors and use cases
- Construct activity diagrams with activities and decisions

## Installation

1. Install Python 3.8+
2. Clone this repository
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

The server requires Enterprise Architect to be installed on the system. No additional configuration is needed beyond the Python dependencies.

## Usage

1. Start the MCP server (either method works):

   As a module:
   ```bash
   python -m server
   ```

   Or directly:
   ```bash
   python path/to/ea_mcp/server.py
   ```

2. The server will expose these tools:

### create_sequence_diagram
Creates a sequence diagram with specified elements.

Parameters:
- `package_guid`: GUID of parent package
- `name`: Diagram name
- `elements`: Array of elements (name, type, stereotype)

Example:
```json
{
  "package_guid": "1234-5678-90AB-CDEF",
  "name": "User Login Sequence",
  "elements": [
    {"name": "User", "type": "Actor"},
    {"name": "System", "type": "Boundary"}
  ]
}
```

### create_class_diagram
Creates a class diagram with specified classes.

Parameters:
- `package_guid`: GUID of parent package
- `name`: Diagram name
- `classes`: Array of classes (name, attributes, methods)

Example:
```json
{
  "package_guid": "1234-5678-90AB-CDEF",
  "name": "Domain Model",
  "classes": [
    {
      "name": "User",
      "attributes": ["username", "password"],
      "methods": ["login()", "logout()"]
    }
  ]
}
```

### create_use_case_diagram
Creates a use case diagram.

Parameters:
- `package_guid`: GUID of parent package
- `name`: Diagram name
- `actors`: Array of actor names
- `use_cases`: Array of use case names

Example:
```json
{
  "package_guid": "1234-5678-90AB-CDEF",
  "name": "Authentication",
  "actors": ["User", "Admin"],
  "use_cases": ["Login", "Logout", "Reset Password"]
}
```

### create_activity_diagram
Creates an activity diagram.

Parameters:
- `package_guid`: GUID of parent package
- `name`: Diagram name
- `activities`: Array of activity names
- `decisions`: Array of decision names

Example:
```json
{
  "package_guid": "1234-5678-90AB-CDEF",
  "name": "Login Flow",
  "activities": ["Enter Credentials", "Validate", "Grant Access"],
  "decisions": ["Valid Credentials?"]
}
```

## Development

To contribute or modify the server:

1. Set up development environment:
   ```bash
   pip install -e .
   ```

2. Run tests:
   ```bash
   pytest tests/
   ```

3. The server follows the MCP protocol specification. Refer to the [MCP documentation](https://github.com/modelcontextprotocol/python-sdk) for details.
