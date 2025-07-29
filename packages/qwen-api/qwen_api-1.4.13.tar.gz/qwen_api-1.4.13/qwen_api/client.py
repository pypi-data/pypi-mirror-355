import json
from typing import AsyncGenerator, Generator, List, Optional
import requests
import aiohttp
from sseclient import SSEClient
from pydantic import ValidationError
from .core.auth_manager import AuthManager
from .logger import setup_logger
from .core.types.chat import ChatResponse,  ChatResponseStream, ChatMessage, MessageRole
from .resources.completions import Completion
from .utils.promp_system import WEB_DEVELOPMENT_PROMPT
from .core.exceptions import QwenAPIError
from .core.types.response.function_tool import ToolCall, Function

class Qwen:
    def __init__(
        self,
        api_key: Optional[str] = None,
        cookie: Optional[str] = None,
        base_url: str = "https://chat.qwen.ai",
        timeout: int = 600,
        log_level: str = "INFO",
        save_logs: bool = False,
    ):
        self.chat = Completion(self)
        self.timeout = timeout
        self.auth = AuthManager(token=api_key, cookie=cookie)
        self.logger = setup_logger(
            log_level=log_level, save_logs=save_logs)
        self.base_url = base_url

    def _build_headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Authorization": self.auth.get_token(),
            "Cookie": self.auth.get_cookie(),
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            "Host": "chat.qwen.ai",
            "Origin": "https://chat.qwen.ai"
        }

    def _build_payload(
        self,
        messages: List[ChatMessage],
        temperature: float,
        model: str,
        max_tokens: Optional[int]
    ) -> dict:
        validated_messages = []

        for msg in messages:
            if isinstance(msg, dict):
                try:
                    validated_msg = ChatMessage(**msg)
                except ValidationError as e:
                    raise QwenAPIError(f"Error validating message: {e}")
            else:
                validated_msg = msg

            if validated_msg.role == "system":
                if validated_msg.web_development and WEB_DEVELOPMENT_PROMPT not in validated_msg.content:
                    updated_content = f"{validated_msg.content}\n\n{WEB_DEVELOPMENT_PROMPT}"
                    validated_msg = ChatMessage(**{
                        **validated_msg.model_dump(),
                        "content": updated_content
                    })

            validated_messages.append({
                "role": (
                    MessageRole.FUNCTION
                    if validated_msg.role == MessageRole.TOOL
                    else validated_msg.role if validated_msg.role == MessageRole.SYSTEM
                    else MessageRole.USER
                    ),
                "content": (
                    validated_msg.blocks[0].text if len(validated_msg.blocks) == 1 and validated_msg.blocks[0].block_type == "text"
                    else [
                        {"type": "text", "text": block.text} if block.block_type == "text"
                        else {"type": "image", "image": str(block.url)} if block.block_type == "image"
                        else {"type": block.block_type}
                        for block in validated_msg.blocks
                    ]
                ),
                "chat_type": "artifacts" if getattr(validated_msg, "web_development", False) else "search" if getattr(validated_msg, "web_search", False) else "t2t",
                "feature_config": {"thinking_enabled": getattr(validated_msg, "thinking", False),
                                   "thinking_budget": getattr(validated_msg, "thinking_budget", 0),
                                   "output_schema": getattr(validated_msg, "output_schema", None)},
                "extra": {}
            })

        return {
            "stream": True,
            "model": model,
            "incremental_output": True,
            "messages": validated_messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

    def _process_response(self, response: requests.Response) -> ChatResponse:
        client = SSEClient(response)
        message = {}
        text = ""
        for event in client.events():
            if event.data:
                try:
                    data = json.loads(event.data)
                    if data["choices"][0]["delta"].get("role") == "function":
                        message["extra"] = (
                            data["choices"][0]["delta"].get("extra"))
                    text += data["choices"][0]["delta"].get("content")
                except json.JSONDecodeError:
                    continue
        message["message"] = {"role": "assistant", "content": text}
        return ChatResponse(choices=message)
    
    def _process_response_tool(self, response: requests.Response) -> ChatResponse:
        client = SSEClient(response)
        message = {}
        text = ""
        for event in client.events():
            if event.data:
                try:
                    data = json.loads(event.data)
                    if data["choices"][0]["delta"].get("role") == "function":
                        message["extra"] = (
                            data["choices"][0]["delta"].get("extra"))
                    text += data["choices"][0]["delta"].get("content")
                except json.JSONDecodeError:
                    continue
        try:
            self.logger.debug(f"text: {text}")
            parse_json = json.loads(text)
            if isinstance(parse_json["arguments"], str):
                parse_arguments = json.loads(parse_json["arguments"])
            else:
                parse_arguments = parse_json["arguments"]
            self.logger.debug(f"parse_json: {parse_json}")
            self.logger.debug(f"arguments: {parse_arguments}")
            function = Function(name=parse_json["name"], arguments=parse_arguments)
            message["message"] = {"role": "assistant", "content": '', 'tool_calls': [ToolCall(function=function)]}
            return ChatResponse(choices=message)
        except json.JSONDecodeError as e:
            return QwenAPIError(f"Error decoding JSON response: {e}")

    async def _process_aresponse(self, response: aiohttp.ClientResponse, session: aiohttp.ClientSession) -> ChatResponse:
        try:
            message = {}
            text = ""
            async for line in response.content:
                if line.startswith(b'data:'):
                    try:
                        data = json.loads(line[5:].decode())
                        if data["choices"][0]["delta"].get("role") == "function":
                            message["extra"] = (
                                data["choices"][0]["delta"].get("extra"))
                        text += data["choices"][0]["delta"].get("content")
                    except json.JSONDecodeError:
                        continue
            message["message"] = {"role": "assistant", "content": text}
            return ChatResponse(choices=message)
        except aiohttp.ClientError as e:
            self.logger.error(f"Client error: {e}")
            raise

        finally:
            await session.close()

    async def _process_aresponse_tool(self, response: aiohttp.ClientResponse, session: aiohttp.ClientSession) -> ChatResponse:
        try:
            message = {}
            text = ""
            async for line in response.content:
                if line.startswith(b'data:'):
                    try:
                        data = json.loads(line[5:].decode())
                        if data["choices"][0]["delta"].get("role") == "function":
                            message["extra"] = (
                                data["choices"][0]["delta"].get("extra"))
                        text += data["choices"][0]["delta"].get("content")
                    except json.JSONDecodeError:
                        continue
            try:
                self.logger.debug(f"text: {text}")
                parse_json = json.loads(text)
                if isinstance(parse_json["arguments"], str):
                    parse_arguments = json.loads(parse_json["arguments"])
                else:
                    parse_arguments = parse_json["arguments"]
                self.logger.debug(f"parse_json: {parse_json}")
                self.logger.debug(f"arguments: {parse_arguments}")
                function = Function(name=parse_json["name"], arguments=parse_arguments)
                message["message"] = {"role": "assistant", "content": '', 'tool_calls': [ToolCall(function=function)]}
                return ChatResponse(choices=message)
            except json.JSONDecodeError as e:
                self.logger.error(f"Error decoding JSON response: {e}")
                return QwenAPIError(f"Error decoding JSON response: {e}")
            
        except aiohttp.ClientError as e:
            self.logger.error(f"Client error: {e}")
            raise

        finally:
            await session.close()

    def _process_stream(self, response: requests.Response) -> Generator[ChatResponseStream, None, None]:
        client = SSEClient(response)
        content = ''
        for event in client.events():
            if event.data:
                try:
                    data = json.loads(event.data)
                    content += data["choices"][0]["delta"].get("content")
                    yield ChatResponseStream(
                        **data,
                        message=ChatMessage(
                            role=data["choices"][0]["delta"].get("role"),
                            content=content
                        )
                    )
                except json.JSONDecodeError:
                    continue

    async def _process_astream(self, response: aiohttp.ClientResponse, session: aiohttp.ClientSession) -> AsyncGenerator[ChatResponseStream, None]:
        try:
            content = ''
            async for line in response.content:
                if line.startswith(b'data:'):
                    try:
                        data = json.loads(line[5:].decode())
                        content += data["choices"][0]["delta"].get("content")
                        yield ChatResponseStream(
                            **data,
                            message=ChatMessage(
                                role=data["choices"][0]["delta"].get("role"),
                                content=content
                            )
                        )
                    except json.JSONDecodeError:
                        continue
        except aiohttp.ClientError as e:
            self.logger.error(f"Client error: {e}")
            raise

        finally:
            self.logger.debug(f"Closing session")
            await session.close()
