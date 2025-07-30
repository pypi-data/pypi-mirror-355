import json
from typing import Dict, Any, Union, Optional
from pathlib import Path
from lax_mcp_flow_generation_cursor_client.core.settings import settings
from lax_mcp_flow_generation_cursor_client.core.client import backend_client
from lax_mcp_flow_generation_cursor_client.utils.file_handler import file_handler
from lax_mcp_flow_generation_cursor_client.utils.logger import get_logger

logger = get_logger(__name__)

async def validate_flow(full_path_to_flow_json: Union[Dict[str, Any], str], save_to_lax: bool = True) -> Dict[str, Any]:
    """
    Validates a flow JSON structure and returns the formatted flow if successful. ALWAYS call this tool every time you write a flow to validate it and get the properly formatted flow with UUIDs and tags.
    When updating / modifying an existing flow, always have the flow id in the flow json. DO *NOT* remove/change the flow id.
    Verify node updates using the search nodes and/or search_flows_by_node tools before validating it
    Args:
        full_path_to_flow_json: The full path to a JSON file containing the flow
        save_to_lax: Whether to save the flow to LAX if validation is successful. Default is True.
        
    Returns:
        dict: On success - the properly formatted flow with UUIDs and tags
              On failure - error information
    """
    try:
        # Handle file path input
        if isinstance(full_path_to_flow_json, str):
            if file_handler.is_valid_path(full_path_to_flow_json):
                logger.info(f"Reading flow from file: {full_path_to_flow_json}")
                flow_json = file_handler.read_json_file(full_path_to_flow_json)
            else:
                return {"error": f"File not found or invalid path: {full_path_to_flow_json} | Ensure you are using the entire full absolute path to the file not just the relative path"}
        else:
            flow_json = full_path_to_flow_json
        
        # Forward to backend server
        result = await backend_client.call_tool("validate_flow", {
            "flow_json": flow_json,
            "save_to_lax": save_to_lax
        })
        
        return result
        
    except Exception as e:
        logger.error(f"Error in validate_flow proxy: {e}")
        return {"error": str(e)}

async def search_flows(query: str, top_k: int = 1) -> Dict[str, Any]:
    """
    Use this tool to search for real-world flows that have similar functionality to what you're building.
    
    Call this tool when:
    - You want to see examples of flows that solve similar problems
    - User describes a use case and you want to find existing implementations for reference
    - You need inspiration for flow structure and design patterns
    - You want to understand how similar business processes are automated
    - You need to see real examples of node connections and data flow patterns
    - User mentions a specific business process and you want to find similar implementations
    
    This tool searches through a database of existing flows to find ones with similar functionality.
    Use the results to understand patterns, node usage, and flow architecture for similar use cases.
    
    Args:
        query: Detailed description of the flow functionality you're looking for
        top_k: Number of top matching flows to return (default: 1)
        
    Returns:
        List of matching flows with their structure and implementation details
    """
    try:
        result = await backend_client.call_tool("search_flows", {
            "query": query,
            "top_k": top_k,
            "columns": None
        })
        return result
        
    except Exception as e:
        logger.error(f"Error in search_flows proxy: {e}")
        return {"error": str(e)}

async def search_flows_by_node(node_name: str, top_k: int = 1) -> Dict[str, Any]:
    """
    Use this tool to see how a specific node is used in real-world flows.
    
    Call this tool when:
    - You found a node through NodeSearch and want to see practical usage examples
    - You need to understand how to properly configure a specific node
    - You want to see what other nodes are commonly connected to a particular node
    - You need examples of data transformations or connections for a specific node
    - You want to understand the typical flow patterns involving a particular node
    - You're unsure about how to integrate a node into your flow design
    
    This tool finds real flows that use the specified node, showing you practical examples of configuration, connections, and usage patterns.
        
    Args:
        node_name: The exact name of the node (use the exact name from node search results)
        top_k: Number of example flows to return (default: 1)
        
    Returns:
        List of flows that use this node, with context about how it's configured and connected
    """
    try:
        result = await backend_client.call_tool("search_flows_by_node", {
            "node_name": node_name,
            "top_k": top_k
        })
        return result
        
    except Exception as e:
        logger.error(f"Error in search_flows_by_node proxy: {e}")
        return {"error": str(e)}

