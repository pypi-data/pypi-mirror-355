from pydantic import BaseModel
from openagentkit.core.models.responses.usage_responses import UsageResponse
from openagentkit.core.models.responses.tool_response import ToolCall
from openagentkit.core.models.responses.audio_response import AudioResponse
from typing import Optional, List, Dict, Any, Union

class OpenAgentResponse(BaseModel):
    """
    The default Response schema for OpenAgentKit.
    
    Schema:
    ```python
    class OpenAgentResponse(BaseModel):
        role: str
        content: Optional[Union[str, BaseModel, dict]] = None
        tool_calls: Optional[List[ToolCall] = None
        tool_results: Optional[List[Union[Dict[str, Any], BaseModel]]] = None
        refusal: Optional[str] = None
        audio: Optional[AudioResponse] = None
        usage: Optional[UsageResponse] = None
    ```
    Where:
        - `role`: The role of the response.
        - `content`: The content of the response.
        - `tool_calls`: The list of tool calls of the response.
        - `tool_results`: The list of tool results of the response.
        - `refusal`: Response refusal data.
        - `audio`: The audio of the response.
        - `usage`: The usage of the response.
    """
    role: str
    content: Optional[Union[str, BaseModel, dict[str, str], Any]] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_results: Optional[List[Union[Dict[str, Any], BaseModel, Any]]] = None
    refusal: Optional[str] = None
    audio: Optional[AudioResponse] = None
    usage: Optional[UsageResponse] = None