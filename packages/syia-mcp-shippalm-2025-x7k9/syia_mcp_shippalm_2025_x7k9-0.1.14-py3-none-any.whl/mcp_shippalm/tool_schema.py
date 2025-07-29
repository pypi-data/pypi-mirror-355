import mcp.types as types

shippalm_tools = [
    types.Tool(
        name="urgent_requisition_from_shippalm",
        description="""Automate retrieval of URGENT priority requisitions for a specific vessel from ShipPalm system.
        
        This tool:
        - Logs into ShipPalm via Microsoft SSO authentication
        - Navigates to Requisition > ALL section
        - Applies vessel name filter and URGENT priority filter
        - Extracts structured table data containing requisition details (order numbers, descriptions, quantities, etc.)
        - Captures full-page screenshot for visual reference
        - Returns both text/HTML table content and screenshot file path
        
        Use this for monitoring critical supply chain issues and urgent material requirements on vessels.
        Get the shippalmDoc from the get_vessel_details tool.""",
        inputSchema={
            "type": "object",
            "properties": {
                "vessel_name": {"type": "string", "description": "Name of the vessel"},
                "shippalmDoc": {"type": "string", "description": "Document type for determining login URL"}
            },
            "required": ["vessel_name", "shippalmDoc"]
        },
    ),
    types.Tool(
        name="expired_certificate_from_shippalm",
        description="""Retrieve expired vessel certificates and survey information from ShipPalm system.
        
        This tool:
        - Logs into ShipPalm via Microsoft SSO authentication
        - Navigates to Certificate & Survey/Service > Vessel Certificates section
        - Applies vessel name filter and "Expired" due status filter
        - Extracts certificate details including names, issue dates, expiry dates, and status
        - Captures full-page screenshot showing expired certificates
        - Returns structured table data and screenshot path
        
        Essential for compliance monitoring and ensuring vessel certification requirements are met.
        Get the shippalmDoc from the get_vessel_detaila tool.""",
        inputSchema={
            "type": "object",
            "properties": {
                "vessel_name": {"type": "string", "description": "Name of the vessel"},
                "shippalmDoc": {"type": "string", "description": "Document type for determining login URL"}

            },
            "required": ["vessel_name", "shippalmDoc"]
        },
    ),
    types.Tool(
        name="critical_spares_inventory_from_shippalm",
        description="""Extract critical spares inventory data for a specific vessel from ShipPalm system.
        
        This tool:
        - Logs into ShipPalm via Microsoft SSO authentication
        - Navigates to Inventory > All Items > Critical Spares section
        - Applies vessel-specific filter to show only relevant inventory
        - Retrieves detailed spares information including part numbers, descriptions, quantities on hand, and minimum stock levels
        - Captures full-page screenshot of the critical spares inventory
        - Returns comprehensive table data and screenshot path
        
        Critical for maintenance planning and ensuring essential spare parts availability for vessel operations.
        Get the shippalmDoc from the get_vessel_detaila tool.""",
        inputSchema={
            "type": "object",
            "properties": {
                "vessel_name": {"type": "string", "description": "Name of the vessel"},
                "shippalmDoc": {"type": "string", "description": "Document type for determining login URL"}
            },
            "required": ["vessel_name", "shippalmDoc"]
        },
    ),
    types.Tool(
        name="position_book_report_from_shippalm",
        description="""Generate Position Book Report for a specific vessel from ShipPalm system.
        
        This tool:
        - Logs into ShipPalm via Microsoft SSO authentication
        - Navigates to Voyage > Position Book Report section
        - Applies vessel name filter to show specific vessel data
        - Extracts voyage and position information including ports, dates, and operational details
        - Captures full-page screenshot of the position book report
        - Returns formatted table data and screenshot path
        
        Essential for voyage tracking, operational planning, and fleet management oversight.
        Get the shippalmDoc from the get_vessel_detaila tool.""",
        inputSchema={
            "type": "object",
            "properties": {
                "vessel_name": {"type": "string", "description": "Name of the vessel"},
                "shippalmDoc": {"type": "string", "description": "Document type for determining login URL"}
            },
            "required": ["vessel_name", "shippalmDoc"]
        },
    ),

    types.Tool(
        name="purchase_order_data_from_shippalm",
        description="""Retrieve detailed information for a specific Purchase Order number from ShipPalm system.
        
        This tool:
        - Logs into ShipPalm via Microsoft SSO authentication
        - Navigates to Requisition > ALL section
        - Filters by the specific order number to locate exact purchase order
        - Extracts comprehensive order details including line items, quantities, prices, vendors, and delivery information
        - Captures full-page screenshot showing complete order information
        - Returns structured table data and screenshot path
        
        Vital for purchase order tracking, vendor management, and procurement process monitoring.
        For Vessel Name , Extract the first four characters from the Purchase Order number (e.g., 'UMAG' from 'UMAG25S0078') or (e.g., 'SANG' from 'SANG25S0235') and use this as input to the get_vessel_details tool to retrieve the shippalmDoc. 
        Pass the retrieved shippalmDoc value here.""",
        inputSchema={
            "type": "object",
            "properties": {
                "order_number": {"type": "string", "description": "Purchase order number to filter by"},
                "shippalmDoc": {"type": "string", "description": "Document type for determining login URL from get_vessel_detaila tool"}
            },
            "required": ["order_number", "shippalmDoc"]
        },
    ),
    types.Tool(
        name="purchase_requisition_order_data_from_shippalm",
        description="""Retrieve detailed information for a specific Purchase Requisition number from ShipPalm system.
        
        This tool:
        - Logs into ShipPalm via Microsoft SSO authentication
        - Navigates to Requisition > ALL section
        - Filters by the specific requisition number to locate exact purchase requisition
        - Extracts detailed requisition information including requested items, quantities, justifications, and approval status
        - Captures full-page screenshot showing complete requisition details
        - Returns structured table data and screenshot path
        
        Essential for requisition tracking, approval workflow monitoring, and procurement request management.
        Extract the first four characters from the Purchase Requisition number (e.g., 'UMAG' from 'UMAG25S0078') or (e.g., 'PWNW' from 'PB-PWNW23000621') and use this as input to the get_vessel_details tool to retrieve the shippalmDoc. 
        Pass the retrieved shippalmDoc value here.""",
        inputSchema={
            "type": "object",
            "properties": {
                "requisition_number": {"type": "string", "description": "Requisition number to filter by"},
                "shippalmDoc": {"type": "string", "description": "Document type for determining login URL"}
            },
            "required": ["requisition_number", "shippalmDoc"]
        },
    ),

] 



tool_definitions = shippalm_tools 