async def search_nodes(query: str, top_k: int = 2) -> Dict[str, Any]:
    """
    Use this tool to search for specific nodes (building blocks) that can be used in your flow.
    
    Call this tool when:
    - You need to find nodes with specific functionality (e.g., "email sending", "data transformation", "API call")
    - User describes a particular operation and you need to find the right node type for it
    - You want to explore what nodes are available for a specific use case
    - You need nodes for data processing, integrations, triggers, or outputs
    - User mentions specific technologies or services and you need compatible nodes
    - You want to understand what built-in capabilities exist for common operations
    
    This tool searches through a database of available nodes using semantic similarity.
    Each result includes node details, parameters, input/output schemas, and usage examples.
    
    Args:
        query: Detailed description of the node functionality you're looking for
        top_k: Number of top matching nodes to return (default: 2)
        
    Returns:
        List of matching nodes with their configuration details and schemas
    """
    try:
        result = await backend_client.call_tool("search_nodes", {
            "query": query,
            "top_k": top_k
        })
        return result
        
    except Exception as e:
        logger.error(f"Error in search_nodes proxy: {e}")
        return {"error": str(e)}

async def check_flow_exists_lax(flow_name: str) -> Dict[str, Any]:
    """
    Use this tool to check if a flow with a specific name already exists in the LAX system.
    
    Call this tool when:
    - User mentions they want to create a flow and you need to avoid naming conflicts
    - You need to verify if a referenced flow actually exists before using it
    - User asks to modify/update an existing flow and you need to confirm it exists
    - You want to suggest alternative names if the desired flow name is already taken
    - Before creating integrations or dependencies on flows that may or may not exist
    
    This tool queries the LAX system to determine if a flow with the given name is already registered.
    Use this for validation before flow creation or when referencing existing flows.
    
    Args:
        flow_name: The exact name of the flow to check for existence
        
    Returns:
        bool: True if the flow exists, False otherwise
    """
    try:
        result = await backend_client.call_tool("check_flow_exists_lax", {
            "flow_name": flow_name
        })
        return result
        
    except Exception as e:
        logger.error(f"Error in check_flow_exists_lax proxy: {e}")
        return {"error": str(e)}

async def search_advanced_features(query: str, top_k: int = 1) -> Dict[str, Any]:
    """
    Use this tool to search for advanced features that can enhance your flow's capabilities.
    
    Call this tool when:
    - You need to implement conditional execution (run nodes only when specific conditions are met)
    - You want to add hooks (pre-execution or post-execution logic)
    - You need to set environment variables for specific nodes
    - You want to implement retry logic or error handling mechanisms
    - User mentions advanced scheduling, triggers, or execution patterns
    - You need features like "run after" dependencies, parallel execution controls
    - You want to add monitoring, logging, or notification capabilities to the flow
    
    This tool searches through a database of advanced features using semantic similarity to find
    features that match your query. Each result includes the feature name, usage instructions,
    when to use it, and concrete examples.
    
    Args:
        query: Detailed description of the advanced functionality you're looking for
        top_k: Number of top matching features to return (default: 1)
        
    Returns:
        List[Dict]: List of matching advanced features with their details
    """
    try:
        result = await backend_client.call_tool("search_advanced_features", {
            "query": query,
            "top_k": top_k
        })
        return result
        
    except Exception as e:
        logger.error(f"Error in search_advanced_features proxy: {e}")
        return {"error": str(e)}

