#!/usr/bin/env python3
import win32com.client
from typing import Optional, Dict, Any
import logging

class EAConnector:
    """Handles connection and operations with Enterprise Architect"""
    
    def __init__(self):
        self.ea_app = None
        self.repository = None
        self.logger = logging.getLogger(__name__)
        
    def connect(self) -> bool:
        """Connect to Enterprise Architect via COM"""
        try:
            self.ea_app = win32com.client.Dispatch("EA.App")
            self.repository = self.ea_app.Repository
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to EA: {str(e)}")
            return False
            
    def get_package(self, package_guid: str) -> Optional[Any]:
        """Get EA package by GUID"""
        if not self.repository:
            return None
            
        try:
            return self.repository.GetPackageByGuid(package_guid)
        except Exception as e:
            self.logger.error(f"Failed to get package {package_guid}: {str(e)}")
            return None
            
    def create_diagram(self, package_guid: str, name: str, diagram_type: str) -> Optional[Dict[str, Any]]:
        """Create a new diagram in EA"""
        package = self.get_package(package_guid)
        if not package:
            return None
            
        try:
            diagrams = package.Diagrams
            diagram = diagrams.AddNew(name, diagram_type)
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
                             stereotype: str = "", x: int = 0, y: int = 0) -> Optional[Dict[str, Any]]:
        """Add an element to an existing diagram"""
        try:
            diagram = self.repository.GetDiagramByGuid(diagram_guid)
            if not diagram:
                return None
                
            element = diagram.DiagramObjects.AddNew(element_name, element_type)
            if stereotype:
                element.Stereotype = stereotype
            element.left = x
            element.top = y
            diagram.DiagramObjects.Refresh()
            
            return {
                "guid": element.ElementGUID,
                "name": element.Name,
                "type": element.Type
            }
        except Exception as e:
            self.logger.error(f"Failed to add element to diagram: {str(e)}")
            return None
            
    def connect_elements(self, diagram_guid: str, source_guid: str, target_guid: str, 
                        connector_type: str, name: str = "") -> Optional[Dict[str, Any]]:
        """Connect two elements on a diagram"""
        try:
            diagram = self.repository.GetDiagramByGuid(diagram_guid)
            if not diagram:
                return None
                
            connector = diagram.DiagramLinks.AddNew(name, connector_type)
            connector.ConnectorID = source_guid
            connector.SupplierID = target_guid
            diagram.DiagramLinks.Refresh()
            
            return {
                "guid": connector.ConnectorGUID,
                "type": connector.Type,
                "source": source_guid,
                "target": target_guid
            }
        except Exception as e:
            self.logger.error(f"Failed to connect elements: {str(e)}")
            return None
