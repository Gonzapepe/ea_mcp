#!/usr/bin/env python3
import win32com.client
import pythoncom
from typing import Optional, Dict, Any
import logging
import sys
import os
import shutil

class EAConnector:
    """Handles connection and operations with Enterprise Architect"""
    
    def __init__(self):
        self.ea_app = None
        self.repository = None
        self.logger = logging.getLogger(__name__)

    def connect_ea(self):
        try:
            self.ea_app = win32com.client.Dispatch("EA.App")
            print("Connected to EA successfully.")
            
            return True
        except AttributeError:
            print("Failed to connect to EA. Attempting to fix gen_py cache...")
            # Limpiar caché y reintentar
            temp_dir = os.path.join(os.environ['LOCALAPPDATA'], 'Temp')
            gen_py_path = os.path.join(temp_dir, 'gen_py')
            
            if os.path.exists(gen_py_path):
                shutil.rmtree(gen_py_path)
            
            # Eliminar módulos corruptos de sys.modules
            for mod in list(sys.modules):
                if mod.startswith('win32com.gen_py'):
                    del sys.modules[mod]
        
        return win32com.client.Dispatch("EA.App")
        
    def connect(self, ea_file_path: Optional[str] = None) -> bool:
        """Connect to Enterprise Architect via COM"""
        try:
            self.connect_ea()
            self.repository = self.ea_app.Repository
            
            # Load EA file from environment variable if not provided
            if not ea_file_path:
                from dotenv import load_dotenv
                load_dotenv()
                ea_file_path = os.getenv("EA_FILE_PATH")
                if not ea_file_path:
                    self.logger.error("EA_FILE_PATH environment variable not set and no path provided.")
                    return False

            self.repository.OpenFile(ea_file_path)
            self.logger.info(f"Successfully opened EA file: {ea_file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to EA: {str(e)}")
            print(f"Error connecting to EA: {e}")
            return False
            
    def create_diagram(self, package_guid: str, name: str, diagram_type: str) -> Optional[Dict[str, Any]]:
        """Create a new diagram in EA"""
        package = self.repository.GetPackageByGuid(package_guid)
        if not package:
            return None
            
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
            self.logger.error(f"Failed to create diagram: {str(e)}")
            return None
            
    def add_element_to_diagram(self, diagram_guid: str, element_name: str, element_type: str, 
                             stereotype: str = "") -> Optional[Dict[str, Any]]:
        """Add an element to an existing diagram"""
        try:
            diagram = self.repository.GetDiagramByGuid(diagram_guid)
            if not diagram:
                return None
            
            # First create the element in the model (not just the diagram)
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
            self.logger.error(f"Failed to add element to diagram: {str(e)}", exc_info=True)
            return None

    def auto_layout_diagram(self, diagram_guid: str, layout_style: int = 0) -> bool:
        """Automatically layout a diagram"""
        try:
            diagram = self.repository.GetDiagramByGuid(diagram_guid)
            if not diagram:
                return False
            
            # Use EA's auto-layout feature
            project = self.repository.GetProjectInterface()
            project.LayoutDiagram(diagram.DiagramGUID, layout_style)
            
            # Reload the diagram to see changes
            self.repository.ReloadDiagram(diagram.DiagramID)
            return True
        except Exception as e:
            self.logger.error(f"Failed to auto-layout diagram: {str(e)}")
            return False


    def get_package(self, package_guid: str) -> Optional[Dict[str, Any]]:
        """Retrieve a package by its GUID"""
        try:
            package = self.repository.GetPackageByGuid(package_guid)
            if package:
                return {
                    "guid": package.PackageGUID,
                    "name": package.Name,
                    "notes": package.Notes
                }
            return None
        except Exception as e:
            self.logger.error(f"Failed to get package: {str(e)}")
            return None
