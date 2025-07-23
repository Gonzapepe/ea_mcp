from ea_connector import EAConnector

def test_ea_connectivity():
    """Test connection to Enterprise Architect and verify package existence"""
    connector = EAConnector()
    
    # Test connection
    connected = connector.connect()
    print("Connected to EA:", connected)
    
    if connected:
        # Test package lookup - GUID must be in {GUID} format for EA
        package_guid = "{573339CB-887D-48ae-BFEF-77F8EBDBF38B}"
        package = connector.get_package(package_guid)
        print(f"Package with GUID {package_guid} exists: {package is not None}")
    else:
        print("Skipping package check - not connected to EA")

def test_diagram_creation_and_modification():
    connector = EAConnector()
    if connector.connect():
        package_guid = "{573339CB-887D-48ae-BFEF-77F8EBDBF38B}"
        diagram_name = "My Automated Test Diagram"
        diagram_type = "Sequence"

        # 1. Create the diagram
        diagram = connector.create_diagram(package_guid, diagram_name, diagram_type)
        print(f"Diagram '{diagram_name}' created successfully: {diagram is not None}")

        if diagram:
            diagram_guid = diagram["guid"]
            print(f"-> Diagram details: {diagram}")

            # 2. Add elements to the diagram
            print("\nAdding elements...")
            element1 = connector.add_element_to_diagram(diagram_guid, "User", "Actor")
            print(f"Element 'User' added: {element1 is not None}")
            if element1:
                print(f"-> Element 1 details: {element1}")

            element2 = connector.add_element_to_diagram(diagram_guid, "System", "Object", stereotype="boundary")
            print(f"Element 'System' (Boundary Lifeline) added: {element2 is not None}")
            if element2:
                print(f"-> Element 2 details: {element2}")

            # 3. Apply auto-layout
            print("\nApplying auto-layout...")
            layout_success = connector.auto_layout_diagram(diagram_guid)
            print(f"Auto-layout applied successfully: {layout_success}")
    else:
        print("Not connected to EA, cannot create diagram.")
