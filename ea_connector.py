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
                shutil.rmtree(gen_py_path)
            
            # Remove corrupted modules from sys.modules
            for mod in list(sys.modules):
                if mod.startswith('win32com.gen_py'):
                    del sys.modules[mod]
            
            try:
                self.ea_app = win32com.client.Dispatch("EA.App")
                self.logger.info("Connected to EA successfully after cache cleanup.")
                return True
            except Exception as e:
                raise EAConnectorError("Failed to connect to EA after cache cleanup.", details=str(e))
        
    def connect(self, ea_file_path: Optional[str] = None):
        """Connect to Enterprise Architect via COM"""
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

            self.repository.OpenFile(ea_file_path)
            self.logger.info(f"Successfully opened EA file: {ea_file_path}")
        except EAConnectorError:
            # Re-raise EAConnectorError as-is to preserve specific error messages
            raise
        except Exception as e:
            raise EAConnectorError("Failed to connect to EA repository.", details=str(e))
            
    def create_diagram(self, package_guid: str, name: str, diagram_type: str) -> Dict[str, Any]:
        """Create a new diagram in EA"""
        package = self.repository.GetPackageByGuid(package_guid)
        if not package:
            raise EAConnectorError(f"Package with GUID '{package_guid}' not found.")
            
        try:
            diagrams = package.Diagrams
            diagram = diagrams.AddNew(name, diagram_type)
            diagram.Update()
            diagrams.Refresh()
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

            return {
                "guid": element.ElementGUID,
                "name": element.Name,
                "type": element.Type
            }
        except Exception as e:
            raise EAConnectorError("Failed to add element to diagram.", details=str(e))

    def auto_layout_diagram(self, diagram_guid: str, layout_style: int = 0):
        """Automatically layout a diagram"""
        diagram = self.repository.GetDiagramByGuid(diagram_guid)
        if not diagram:
            raise EAConnectorError(f"Diagram with GUID '{diagram_guid}' not found.")
        
        try:
            project = self.repository.GetProjectInterface()
            project.LayoutDiagram(diagram.DiagramGUID, layout_style)
            self.repository.ReloadDiagram(diagram.DiagramID)
        except Exception as e:
            raise EAConnectorError("Failed to auto-layout diagram.", details=str(e))

    def get_package(self, package_guid: str) -> Dict[str, Any]:
        """Retrieve a package by its GUID"""
        package = self.repository.GetPackageByGuid(package_guid)
        if not package:
            raise EAConnectorError(f"Package with GUID '{package_guid}' not found.")
        
        try:
            return {
                "guid": package.PackageGUID,
                "name": package.Name,
                "notes": package.Notes
            }
        except Exception as e:
            raise EAConnectorError("Failed to retrieve package details.", details=str(e))
