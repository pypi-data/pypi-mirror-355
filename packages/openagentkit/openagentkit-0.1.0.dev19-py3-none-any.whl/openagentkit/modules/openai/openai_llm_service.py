from typing import Any, Callable, Dict, List, Optional, Literal, Generator
from openai import OpenAI
from openai._types import NOT_GIVEN, NotGiven
from pydantic import BaseModel
from openagentkit.core.handlers import ToolHandler
from openagentkit.core.interfaces.base_llm_model import BaseLLMModel
from openagentkit.core.models.responses import (
    OpenAgentResponse, 
    UsageResponse, 
    PromptTokensDetails, 
    CompletionTokensDetails, 
    OpenAgentStreamingResponse
)
import os
from loguru import logger
class OpenAILLMService(BaseLLMModel):
    def __init__(self, 
                 client: OpenAI = None,
                 model: str = "gpt-4o-mini",
                 tools: Optional[List[Callable[..., Any]]] = NOT_GIVEN,
                 api_key: Optional[str] = os.getenv("OPENAI_API_KEY"),
                 temperature: Optional[float] = 0.3,
                 max_tokens: Optional[int] = None,
                 top_p: Optional[float] = None,
                 ) -> None:
        super().__init__(
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
        )

        self._tool_handler = ToolHandler(
            tools=tools, llm_provider="openai", schema_type="OpenAI"
        )
        
        self._client = client
        if client is None:
            if api_key is None:
                raise ValueError("No API key provided. Please set the OPENAI_API_KEY environment variable or pass it as an argument.")
            self._client = OpenAI(
                api_key=api_key,
            )

        self._model = model
        self._api_key = api_key

    @property
    def model(self) -> str:
        """
        Get the model name.

        Returns:
            The model name.
        """
        return self._model
    
    # Property to access tools from the tool handler
    @property
    def tools(self):
        """
        Get the tools from the tool handler.

        Returns:
            The tools from the tool handler.
        """
        return self._tool_handler.tools
    
    def clone(self) -> 'OpenAILLMService':
        """
        Clone the LLM model instance.

        Returns:
            A clone of the LLM model instance.
        """
        return OpenAILLMService(
            client=self._client,
            model=self._model,
            tools=self.tools,
            api_key=self._api_key,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            top_p=self._top_p,
        )
    
    def _handle_client_request(self,
                              messages: List[Dict[str, str]],
                              tools: Optional[List[Dict[str, Any]]],
                              response_schema: Optional[BaseModel] = NOT_GIVEN,
                              temperature: Optional[float] = None,
                              max_tokens: Optional[int] = None,
                              top_p: Optional[float] = None,
                              audio: Optional[bool] = False,
                              audio_format: Optional[str] = "pcm16",
                              audio_voice: Optional[Literal["alloy", "ash", "coral", "echo", "fable", "onyx", "nova", "sage", "shimmer"]] = "alloy",
                              **kwargs) -> OpenAgentResponse:
        """
        Handle the client request.

        Args:
            messages: The messages to send to the model.
            tools: The tools to use in the response.
            response_schema: The schema to use in the response.
            temperature: The temperature to use in the response.
            max_tokens: The max tokens to use in the response.
            top_p: The top p to use in the response.

        Returns:
            An OpenAgentResponse object.
        """

        temperature = kwargs.get("temperature", temperature)
        if temperature is None:
            temperature = self._temperature

        max_tokens = kwargs.get("max_tokens", max_tokens)
        if max_tokens is None:
            max_tokens = self._max_tokens

        top_p = kwargs.get("top_p", top_p)
        if top_p is None:
            top_p = self._top_p

        if tools is None:
            tools = self.tools

        if response_schema is NOT_GIVEN or isinstance(response_schema, NotGiven):
            # Handle the client request without response schema
            client_response = self._client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    tools=tools,
                    temperature=self._temperature,
                    max_tokens=self._max_tokens,
                    top_p=self._top_p,
                    modalities=["text", "audio"] if audio else ["text"],
                    audio={
                        "format": audio_format,
                        "voice": audio_voice,
                    } if audio else None,
            )
            
            response_message = client_response.choices[0].message

            # Create the response object
            response = OpenAgentResponse(
                role=response_message.role,
                content=response_message.content,
                tool_calls=response_message.tool_calls,
                refusal=response_message.refusal,
                audio=response_message.audio,
            )
        else:
            # Handle the client request with response schema
            client_response = self._client.beta.chat.completions.parse(
                model=self._model,
                messages=messages,
                tools=tools,
                response_format=response_schema,
                temperature=self._temperature,
                max_tokens=self._max_tokens,
                top_p=self._top_p,
            )

            response_message = client_response.choices[0].message

            # Create the response object
            response = OpenAgentResponse(
                role=response_message.role,
                content=response_message.parsed,
                tool_calls=response_message.tool_calls,
                refusal=response_message.refusal,
                audio=response_message.audio,
            )
        
        response.usage = UsageResponse(
            prompt_tokens=client_response.usage.prompt_tokens,
            completion_tokens=client_response.usage.completion_tokens,
            total_tokens=client_response.usage.total_tokens,
            prompt_tokens_details=PromptTokensDetails(
                cached_tokens=client_response.usage.prompt_tokens_details.cached_tokens,
                audio_tokens=client_response.usage.prompt_tokens_details.audio_tokens,
            ),
            completion_tokens_details=CompletionTokensDetails(
                reasoning_tokens=client_response.usage.completion_tokens_details.reasoning_tokens,
                audio_tokens=client_response.usage.completion_tokens_details.audio_tokens,
                accepted_prediction_tokens=client_response.usage.completion_tokens_details.accepted_prediction_tokens,
                rejected_prediction_tokens=client_response.usage.completion_tokens_details.rejected_prediction_tokens,
            ),
        )
        
        return response
    
    def _handle_client_stream(self,
                              messages: List[Dict[str, str]],
                              tools: Optional[List[Dict[str, Any]]] = None,
                              response_schema: BaseModel = NOT_GIVEN,
                              temperature: Optional[float] = 0.3,
                              max_tokens: Optional[int] = None,
                              top_p: Optional[float] = None,
                              audio: Optional[bool] = False,
                              audio_format: Optional[str] = "pcm16",
                              audio_voice: Optional[Literal["alloy", "ash", "coral", "echo", "fable", "onyx", "nova", "sage", "shimmer"]] = "alloy",
                              **kwargs) -> Generator[OpenAgentStreamingResponse, None, None]:
        """
        Handle the client stream.

        Args:
            messages: The messages to send to the model.
            tools: The tools to use in the response.
            response_schema: The schema to use in the response. **(not implemented yet)**
            temperature: The temperature to use in the response.
            max_tokens: The max tokens to use in the response.
            top_p: The top p to use in the response.
            audio: Whether to include audio in the response.
            audio_format: The format of the audio.
            audio_voice: The voice to use for the audio.

        Returns:
            An Generator[OpenAgentStreamingResponse, None] object.
        """
        # TODO: THIS IS A PLACEHOLDER FOR NOW, WE NEED TO IMPLEMENT THE STREAMING FOR THE RESPONSE SCHEMA
        if response_schema is not NOT_GIVEN and isinstance(response_schema, BaseModel):
            raise ValueError("Response schema is not supported for streaming")

        temperature = kwargs.get("temperature", temperature)
        if temperature is None:
            temperature = self._temperature

        max_tokens = kwargs.get("max_tokens", max_tokens)
        if max_tokens is None:
            max_tokens = self._max_tokens

        top_p = kwargs.get("top_p", top_p)
        if top_p is None:
            top_p = self._top_p
        
        if tools == NOT_GIVEN:
            tools = self._llm_service.tools
        
        
        if tools is None:
            tools = self.tools
        
        if response_schema is NOT_GIVEN or isinstance(response_schema, NotGiven):
            client_stream = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                tools=tools,
                temperature=self._temperature,
                max_tokens=self._max_tokens,
                top_p=self._top_p,
                stream=True,
                stream_options={"include_usage": True},
                modalities=["text", "audio"] if audio else ["text"],
                audio={
                    "format": audio_format,
                    "voice": audio_voice,
                } if audio else None,
            )

            final_tool_calls = {}
            final_content = ""
            final_chunk = None
            
            for chunk in client_stream:
                final_chunk = chunk  # Store the last chunk for usage info
                
                # If the chunk is empty, skip it
                if not chunk.choices:
                    continue
                    
                # If the chunk has content, yield it
                if chunk.choices[0].delta.content is not None:
                    final_content += chunk.choices[0].delta.content
                    yield OpenAgentStreamingResponse(
                        role="assistant",
                        delta_content=chunk.choices[0].delta.content,
                        finish_reason=chunk.choices[0].finish_reason,
                    )

                # If the chunk has tool calls, add them to the final tool calls
                if chunk.choices[0].delta.tool_calls:
                    for tool_call in chunk.choices[0].delta.tool_calls:
                        index = tool_call.index

                        if index not in final_tool_calls:
                            final_tool_calls[index] = tool_call

                        final_tool_calls[index].function.arguments += tool_call.function.arguments
                
                # Handle audio chunks (if available)
                if chunk.choices[0].delta.model_dump().get("audio") is not None:
                    if chunk.choices[0].delta.model_dump().get("audio").get("data") is not None:
                        yield OpenAgentStreamingResponse(
                            role="assistant",
                            delta_audio=chunk.choices[0].delta.model_dump().get("audio").get("data"),
                            finish_reason=chunk.choices[0].finish_reason,
                        )
                    
                    if chunk.choices[0].delta.model_dump().get("audio").get("transcript") is not None:
                        final_content += chunk.choices[0].delta.model_dump().get("audio").get("transcript")
                        yield OpenAgentStreamingResponse(
                            role="assistant",
                            delta_content=chunk.choices[0].delta.model_dump().get("audio").get("transcript"),
                            finish_reason=chunk.choices[0].finish_reason,
                        )

            # After the stream is done, yield the final response with usage info if available
            if final_chunk and hasattr(final_chunk, 'usage'):
                yield OpenAgentStreamingResponse(
                    role="assistant",
                    content=final_content if final_content else None,
                    finish_reason="tool_calls" if final_tool_calls else "stop",
                    tool_calls=list(final_tool_calls.values()),
                    usage=UsageResponse(
                        prompt_tokens=final_chunk.usage.prompt_tokens,
                        completion_tokens=final_chunk.usage.completion_tokens,
                        total_tokens=final_chunk.usage.total_tokens,
                        prompt_tokens_details=PromptTokensDetails(
                            cached_tokens=final_chunk.usage.prompt_tokens_details.cached_tokens,
                            audio_tokens=final_chunk.usage.prompt_tokens_details.audio_tokens,
                        ),
                        completion_tokens_details=CompletionTokensDetails(
                            reasoning_tokens=final_chunk.usage.completion_tokens_details.reasoning_tokens,
                            audio_tokens=final_chunk.usage.completion_tokens_details.audio_tokens,
                            accepted_prediction_tokens=final_chunk.usage.completion_tokens_details.accepted_prediction_tokens,
                            rejected_prediction_tokens=final_chunk.usage.completion_tokens_details.rejected_prediction_tokens,
                        ),
                    ),
                )
            else:
                logger.warning("Final chunk or usage is None")
                
                yield OpenAgentStreamingResponse(
                    role="assistant",
                    content=final_content,
                    finish_reason="tool_calls" if final_tool_calls else "stop",
                    tool_calls=list(final_tool_calls.values()),
                )
        else:
            with self._client.beta.chat.completions.stream(
                model=self._model,
                messages=messages,
                tools=tools,
                temperature=self._temperature,
                max_tokens=self._max_tokens,
                top_p=self._top_p,
                stream=True,
                stream_options={"include_usage": True},
                response_format=response_schema,
            ) as stream:
                for event in stream:
                    if event.type == "content.delta":
                        if event.parsed is not None:
                            # Print the parsed data as JSON
                            print("content.delta parsed:", event.parsed)
                    elif event.type == "content.done":
                        print("content.done")
                    elif event.type == "error":
                        print("Error in stream:", event.error)

            final_completion = stream.get_final_completion()
            print("Final completion:", final_completion)
        
    def model_generate(self, 
                       messages: List[Dict[str, str]],
                       tools: Optional[List[Dict[str, Any]]] = None,
                       response_schema: Optional[BaseModel] = NOT_GIVEN,
                       temperature: Optional[float] = None,
                       max_tokens: Optional[int] = None,
                       top_p: Optional[float] = None,
                       audio: Optional[bool] = False,
                       audio_format: Optional[str] = "pcm16",
                       audio_voice: Optional[Literal["alloy", "ash", "coral", "echo", "fable", "onyx", "nova", "sage", "shimmer"]] = "alloy",
                       **kwargs) -> OpenAgentResponse:
        """
        Generate a response from the model.
        
        Args:
            messages: The messages to send to the model.
            tools: The tools to use in the response.
            response_schema: The schema to use in the response.
            temperature: The temperature to use in the response.
            max_tokens: The maximum number of tokens to use in the response.
            top_p: The top p to use in the response.
            audio: Whether to include audio in the response.
            audio_format: The format of the audio.
            audio_voice: The voice to use for the audio.
        
        Returns:
            An OpenAgentResponse object.

        Example:
        ```python
        from openagentkit.tools import duckduckgo_search_tool
        from openagentkit.modules.openai import OpenAILLMService

        llm_service = OpenAILLMService(client, tools=[duckduckgo_search_tool])
        response = llm_service.model_generate(messages=[{"role": "user", "content": "What is TECHVIFY?"}])
        ```
        """

        temperature = kwargs.get("temperature", temperature)
        if temperature is None:
            temperature = self._temperature

        max_tokens = kwargs.get("max_tokens", max_tokens)
        if max_tokens is None:
            max_tokens = self._max_tokens

        top_p = kwargs.get("top_p", top_p)
        if top_p is None:
            top_p = self._top_p

        if tools is None:
            tools = self.tools
            
        #logger.info(f"Tools: {tools}")

        # Handle the client request
        response = self._handle_client_request(
            messages=messages, 
            tools=tools,
            response_schema=response_schema,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            audio=audio,
            audio_format=audio_format,
            audio_voice=audio_voice,
        )
        
        if response.tool_calls:
            # Extract tool_calls arguments using the tool handler
            tool_calls = self._tool_handler.parse_tool_args(response)
            
            # Update the response with the parsed tool calls
            response.tool_calls = tool_calls
        
        return response
    
    def model_stream(self,
                     messages: List[Dict[str, str]],
                     tools: Optional[List[Dict[str, Any]]] = None,
                     response_schema: BaseModel = NOT_GIVEN,
                     temperature: Optional[float] = None,
                     max_tokens: Optional[int] = None,
                     top_p: Optional[float] = None,
                     audio: Optional[bool] = False,
                     audio_format: Optional[str] = "pcm16",
                     audio_voice: Optional[Literal["alloy", "ash", "coral", "echo", "fable", "onyx", "nova", "sage", "shimmer"]] = "alloy",
                     **kwargs) -> Generator[OpenAgentStreamingResponse, None, None]:
        """
        Generate a response from the model.

        Args:
            messages: The messages to send to the model.
            tools: The tools to use in the response.
            response_schema: The schema to use in the response. **(not implemented yet)**
            temperature: The temperature to use in the response.
            max_tokens: The max tokens to use in the response.
            top_p: The top p to use in the response.
            audio: Whether to include audio in the response.
            audio_format: The format of the audio.
            audio_voice: The voice to use for the audio.

        Returns:
            An AsyncGenerator[OpenAgentStreamingResponse, None] object.
        """
        # TODO: Handle the case with response schema (not working)
        if response_schema is not NOT_GIVEN and isinstance(response_schema, BaseModel):
            raise ValueError("Response schema is not supported for streaming")
        
        temperature = kwargs.get("temperature", temperature)
        if temperature is None:
            temperature = self._temperature

        max_tokens = kwargs.get("max_tokens", max_tokens)
        if max_tokens is None:
            max_tokens = self._max_tokens

        top_p = kwargs.get("top_p", top_p)
        if top_p is None:
            top_p = self._top_p

        if tools is None:
            tools = self.tools

        generator = self._handle_client_stream(
            messages=messages, 
            tools=tools,
            response_schema=response_schema,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            audio=audio,
            audio_format=audio_format,
            audio_voice=audio_voice,
        )

        for chunk in generator:
            if chunk.tool_calls:
                # Extract tool_calls arguments using the tool handler
                tool_calls = self._tool_handler.parse_tool_args(chunk)
                
                # Update the chunk with the parsed tool calls
                chunk.tool_calls = tool_calls
            yield chunk