async def search_functions(query: str, top_k: int = 1) -> Dict[str, Any]:
    """
    Use this tool to search for pre-built functions that can be used in the transform node specifically.
    
    Call this tool when:
    - You need to find specific utility functions for data transformation, validation, or processing
    - User mentions specific programming functionality that might already exist (e.g., date parsing, string manipulation)
    - You need functions for API calls, database operations, or file handling
    - You want to find functions with specific parameter signatures or return types
    - You need to understand what built-in functions are available for complex operations
    - User requests functionality that sounds like it might be a common programming pattern
    
    This tool searches through a database of available functions using semantic similarity.
    Each result includes the function title, subtitle, parameters, and formatted features.
    
    Args:
        query: Detailed description of the function functionality you're looking for
        top_k: Number of top matching functions to return (default: 1)
        
    Returns:
        List[Dict]: List of matching functions with their details and parameters
    """
    try:
        result = await backend_client.call_tool("search_functions", {
            "query": query,
            "top_k": top_k
        })
        return result
        
    except Exception as e:
        logger.error(f"Error in search_functions proxy: {e}")
        return {"error": str(e)}

async def fetch_execution_of_node(node_name: str) -> Dict[str, Any]:
    """
    Use this tool to fetch real execution examples of nodes that have dynamic or complex outputs.
    
    Call this tool when:
    - A node's schema indicates it has dynamic outputs that vary based on input
    - You need to understand the actual data structure a node produces in practice
    - The node documentation is unclear about output format and you need real examples
    - You need to see what data transformations are required before/after the node
    - A node's output depends on external API responses or dynamic data sources
    - You're designing data mappings and need to see actual output structures
    
    This tool fetches real execution data from the database to show you exactly what
    a node outputs in practice, including data types, structures, and transformations.
    
    Args:
        node_name: The exact name of the node to fetch execution details for
        
    Returns:
        dict: Real execution data showing inputs, outputs, and transformations for the node
    """
    try:
        result = await backend_client.call_tool("fetch_execution_of_node", {
            "node_name": node_name
        })
        return result
        
    except Exception as e:
        logger.error(f"Error in fetch_execution_of_node proxy: {e}")
        return {"error": str(e)}

async def get_node_by_name(node_name: str) -> Dict[str, Any]:
    """
    Use this tool to get detailed information about a specific node when you know its exact name.
    
    Call this tool when:
    - You know the specific node name and need its complete configuration details
    - You need the exact schema, parameters, or properties of a well-known node
    - User mentions a specific node by name (e.g., "manual_trigger", "transform", "output")
    - You need to verify the capabilities or requirements of a standard node
    - You want to get the definitive information about a commonly used node
    - You need the exact parameter structure for a node you plan to use
    
    This tool retrieves the complete node definition including schema, parameters,
    input/output specifications, and configuration options.
    
    Args:
        node_name: The exact name of the node (must match exactly, e.g. "manual_trigger")
        
    Returns:
        dict: Complete node definition with schema, parameters, and configuration details
    """
    try:
        result = await backend_client.call_tool("get_node_by_name", {
            "node_name": node_name
        })
        return result
        
    except Exception as e:
        logger.error(f"Error in get_node_by_name proxy: {e}")
        return {"error": str(e)}

async def think(thought: str) -> Dict[str, Any]:
    """
    Use this tool when you need to think through complex problems, analyze information, or document your reasoning process.
    
    Call this tool when:
    - You need to analyze complex user requirements or multiple pieces of information
    - You want to break down a complex flow design into logical steps
    - You need to review and evaluate multiple options or approaches
    - You're working through complicated node relationships or data transformations
    - You want to document your reasoning process for complex decisions
    - You need to brainstorm solutions or explore different possibilities
    - You're analyzing retrieved information from other tools and need to synthesize it
    - You want to plan your approach before taking action
    - You need to reflect on user feedback and adjust your strategy
    
    This tool logs your thoughts and reasoning process, helping you organize complex information.
    It also sends a progress update to the user via websocket if available, keeping them informed
    of your thinking process during complex operations.
    
    Args:
        thought: Your detailed thoughts, analysis, or reasoning process
        
    Returns:
        str: The thought string that was logged
    """
    try:
        result = await backend_client.call_tool("think", {
            "thought": thought
        })
        return result
        
    except Exception as e:
        logger.error(f"Error in think proxy: {e}")
        return {"error": str(e)}

