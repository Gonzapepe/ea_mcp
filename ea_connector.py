#!/usr/bin/env python3
import win32com.client
import pythoncom
from typing import Optional, Dict, Any
import logging
import sys
import os
import shutil
import time
from exceptions import EAConnectorError

class EAConnector:
    """Handles connection and operations with Enterprise Architect"""
    
    def __init__(self):
        self.ea_app = None
        self.repository = None
        self.logger = logging.getLogger(__name__)

    def connect_ea(self):
        self.logger.info("Attempting to connect to Enterprise Architect COM interface.")
        try:
            self.ea_app = win32com.client.Dispatch("EA.App")
            self.logger.info("Connected to EA successfully.")
            return True
        except AttributeError:
            self.logger.warning("Failed to connect to EA. Attempting to fix gen_py cache...")
            # Clean up cache and retry
            temp_dir = os.path.join(os.environ['LOCALAPPDATA'], 'Temp')
            gen_py_path = os.path.join(temp_dir, 'gen_py')
            
            if os.path.exists(gen_py_path):
                self.logger.info(f"Removing gen_py cache at: {gen_py_path}")
                shutil.rmtree(gen_py_path)
            
            # Remove corrupted modules from sys.modules
            for mod in list(sys.modules):
                if mod.startswith('win32com.gen_py'):
                    self.logger.info(f"Removing corrupted module from sys.modules: {mod}")
                    del sys.modules[mod]
            
            try:
                self.ea_app = win32com.client.Dispatch("EA.App")
                self.logger.info("Connected to EA successfully after cache cleanup.")
                return True
            except Exception as e:
                raise EAConnectorError("Failed to connect to EA after cache cleanup.", details=str(e))
        
    def connect(self, ea_file_path: Optional[str] = None):
        """Connect to Enterprise Architect via COM"""
        self.logger.info("Connecting to EA repository.")
        try:
            if not self.ea_app:
                self.connect_ea()
            
            self.repository = self.ea_app.Repository
            
            if not ea_file_path:
                from dotenv import load_dotenv
                load_dotenv()
                ea_file_path = os.getenv("EA_FILE_PATH")
                if not ea_file_path:
                    raise EAConnectorError("EA_FILE_PATH environment variable not set and no path provided.")

            self.logger.info(f"Opening EA file: {ea_file_path}")
            self.repository.OpenFile(ea_file_path)
            time.sleep(1)
            # Re-fetch repository reference — OpenFile can invalidate the previous object
            self.repository = self.ea_app.Repository
            self.logger.info(f"Successfully opened EA file: {ea_file_path}")
        except EAConnectorError:
            # Re-raise EAConnectorError as-is to preserve specific error messages
            raise
        except Exception as e:
            raise EAConnectorError("Failed to connect to EA repository.", details=str(e))
            
    def create_diagram(self, package_guid: str, name: str, diagram_type: str) -> Dict[str, Any]:
        """Create a new diagram in EA"""
        self.logger.info(f"Creating diagram '{name}' of type '{diagram_type}' in package '{package_guid}'.")
        try:
            package = self.repository.GetPackageByGuid(package_guid)
            if not package:
                raise EAConnectorError(f"Package with GUID '{package_guid}' not found.")
            
            diagrams = package.Diagrams
            diagram = diagrams.AddNew(name, diagram_type)
            diagram.Update()
            diagrams.Refresh()
            self.logger.info(f"Successfully created diagram with GUID: {diagram.DiagramGUID}")
            return {
                "guid": diagram.DiagramGUID,
                "name": diagram.Name,
                "type": diagram.Type
            }
        except Exception as e:
            raise EAConnectorError("Failed to create diagram.", details=str(e))
            
    def add_element_to_diagram(self, diagram_guid: str, element_name: str, element_type: str, 
                             stereotype: str = "") -> Dict[str, Any]:
        """Add an element to an existing diagram"""
        self.logger.info(f"Adding element '{element_name}' of type '{element_type}' to diagram '{diagram_guid}'.")
        diagram = self.repository.GetDiagramByGuid(diagram_guid)
        if not diagram:
            raise EAConnectorError(f"Diagram with GUID '{diagram_guid}' not found.")
        
        try:
            package = self.repository.GetPackageByID(diagram.PackageID)
            elements = package.Elements
            element = elements.AddNew(element_name, element_type)
            if stereotype:
                element.Stereotype = stereotype
            element.Update()
            elements.Refresh()

            diagram_object = diagram.DiagramObjects.AddNew("", "")
            diagram_object.ElementID = element.ElementID
            diagram_object.Update()
            diagram.DiagramObjects.Refresh()

            self.logger.info(f"Successfully added element with GUID: {element.ElementGUID}")
            return {
                "guid": element.ElementGUID,
                "name": element.Name,
                "type": element.Type
            }
        except Exception as e:
            raise EAConnectorError("Failed to add element to diagram.", details=str(e))

    def auto_layout_diagram(self, diagram_guid: str, layout_style: int = 0):
        """Automatically layout a diagram"""
        self.logger.info(f"Auto-laying out diagram '{diagram_guid}' with style '{layout_style}'.")
        diagram = self.repository.GetDiagramByGuid(diagram_guid)
        if not diagram:
            raise EAConnectorError(f"Diagram with GUID '{diagram_guid}' not found.")
        
        try:
            project = self.repository.GetProjectInterface()
            project.LayoutDiagram(diagram.DiagramGUID, layout_style)
            self.repository.ReloadDiagram(diagram.DiagramID)
            self.logger.info(f"Successfully auto-laid out diagram '{diagram_guid}'.")
        except Exception as e:
            raise EAConnectorError("Failed to auto-layout diagram.", details=str(e))

    def get_package(self, package_guid: str) -> Dict[str, Any]:
        """Retrieve a package by its GUID"""
        self.logger.info(f"Retrieving package with GUID: {package_guid}")
        package = self.repository.GetPackageByGuid(package_guid)
        if not package:
            raise EAConnectorError(f"Package with GUID '{package_guid}' not found.")
        
        try:
            result = {
                "guid": package.PackageGUID,
                "name": package.Name,
                "notes": package.Notes
            }
            self.logger.info(f"Successfully retrieved package: {result['name']}")
            return result
        except Exception as e:
            raise EAConnectorError("Failed to retrieve package details.", details=str(e))

    def get_element_by_guid(self, element_guid: str) -> Dict[str, Any]:
        """Retrieve an element by its GUID"""
        self.logger.info(f"Retrieving element with GUID: {element_guid}")
        element = self.repository.GetElementByGuid(element_guid)
        if not element:
            raise EAConnectorError(f"Element with GUID '{element_guid}' not found.")
        
        try:
            result = {
                "guid": element.ElementGUID,
                "name": element.Name,
                "type": element.Type,
                "stereotype": element.Stereotype,
                "notes": element.Notes
            }
            self.logger.info(f"Successfully retrieved element: {result['name']}")
            return result
        except Exception as e:
            raise EAConnectorError("Failed to retrieve element details.", details=str(e))

    def get_diagram_by_guid(self, diagram_guid: str) -> Dict[str, Any]:
        """Retrieve a diagram by its GUID"""
        self.logger.info(f"Retrieving diagram with GUID: {diagram_guid}")
        diagram = self.repository.GetDiagramByGuid(diagram_guid)
        if not diagram:
            raise EAConnectorError(f"Diagram with GUID '{diagram_guid}' not found.")
        
        try:
            result = {
                "guid": diagram.DiagramGUID,
                "name": diagram.Name,
                "type": diagram.Type,
                "notes": diagram.Notes
            }
            self.logger.info(f"Successfully retrieved diagram: {result['name']}")
            return result
        except Exception as e:
            raise EAConnectorError("Failed to retrieve diagram details.", details=str(e))

    def get_package_elements(self, package_guid: str, element_type: Optional[str] = None) -> list:
        """Retrieve elements from a package, optionally filtered by type"""
        self.logger.info(f"Retrieving elements from package '{package_guid}'.")
        package = self.repository.GetPackageByGuid(package_guid)
        if not package:
            raise EAConnectorError(f"Package with GUID '{package_guid}' not found.")
        
        try:
            elements = []
            for element in package.Elements:
                if not element_type or element.Type == element_type:
                    elements.append({
                        "guid": element.ElementGUID,
                        "name": element.Name,
                        "type": element.Type,
                        "stereotype": element.Stereotype
                    })
            self.logger.info(f"Found {len(elements)} elements in package '{package_guid}'.")
            return elements
        except Exception as e:
            raise EAConnectorError("Failed to retrieve package elements.", details=str(e))

    def get_sub_packages(self, package_guid: Optional[str] = None) -> list:
        """Retrieve sub-packages from a package, or root packages if no GUID is provided."""
        self.logger.info(f"Retrieving sub-packages for package GUID: {package_guid or 'root'}")
        try:
            package_collection = None
            if package_guid:
                package = self.repository.GetPackageByGuid(package_guid)
                if not package:
                    raise EAConnectorError(f"Package with GUID '{package_guid}' not found.")
                package_collection = package.Packages
            else:
                package_collection = self.repository.Models
            
            packages = []
            for pkg in package_collection:
                packages.append({
                    "guid": pkg.PackageGUID,
                    "name": pkg.Name
                })
            
            self.logger.info(f"Found {len(packages)} sub-packages.")
            return packages
        except Exception as e:
            raise EAConnectorError("Failed to retrieve sub-packages.", details=str(e))

    def get_element_connectors(self, element_guid: str) -> list:
        """Retrieve connectors for a given element"""
        self.logger.info(f"Retrieving connectors for element '{element_guid}'.")
        element = self.repository.GetElementByGuid(element_guid)
        if not element:
            raise EAConnectorError(f"Element with GUID '{element_guid}' not found.")

        try:
            connectors = []
            for connector in element.Connectors:
                client  = self.repository.GetElementByID(connector.ClientID)
                supplier = self.repository.GetElementByID(connector.SupplierID)
                connectors.append({
                    "guid": connector.ConnectorGUID,
                    "name": connector.Name,
                    "type": connector.Type,
                    "client_guid":   client.ElementGUID   if client   else None,
                    "client_name":   client.Name          if client   else None,
                    "supplier_guid": supplier.ElementGUID if supplier else None,
                    "supplier_name": supplier.Name        if supplier else None,
                })
            self.logger.info(f"Found {len(connectors)} connectors for element '{element_guid}'.")
            return connectors
        except Exception as e:
            raise EAConnectorError("Failed to retrieve element connectors.", details=str(e))

    def find_elements(self, search_term: str, element_type: Optional[str] = None) -> list:
        """Find elements by search term, optionally filtered by type"""
        self.logger.info(f"Searching for elements with term '{search_term}'.")
        try:
            search_results = self.repository.GetElementSet(f"SELECT * FROM t_object WHERE Name LIKE '%{search_term}%'", 2)
            elements = []
            for element in search_results:
                if not element_type or element.Type == element_type:
                    elements.append({
                        "guid": element.ElementGUID,
                        "name": element.Name,
                        "type": element.Type,
                        "stereotype": element.Stereotype
                    })
            self.logger.info(f"Found {len(elements)} elements matching '{search_term}'.")
            return elements
        except Exception as e:
            raise EAConnectorError("Failed to find elements.", details=str(e))

    def list_diagrams(self, package_guid: str) -> list:
        """List all diagrams in a package"""
        self.logger.info(f"Listing diagrams in package '{package_guid}'.")
        package = self.repository.GetPackageByGuid(package_guid)
        if not package:
            raise EAConnectorError(f"Package with GUID '{package_guid}' not found.")
        try:
            diagrams = []
            for d in package.Diagrams:
                diagrams.append({
                    "guid": d.DiagramGUID,
                    "name": d.Name,
                    "type": d.Type
                })
            return diagrams
        except Exception as e:
            raise EAConnectorError("Failed to list diagrams.", details=str(e))

    def get_diagram_elements(self, diagram_guid: str) -> list:
        """List all elements shown in a diagram"""
        self.logger.info(f"Getting elements for diagram '{diagram_guid}'.")
        diagram = self.repository.GetDiagramByGuid(diagram_guid)
        if not diagram:
            raise EAConnectorError(f"Diagram with GUID '{diagram_guid}' not found.")
        try:
            elements = []
            for obj in diagram.DiagramObjects:
                element = self.repository.GetElementByID(obj.ElementID)
                if element:
                    elements.append({
                        "guid": element.ElementGUID,
                        "name": element.Name,
                        "type": element.Type,
                        "stereotype": element.Stereotype
                    })
            return elements
        except Exception as e:
            raise EAConnectorError("Failed to get diagram elements.", details=str(e))

    def get_class_details(self, element_guid: str) -> Dict[str, Any]:
        """Get a class element with its attributes and methods"""
        self.logger.info(f"Getting class details for element '{element_guid}'.")
        element = self.repository.GetElementByGuid(element_guid)
        if not element:
            raise EAConnectorError(f"Element with GUID '{element_guid}' not found.")
        try:
            attributes = []
            for attr in element.Attributes:
                attributes.append({
                    "name": attr.Name,
                    "type": attr.Type,
                    "visibility": attr.Visibility,
                    "is_static": bool(attr.IsStatic),
                    "default": attr.Default
                })
            methods = []
            for method in element.Methods:
                params = []
                for p in method.Parameters:
                    params.append({"name": p.Name, "type": p.Type})
                methods.append({
                    "name": method.Name,
                    "return_type": method.ReturnType,
                    "visibility": method.Visibility,
                    "is_static": bool(method.IsStatic),
                    "parameters": params
                })
            return {
                "guid": element.ElementGUID,
                "name": element.Name,
                "type": element.Type,
                "stereotype": element.Stereotype,
                "notes": element.Notes,
                "attributes": attributes,
                "methods": methods
            }
        except Exception as e:
            raise EAConnectorError("Failed to get class details.", details=str(e))

    def add_element_to_package(self, package_guid: str, name: str, element_type: str,
                               stereotype: str = "") -> Dict[str, Any]:
        """Create an element in a package (without adding it to any diagram)"""
        self.logger.info(f"Adding element '{name}' to package '{package_guid}'.")
        package = self.repository.GetPackageByGuid(package_guid)
        if not package:
            raise EAConnectorError(f"Package with GUID '{package_guid}' not found.")
        try:
            element = package.Elements.AddNew(name, element_type)
            if stereotype:
                element.Stereotype = stereotype
            element.Update()
            package.Elements.Refresh()
            return {
                "guid": element.ElementGUID,
                "name": element.Name,
                "type": element.Type
            }
        except Exception as e:
            raise EAConnectorError("Failed to add element to package.", details=str(e))

    def create_lifeline(self, diagram_guid: str, name: str,
                        class_guid: Optional[str] = None,
                        lifeline_type: str = "Object",
                        stereotype: str = "") -> Dict[str, Any]:
        """Create a lifeline in a sequence diagram.

        If class_guid is provided the lifeline is linked to that class and EA
        displays it as 'name:ClassName'. Omitting name (pass "") lets EA use
        just ':ClassName'.

        lifeline_type values:
          Object   — regular class instance (default)
          Actor    — actor (stick figure)
          Sequence — generic lifeline; combine with stereotype for boundary/
                     control/entity/database shapes
        """
        self.logger.info(f"Creating lifeline '{name}' in diagram '{diagram_guid}'.")
        diagram = self.repository.GetDiagramByGuid(diagram_guid)
        if not diagram:
            raise EAConnectorError(f"Diagram '{diagram_guid}' not found.")
        try:
            package = self.repository.GetPackageByID(diagram.PackageID)
            el = package.Elements.AddNew(name, lifeline_type)
            if stereotype:
                el.Stereotype = stereotype
            if class_guid:
                cls = self.repository.GetElementByGuid(class_guid)
                if not cls:
                    raise EAConnectorError(f"Class '{class_guid}' not found.")
                el.ClassifierID = cls.ElementID
            el.Update()
            package.Elements.Refresh()

            obj = diagram.DiagramObjects.AddNew("", "")
            obj.ElementID = el.ElementID
            obj.Update()
            diagram.DiagramObjects.Refresh()

            classifier_name = ""
            if class_guid:
                cls = self.repository.GetElementByGuid(class_guid)
                classifier_name = cls.Name if cls else ""

            return {
                "guid": el.ElementGUID,
                "name": el.Name,
                "type": el.Type,
                "classifier": classifier_name,
                "display": f"{el.Name}:{classifier_name}" if classifier_name else el.Name,
            }
        except EAConnectorError:
            raise
        except Exception as e:
            raise EAConnectorError("Failed to create lifeline.", details=str(e))

    def create_erd_entity(self, package_guid: str, name: str) -> Dict[str, Any]:
        """Create an ERD entity (table rectangle) in a package."""
        self.logger.info(f"Creating ERD entity '{name}' in package '{package_guid}'.")
        package = self.repository.GetPackageByGuid(package_guid)
        if not package:
            raise EAConnectorError(f"Package '{package_guid}' not found.")
        try:
            el = package.Elements.AddNew(name, "Class")
            el.Stereotype = "ERD_Entity"
            el.Update()
            package.Elements.Refresh()
            return {"guid": el.ElementGUID, "name": el.Name}
        except Exception as e:
            raise EAConnectorError("Failed to create ERD entity.", details=str(e))

    def create_erd_attribute(self, package_guid: str, entity_guid: str,
                             name: str, is_pk: bool = False) -> Dict[str, Any]:
        """Create an ERD attribute (oval) in a package and connect it to an entity.

        PKs get attributeType=primaryKey (shown underlined in the diagram).
        Regular attributes get attributeType=normal.
        The connector between entity and attribute gets stereotype ERD_Connector.
        """
        self.logger.info(f"Creating ERD attribute '{name}' for entity '{entity_guid}'.")
        package = self.repository.GetPackageByGuid(package_guid)
        entity  = self.repository.GetElementByGuid(entity_guid)
        if not package:
            raise EAConnectorError(f"Package '{package_guid}' not found.")
        if not entity:
            raise EAConnectorError(f"Entity '{entity_guid}' not found.")
        try:
            # Create the attribute oval
            attr_el = package.Elements.AddNew(name, "Class")
            attr_el.Stereotype = "ERD_Attribute"
            attr_el.Update()
            package.Elements.Refresh()

            # Set attributeType tagged value (controls underline display for PKs)
            tv = attr_el.TaggedValues.AddNew("attributeType", "primaryKey" if is_pk else "normal")
            tv.Update()
            attr_el.TaggedValues.Refresh()

            # Connect entity -> attribute with ERD_Connector stereotype
            conn = entity.Connectors.AddNew("", "Association")
            conn.SupplierID = attr_el.ElementID
            conn.Stereotype = "ERD_Connector"
            conn.Update()
            entity.Connectors.Refresh()

            return {
                "guid": attr_el.ElementGUID,
                "name": attr_el.Name,
                "is_pk": is_pk,
            }
        except Exception as e:
            raise EAConnectorError("Failed to create ERD attribute.", details=str(e))

    def create_package(self, parent_guid: str, name: str) -> Dict[str, Any]:
        """Create a sub-package inside a parent package"""
        self.logger.info(f"Creating package '{name}' inside '{parent_guid}'.")
        parent = self.repository.GetPackageByGuid(parent_guid)
        if not parent:
            raise EAConnectorError(f"Parent package with GUID '{parent_guid}' not found.")
        try:
            pkg = parent.Packages.AddNew(name, "")
            pkg.Update()
            parent.Packages.Refresh()
            return {"guid": pkg.PackageGUID, "name": pkg.Name}
        except Exception as e:
            raise EAConnectorError("Failed to create package.", details=str(e))

    def update_element(self, element_guid: str, name: Optional[str] = None,
                       notes: Optional[str] = None, stereotype: Optional[str] = None) -> Dict[str, Any]:
        """Update properties of an existing element"""
        self.logger.info(f"Updating element '{element_guid}'.")
        element = self.repository.GetElementByGuid(element_guid)
        if not element:
            raise EAConnectorError(f"Element with GUID '{element_guid}' not found.")
        try:
            if name is not None:
                element.Name = name
            if notes is not None:
                element.Notes = notes
            if stereotype is not None:
                element.Stereotype = stereotype
            element.Update()
            return {
                "guid": element.ElementGUID,
                "name": element.Name,
                "type": element.Type,
                "stereotype": element.Stereotype
            }
        except Exception as e:
            raise EAConnectorError("Failed to update element.", details=str(e))

    def add_attribute(self, element_guid: str, name: str, attr_type: str = "String",
                      visibility: str = "Private", is_static: bool = False) -> Dict[str, Any]:
        """Add an attribute to a class element"""
        self.logger.info(f"Adding attribute '{name}' to element '{element_guid}'.")
        element = self.repository.GetElementByGuid(element_guid)
        if not element:
            raise EAConnectorError(f"Element with GUID '{element_guid}' not found.")
        try:
            attr = element.Attributes.AddNew(name, attr_type)
            attr.Visibility = visibility
            attr.IsStatic = is_static
            attr.Update()
            element.Attributes.Refresh()
            return {
                "name": attr.Name,
                "type": attr.Type,
                "visibility": attr.Visibility,
                "is_static": bool(attr.IsStatic)
            }
        except Exception as e:
            raise EAConnectorError("Failed to add attribute.", details=str(e))

    def add_operation(self, element_guid: str, name: str, return_type: str = "void",
                      visibility: str = "Public", is_static: bool = False,
                      parameters: list = None) -> Dict[str, Any]:
        """Add a method/operation to a class element"""
        self.logger.info(f"Adding operation '{name}' to element '{element_guid}'.")
        element = self.repository.GetElementByGuid(element_guid)
        if not element:
            raise EAConnectorError(f"Element with GUID '{element_guid}' not found.")
        try:
            method = element.Methods.AddNew(name, return_type)
            method.Visibility = visibility
            method.IsStatic = is_static
            method.Update()
            if parameters:
                for p in parameters:
                    param = method.Parameters.AddNew(p["name"], p["type"])
                    param.Update()
                method.Parameters.Refresh()
            element.Methods.Refresh()
            return {
                "name": method.Name,
                "return_type": method.ReturnType,
                "visibility": method.Visibility,
                "parameters": [{"name": p["name"], "type": p["type"]} for p in (parameters or [])]
            }
        except Exception as e:
            raise EAConnectorError("Failed to add operation.", details=str(e))

    def create_connector(self, source_guid: str, target_guid: str, connector_type: str = "Association",
                         name: str = "", source_role: str = "", target_role: str = "",
                         is_return: bool = False) -> Dict[str, Any]:
        """Create a connector between two elements.

        For Sequence connectors:
          is_return=False  -> call message  (solid arrow,  TransitionAction='Call')
          is_return=True   -> return message (dashed arrow, TransitionAction='Return')
        """
        self.logger.info(f"Creating '{connector_type}' connector from '{source_guid}' to '{target_guid}'.")
        source = self.repository.GetElementByGuid(source_guid)
        target = self.repository.GetElementByGuid(target_guid)
        if not source:
            raise EAConnectorError(f"Source element '{source_guid}' not found.")
        if not target:
            raise EAConnectorError(f"Target element '{target_guid}' not found.")
        try:
            conn = source.Connectors.AddNew(name, connector_type)
            conn.SupplierID = target.ElementID
            if source_role:
                conn.ClientEnd.Role = source_role
                conn.ClientEnd.Update()
            if target_role:
                conn.SupplierEnd.Role = target_role
                conn.SupplierEnd.Update()
            if connector_type == "Sequence":
                conn.TransitionEvent = "Synchronous"
                conn.TransitionAction = "Return" if is_return else "Call"
            conn.Update()
            source.Connectors.Refresh()
            return {
                "guid": conn.ConnectorGUID,
                "type": conn.Type,
                "name": conn.Name,
                "source_guid": source_guid,
                "target_guid": target_guid,
                "message_kind": ("return" if is_return else "call") if connector_type == "Sequence" else None,
            }
        except Exception as e:
            raise EAConnectorError("Failed to create connector.", details=str(e))

    def remove_connector(self, connector_guid: str) -> Dict[str, Any]:
        """Remove a connector by its GUID"""
        self.logger.info(f"Removing connector '{connector_guid}'.")
        connector = self.repository.GetConnectorByGuid(connector_guid)
        if not connector:
            raise EAConnectorError(f"Connector '{connector_guid}' not found.")
        try:
            source = self.repository.GetElementByID(connector.ClientID)
            for i in range(source.Connectors.Count):
                conn = source.Connectors.GetAt(i)
                if conn.ConnectorGUID == connector_guid:
                    source.Connectors.DeleteAt(i, False)
                    source.Connectors.Refresh()
                    return {"status": "success", "deleted_guid": connector_guid}
            raise EAConnectorError(f"Connector '{connector_guid}' not found in element connectors.")
        except EAConnectorError:
            raise
        except Exception as e:
            raise EAConnectorError("Failed to remove connector.", details=str(e))

    def remove_dependencies_between(self, source_guid: str, target_guid: str) -> int:
        """Remove all Dependency connectors from source to target. Returns count removed."""
        self.logger.info(f"Removing Dependency connectors from '{source_guid}' to '{target_guid}'.")
        source = self.repository.GetElementByGuid(source_guid)
        target = self.repository.GetElementByGuid(target_guid)
        if not source:
            raise EAConnectorError(f"Source element '{source_guid}' not found.")
        if not target:
            raise EAConnectorError(f"Target element '{target_guid}' not found.")
        try:
            to_delete = []
            for i in range(source.Connectors.Count):
                conn = source.Connectors.GetAt(i)
                if conn.Type != "Dependency":
                    continue
                other_id = conn.SupplierID if conn.ClientID == source.ElementID else conn.ClientID
                if other_id == target.ElementID:
                    to_delete.append(i)
            for i in reversed(to_delete):
                source.Connectors.DeleteAt(i, False)
            if to_delete:
                source.Connectors.Refresh()
            return len(to_delete)
        except Exception as e:
            raise EAConnectorError("Failed to remove dependencies.", details=str(e))

    def add_existing_element_to_diagram(self, diagram_guid: str, element_guid: str) -> Dict[str, Any]:
        """Add an existing element to an existing diagram"""
        self.logger.info(f"Adding element '{element_guid}' to diagram '{diagram_guid}'.")
        diagram = self.repository.GetDiagramByGuid(diagram_guid)
        element = self.repository.GetElementByGuid(element_guid)
        if not diagram:
            raise EAConnectorError(f"Diagram '{diagram_guid}' not found.")
        if not element:
            raise EAConnectorError(f"Element '{element_guid}' not found.")
        try:
            obj = diagram.DiagramObjects.AddNew("", "")
            obj.ElementID = element.ElementID
            obj.Update()
            diagram.DiagramObjects.Refresh()
            return {
                "status": "success",
                "element_guid": element_guid,
                "diagram_guid": diagram_guid
            }
        except Exception as e:
            raise EAConnectorError("Failed to add element to diagram.", details=str(e))

    def get_connector_details(self, connector_guid: str) -> Dict[str, Any]:
        """Get full details of a connector by GUID, including sequence number and guard."""
        self.logger.info(f"Getting connector details for '{connector_guid}'.")
        connector = self.repository.GetConnectorByGuid(connector_guid)
        if not connector:
            raise EAConnectorError(f"Connector '{connector_guid}' not found.")
        try:
            client = self.repository.GetElementByID(connector.ClientID)
            supplier = self.repository.GetElementByID(connector.SupplierID)
            return {
                "guid": connector.ConnectorGUID,
                "name": connector.Name,
                "type": connector.Type,
                "sequence_no": connector.SequenceNo,
                "message_kind": connector.TransitionAction or None,
                "guard": connector.TransitionGuard or None,
                "notes": connector.Notes or None,
                "client_guid": client.ElementGUID if client else None,
                "client_name": client.Name if client else None,
                "supplier_guid": supplier.ElementGUID if supplier else None,
                "supplier_name": supplier.Name if supplier else None,
            }
        except Exception as e:
            raise EAConnectorError("Failed to get connector details.", details=str(e))

    def get_diagram_connectors(self, diagram_guid: str) -> list:
        """List all connectors visible in a diagram, ordered by sequence number.

        Uses DiagramLinks (the diagram-level link table) to enumerate only connectors
        that are actually rendered on the diagram, avoiding duplicates that would appear
        when iterating per-element connectors.
        """
        self.logger.info(f"Getting connectors for diagram '{diagram_guid}'.")
        diagram = self.repository.GetDiagramByGuid(diagram_guid)
        if not diagram:
            raise EAConnectorError(f"Diagram '{diagram_guid}' not found.")
        try:
            seen: set = set()
            rows = []
            for link in diagram.DiagramLinks:
                conn = self.repository.GetConnectorByID(link.ConnectorID)
                if not conn or conn.ConnectorGUID in seen:
                    continue
                seen.add(conn.ConnectorGUID)
                client = self.repository.GetElementByID(conn.ClientID)
                supplier = self.repository.GetElementByID(conn.SupplierID)
                rows.append({
                    "guid": conn.ConnectorGUID,
                    "name": conn.Name,
                    "type": conn.Type,
                    "sequence_no": conn.SequenceNo,
                    "message_kind": conn.TransitionAction or None,
                    "guard": conn.TransitionGuard or None,
                    "notes": conn.Notes or None,
                    "client_guid": client.ElementGUID if client else None,
                    "client_name": client.Name if client else None,
                    "supplier_guid": supplier.ElementGUID if supplier else None,
                    "supplier_name": supplier.Name if supplier else None,
                })
            rows.sort(key=lambda r: r["sequence_no"] if r["sequence_no"] else 0)
            return rows
        except Exception as e:
            raise EAConnectorError("Failed to get diagram connectors.", details=str(e))

    def get_combined_fragment(self, element_guid: str) -> Dict[str, Any]:
        """Read a CombinedFragment element with its interaction operands.

        CombinedFragments represent alt/loop/opt/par blocks in sequence diagrams.
        The operator is stored as the element's Stereotype; operands are embedded
        elements of type InteractionOperand whose guard condition is in their Notes.
        """
        self.logger.info(f"Getting combined fragment for element '{element_guid}'.")
        element = self.repository.GetElementByGuid(element_guid)
        if not element:
            raise EAConnectorError(f"Element '{element_guid}' not found.")
        try:
            operands = []
            for emb in element.EmbeddedElements:
                if emb.Type == "InteractionOperand":
                    operands.append({
                        "guid": emb.ElementGUID,
                        "name": emb.Name or None,
                        "guard": emb.Notes or None,
                    })
            # EA Trial stores the guard directly in element.Notes when there are no operands
            if not operands and element.Notes:
                operands.append({"guid": None, "name": None, "guard": element.Notes})
            return {
                "guid": element.ElementGUID,
                "name": element.Name,
                "type": element.Type,
                "operator": element.Stereotype or None,
                "notes": element.Notes or None,
                "operands": operands,
            }
        except Exception as e:
            raise EAConnectorError("Failed to get combined fragment.", details=str(e))

    def rename_connector(self, connector_guid: str, name: str) -> Dict[str, Any]:
        """Rename a connector."""
        self.logger.info(f"Renaming connector '{connector_guid}' to '{name}'.")
        connector = self.repository.GetConnectorByGuid(connector_guid)
        if not connector:
            raise EAConnectorError(f"Connector '{connector_guid}' not found.")
        try:
            old_name = connector.Name
            connector.Name = name
            connector.Update()
            return {
                "guid": connector.ConnectorGUID,
                "old_name": old_name,
                "name": connector.Name,
            }
        except Exception as e:
            raise EAConnectorError("Failed to rename connector.", details=str(e))

    def create_combined_fragment(self, diagram_guid: str, operator: str,
                                  guard: str = "",
                                  seq_from: Optional[int] = None,
                                  seq_to: Optional[int] = None,
                                  left: Optional[int] = None,
                                  top: Optional[int] = None,
                                  right: Optional[int] = None,
                                  bottom: Optional[int] = None) -> Dict[str, Any]:
        """Create a CombinedFragment (loop/alt/opt/par) in a sequence diagram.

        If left/top/right/bottom are omitted the method estimates the position
        from the diagram's lifeline bounds and the seq_from/seq_to range.
        operator values: loop, alt, opt, par, break, critical, ignore, consider
        """
        self.logger.info(f"Creating '{operator}' CombinedFragment in diagram '{diagram_guid}'.")
        diagram = self.repository.GetDiagramByGuid(diagram_guid)
        if not diagram:
            raise EAConnectorError(f"Diagram '{diagram_guid}' not found.")
        try:
            # --- auto-position from lifeline bounds + sequence numbers ---
            if None in (left, top, right, bottom):
                lf_left, lf_right = 9999999, -9999999
                lf_top, lf_bottom = None, None
                msg_count = diagram.DiagramLinks.Count
                for obj in diagram.DiagramObjects:
                    lf_left = min(lf_left, obj.Left)
                    lf_right = max(lf_right, obj.Right)
                    if lf_top is None or obj.Top > lf_top:
                        lf_top = obj.Top
                    if lf_bottom is None or obj.Bottom < lf_bottom:
                        lf_bottom = obj.Bottom

                if lf_top is None:
                    lf_top, lf_bottom = -50, -900
                diagram_height = abs(lf_bottom - lf_top)
                spacing = diagram_height / max(msg_count + 1, 1)

                sf = seq_from if seq_from is not None else 1
                st = seq_to   if seq_to   is not None else sf

                # Y in EA sequence diagrams is negative and grows downward
                y_top    = lf_top - (sf - 1.3) * spacing
                y_bottom = lf_top - (st + 0.3)  * spacing

                left   = left   if left   is not None else lf_left - 10
                right  = right  if right  is not None else lf_right + 10
                top    = top    if top    is not None else int(y_top)
                bottom = bottom if bottom is not None else int(y_bottom)

            # --- create the CombinedFragment element ---
            # EA uses "InteractionFragment" as the element type for CombinedFragments.
            # The operator (loop/alt/opt/...) goes in Stereotype; the guard goes in Notes.
            package = self.repository.GetPackageByID(diagram.PackageID)
            cf = package.Elements.AddNew(operator, "InteractionFragment")
            cf.Stereotype = operator
            if guard:
                cf.Notes = guard
            cf.Update()
            package.Elements.Refresh()

            # Place on the diagram
            obj = diagram.DiagramObjects.AddNew("", "")
            obj.ElementID = cf.ElementID
            obj.Left   = left
            obj.Right  = right
            obj.Top    = top
            obj.Bottom = bottom
            obj.Update()
            diagram.DiagramObjects.Refresh()
            diagram.Update()

            return {
                "guid": cf.ElementGUID,
                "name": cf.Name,
                "operator": operator,
                "guard": guard,
                "position": {"left": left, "top": top, "right": right, "bottom": bottom},
            }
        except EAConnectorError:
            raise
        except Exception as e:
            raise EAConnectorError("Failed to create combined fragment.", details=str(e))

    def remove_element(self, element_guid: str) -> Dict[str, Any]:
        """Remove an element from its package (and from all diagrams it appears on)."""
        self.logger.info(f"Removing element '{element_guid}'.")
        element = self.repository.GetElementByGuid(element_guid)
        if not element:
            raise EAConnectorError(f"Element '{element_guid}' not found.")
        try:
            name = element.Name
            etype = element.Type
            package = self.repository.GetPackageByID(element.PackageID)
            for i in range(package.Elements.Count):
                el = package.Elements.GetAt(i)
                if el.ElementGUID == element_guid:
                    package.Elements.DeleteAt(i, False)
                    package.Elements.Refresh()
                    return {"status": "success", "deleted_guid": element_guid, "name": name, "type": etype}
            raise EAConnectorError(f"Element '{element_guid}' not found in its package.")
        except EAConnectorError:
            raise
        except Exception as e:
            raise EAConnectorError("Failed to remove element.", details=str(e))

    def set_connector_sequence_no(self, connector_guid: str, sequence_no: int) -> Dict[str, Any]:
        """Set the sequence number (vertical position) of a message in a sequence diagram."""
        self.logger.info(f"Setting sequence_no={sequence_no} on connector '{connector_guid}'.")
        connector = self.repository.GetConnectorByGuid(connector_guid)
        if not connector:
            raise EAConnectorError(f"Connector '{connector_guid}' not found.")
        try:
            old_seq = connector.SequenceNo
            connector.SequenceNo = sequence_no
            connector.Update()
            return {
                "guid": connector.ConnectorGUID,
                "name": connector.Name,
                "old_sequence_no": old_seq,
                "sequence_no": connector.SequenceNo,
            }
        except Exception as e:
            raise EAConnectorError("Failed to set connector sequence number.", details=str(e))

    def reorder_sequence_diagram(self, diagram_guid: str, ordered_guids: list) -> list:
        """Assign sequence numbers 1..N to connectors in the given order.

        ordered_guids — list of connector GUIDs in the desired top-to-bottom order.
        Every GUID must belong to a connector visible in the diagram.
        Returns a list of {guid, name, old_sequence_no, sequence_no} dicts.
        """
        self.logger.info(f"Reordering {len(ordered_guids)} connectors in diagram '{diagram_guid}'.")
        diagram = self.repository.GetDiagramByGuid(diagram_guid)
        if not diagram:
            raise EAConnectorError(f"Diagram '{diagram_guid}' not found.")
        try:
            results = []
            for rank, guid in enumerate(ordered_guids, 1):
                conn = self.repository.GetConnectorByGuid(guid)
                if not conn:
                    raise EAConnectorError(f"Connector '{guid}' not found.")
                old_seq = conn.SequenceNo
                conn.SequenceNo = rank
                conn.Update()
                results.append({
                    "guid": conn.ConnectorGUID,
                    "name": conn.Name,
                    "old_sequence_no": old_seq,
                    "sequence_no": rank,
                })
            diagram.Update()
            return results
        except EAConnectorError:
            raise
        except Exception as e:
            raise EAConnectorError("Failed to reorder sequence diagram.", details=str(e))

    def save(self):
        """Explicitly save the repository."""
        self.logger.info("Saving repository changes.")
        try:
            # EA repository doesn't have a direct 'Save' method.
            # Changes are typically saved on CloseFile().
            # This is a placeholder for any future save logic.
            pass
        except Exception as e:
            raise EAConnectorError("Failed to save repository.", details=str(e))

    def disconnect(self):
        """Close the repository and quit the EA application."""
        self.logger.info("Disconnecting from EA.")
        try:
            if self.repository:
                self.repository.CloseFile()
                self.repository = None
                self.logger.info("Repository file closed.")
            if self.ea_app:
                self.ea_app.Quit()
                self.ea_app = None
                self.logger.info("EA application quit.")
        except Exception as e:
            raise EAConnectorError("Failed to disconnect from EA.", details=str(e))
        finally:
            pythoncom.CoUninitialize()

if __name__ == '__main__':
    # This block is for standalone testing of the connector
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    logger.info("Running EAConnector in standalone mode for testing.")
    
    # Example usage:
    # You need to have an EA instance running and a .env file with EA_FILE_PATH
    # or provide the path directly.
    try:
        connector = EAConnector()
        # Load .env file for EA_FILE_PATH
        from dotenv import load_dotenv
        load_dotenv()
        ea_file = os.getenv("EA_FILE_PATH")
        
        if not ea_file or not os.path.exists(ea_file):
            logger.error("EA_FILE_PATH not found in .env or the file does not exist.")
            logger.error("Please create a .env file with EA_FILE_PATH pointing to your .eapx file.")
        else:
            connector.connect(ea_file)
            logger.info("Connection test successful.")
            # Further test calls can be added here
            # e.g., connector.get_package("{GUID}")
            
    except EAConnectorError as e:
        logger.error(f"An error occurred: {e.message} - Details: {e.details}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
