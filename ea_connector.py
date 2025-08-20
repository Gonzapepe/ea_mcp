#!/usr/bin/env python3
import win32com.client
import pythoncom
from typing import Optional, Dict, Any
import logging
import sys
import os
import shutil
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