async def get_flow_by_name(flow_name: str) -> Dict[str, Any]:
    """
    Use this tool to retrieve detailed information about an existing flow from the LAX system.
    
    Call this tool when:
    - User explicitly mentions that their new flow should call/integrate with an existing flow
    - You need to understand the input/output schema of an existing flow for integration purposes
    - User wants to modify or extend functionality of an existing flow
    - You need to see the structure and nodes of an existing flow to understand how to interface with it
    - User references a specific flow name and you need its configuration details
    - You're creating a flow that needs to pass data to or receive data from an existing flow
    
    This tool fetches the complete flow definition including nodes, connections, input/output schemas,
    and configuration. Use this information to properly integrate with or reference the existing flow.
    
    Args:
        flow_name: The exact name of the flow to retrieve
        
    Returns:
        dict: Complete flow definition with all nodes, connections, and configuration
    """
    try:
        result = await backend_client.call_tool("get_flow_by_name", {
            "flow_name": flow_name
        })

        # If workspace path is set, save the flow to the workspace
        if settings.WORKSPACE_PATH is not None:
            # Save the flow to the workspace
            save_path = Path(settings.WORKSPACE_PATH) / f"{flow_name}.json"
            with open(save_path, "w") as f:
                if isinstance(result, dict):
                    json.dump(result, f)
                elif isinstance(result, str):
                    data_dict = json.loads(result)["flow"]
                    try:
                        del data_dict["status"]
                    except:
                        pass
                    json.dump(data_dict, f, indent=4)
                else:
                    raise ValueError(f"Invalid result type: {type(result)}")

            return f"Flow downloaded successfully and saved to {save_path}. When updating, modify this file directly to save time— DON'T rewrite the entire file just to make a few changes."

        return result
        
    except Exception as e:
        logger.error(f"Error in get_flow_by_name proxy: {e}")
        return {"error": str(e)}

async def save_flow_to_lax(full_path_to_flow_json: Union[Dict[str, Any], str], update_flow: bool = False) -> Dict[str, Any]:
    """
    
    Save a flow to the LAX system. Only use this when the flow has been properly validated and you want to save it to the LAX system. This will save the flow to the LAX system and return the flow ID.
    If you are updating a flow, you need to pass the same flow_id as in the flow originally fetched from the LAX system.
    When updating a flow make sure you keep the following keys intact: "id", "is_published", "is_pre_built", "is_archived", "is_public", "user", "user_id"

    Args:
        full_path_to_flow_json: The full path to a JSON file containing the flow that has already been validated
        update_flow: Whether this is an update to an existing flow
        
    Returns:
        dict: Response from the LAX system
    """
    try:
        # Handle file path input
        if isinstance(full_path_to_flow_json, str):
            if file_handler.is_valid_path(full_path_to_flow_json):
                logger.info(f"Reading flow from file: {full_path_to_flow_json}")
                flow_json = file_handler.read_json_file(full_path_to_flow_json)
            else:
                return {"error": f"File not found or invalid path: {full_path_to_flow_json} | Ensure you are using the entire full absolute path to the file not just the relative path"}
        else:
            flow_json = full_path_to_flow_json
        
        result = await backend_client.call_tool("save_flow_to_lax", {
            "flow_json": flow_json,
            "update_flow": update_flow
        })
        return result
        
    except Exception as e:
        logger.error(f"Error in save_flow_to_lax proxy: {e}")
        return {"error": str(e)}

# Define the proxy tools dictionary
PROXY_TOOLS = {
    "validate_flow": validate_flow,
    "search_flows": search_flows,
    "search_flows_by_node": search_flows_by_node,
    "search_nodes": search_nodes,
    "check_flow_exists_lax": check_flow_exists_lax,
    "search_advanced_features": search_advanced_features,
    "search_functions": search_functions,
    "fetch_execution_of_node": fetch_execution_of_node,
    "get_node_by_name": get_node_by_name,
    "think": think,
    "get_flow_by_name": get_flow_by_name,
    "save_flow_to_lax": save_flow_to_lax,
} 