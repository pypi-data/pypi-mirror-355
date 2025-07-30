import json
from typing import Dict, Optional, List, Any, Callable, Tuple
from agno.tools import tool
from xpander_sdk import ToolCall, ToolCallType
from .base import SDKAdapter


class AgnoAdapter(SDKAdapter):
    """
    Adapter for integrating Agno with xpander.ai.
    
    This class extends SDKAdapter to provide Agno-compatible methods 
    for managing tools and system prompts.
    """

    def __init__(self, api_key: str, agent_id: str, base_url: Optional[str] = None, 
                 organization_id: Optional[str] = None, with_metrics_report: Optional[bool] = False):
        """
        Initialize the AgnoAdapter.

        Args:
            api_key (str): The API key for authentication with xpander.ai.
            agent_id (str): The ID of the xpander.ai agent.
            base_url (Optional[str]): The base URL for the xpander.ai API.
            organization_id (Optional[str]): The organization ID, if applicable.
            with_metrics_report (Optional[bool]): If to auto-report metrics (llm & execution).
        """
        super().__init__(api_key=api_key, agent_id=agent_id, base_url=base_url, 
                         organization_id=organization_id, with_metrics_report=with_metrics_report)
        self.agent.disable_agent_end_tool()

    def get_tools(self) -> List[Callable]:
        """
        Retrieve the tools available for the agent as agno-compatible functions.

        Returns:
            List[Callable]: A list of Agno-compatible tool functions.
        """
        xpander_tools = self.agent.get_tools()
        tools = []

        for tool_schema in xpander_tools:
            function_spec = tool_schema["function"]
            tool_name = function_spec["name"]
            tool_description = function_spec["description"]
            
            parameters = function_spec.get("parameters", {})
            properties = parameters.get("properties", {})
            required_params = parameters.get("required", [])

            agno_tool_func = self._create_agno_tool_function(
                tool_name=tool_name,
                tool_description=tool_description,
                properties=properties,
                required_params=required_params
            )

            tools.append(agno_tool_func)

        return tools

    def _create_agno_tool_function(self, tool_name: str, tool_description: str, 
                                   properties: Dict, required_params: List[str]) -> Callable:
        """Create a dynamic agno tool function from xpander tool schema."""
        
        def dynamic_tool_function(**kwargs) -> str:
            """Execute a tool by calling the xpander.ai agent's tool execution API."""
            
            body_params = {}
            query_params = {}
            path_params = {}

            if "bodyParams" in properties and "properties" in properties["bodyParams"]:
                # Nested structure (like email tool)
                body_param_props = properties["bodyParams"]["properties"]
                query_param_props = properties.get("queryParams", {}).get("properties", {})
                path_param_props = properties.get("pathParams", {}).get("properties", {})
                
                for param_name, param_value in kwargs.items():
                    if param_name in body_param_props:
                        body_params[param_name] = param_value
                    elif param_name in query_param_props:
                        query_params[param_name] = param_value
                    elif param_name in path_param_props:
                        path_params[param_name] = param_value
                    else:
                        body_params[param_name] = param_value
            else:
                # Flat parameter structure
                for param_name, param_value in kwargs.items():
                    if param_name in properties:
                        param_desc = properties[param_name].get("description", "").lower()
                        if "query" in param_desc and "path" not in param_desc:
                            query_params[param_name] = param_value
                        elif "path" in param_desc:
                            path_params[param_name] = param_value
                        else:
                            body_params[param_name] = param_value
                    else:
                        body_params[param_name] = param_value

            xpander_tool_invocation = self.agent.run_tool(
                tool=ToolCall(
                    name=tool_name,
                    type=ToolCallType.XPANDER,
                    payload={
                        "bodyParams": body_params,
                        "queryParams": query_params,
                        "pathParams": path_params
                    }
                )
            )

            stringified_result = json.dumps(xpander_tool_invocation.result)

            if not xpander_tool_invocation.is_success:
                raise Exception(f"Error running tool {tool_name}: {stringified_result}")

            return stringified_result

        # Set function metadata
        dynamic_tool_function.__name__ = tool_name
        dynamic_tool_function.__doc__ = tool_description

        # Create type annotations for agno
        annotations = self._build_annotations(properties, required_params)
        annotations['return'] = str
        dynamic_tool_function.__annotations__ = annotations

        # Apply the @tool decorator
        decorated_function = tool(
            name=tool_name,
            description=tool_description,
            show_result=True
        )(dynamic_tool_function)
        
        if hasattr(decorated_function, '__name__'):
            decorated_function.__name__ = tool_name
            
        # Set parameter schema for agno
        parameter_schema = self._build_parameter_schema(properties, required_params)
        if hasattr(decorated_function, 'parameters'):
            decorated_function.parameters = parameter_schema
        
        return decorated_function

    def _collect_parameters(self, properties: Dict, required_params: List[str]) -> Tuple[Dict, List[str]]:
        """Collect all parameters from nested or flat structure."""
        if "bodyParams" in properties and "properties" in properties["bodyParams"]:
            all_param_props = {}
            all_required = []
            
            for section in ["bodyParams", "queryParams", "pathParams"]:
                if section in properties and "properties" in properties[section]:
                    section_props = properties[section].get("properties", {})
                    section_required = properties[section].get("required", [])
                    all_param_props.update(section_props)
                    all_required.extend(section_required)
            
            return all_param_props, all_required
        else:
            return properties, required_params

    def _build_annotations(self, properties: Dict, required_params: List[str]) -> Dict:
        """Build type annotations for the dynamic function."""
        all_param_props, all_required = self._collect_parameters(properties, required_params)
        annotations = {}
        
        for param_name, param_spec in all_param_props.items():
            param_type = self._get_python_type(param_spec.get("type", "string"))
            if param_name not in all_required:
                param_type = Optional[param_type]
            annotations[param_name] = param_type

        return annotations

    def _build_parameter_schema(self, properties: Dict, required_params: List[str]) -> Dict:
        """Build parameter schema for agno."""
        all_param_props, all_required = self._collect_parameters(properties, required_params)
        return {
            "type": "object",
            "properties": all_param_props,
            "required": all_required
        }

    def _get_python_type(self, json_type: str) -> type:
        """Convert JSON schema type to Python type."""
        type_mapping = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "array": List[Any],
            "object": Dict[str, Any]
        }
        return type_mapping.get(json_type, Any)

    def get_system_prompt(self) -> str:
        """Retrieve the system prompt for the agent."""
        return f"""Agent general instructions: "{self.agent.instructions.general}"
Agent role instructions: "{self.agent.instructions.role}"
Agent goal instructions: "{self.agent.instructions.goal}\"""" 