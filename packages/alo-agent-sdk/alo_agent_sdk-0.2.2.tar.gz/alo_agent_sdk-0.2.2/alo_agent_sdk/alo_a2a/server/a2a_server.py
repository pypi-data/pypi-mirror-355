"""
Enhanced A2A server with protocol support using FastAPI.
"""

import uuid
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any, List, Union, Generator, Iterator, Callable, AsyncGenerator

from fastapi import FastAPI, Request, HTTPException, Body
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from ..models.agent import AgentCard, AgentSkill
from ..models.task import Task, TaskStatus, TaskState
from ..models.message import Message, MessageRole
from ..models.conversation import Conversation
from ..models.content import TextContent, ErrorContent, FunctionResponseContent, FunctionCallContent
from .base import BaseA2AServer
from ..exceptions import A2AConfigurationError, A2AStreamingError

# Pydantic models for request/response bodies (can be expanded)
class GoogleA2AMessagePart(BaseModel):
    type: str
    text: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    name: Optional[str] = None
    response: Optional[Dict[str, Any]] = None
    parameters: Optional[List[Dict[str, Any]]] = None
    message: Optional[str] = None


class GoogleA2AMessage(BaseModel):
    role: str
    parts: List[GoogleA2AMessagePart]
    id: Optional[str] = None
    conversation_id: Optional[str] = None
    parent_message_id: Optional[str] = None
    timestamp: Optional[str] = None


class PythonA2AMessageContent(BaseModel):
    type: str
    text: Optional[str] = None
    message: Optional[str] = None # For error content
    name: Optional[str] = None # For function call/response
    parameters: Optional[List[Dict[str, Any]]] = None # For function call
    response: Optional[Dict[str, Any]] = None # For function response

class PythonA2AMessage(BaseModel):
    content: PythonA2AMessageContent
    role: str
    message_id: Optional[str] = None
    conversation_id: Optional[str] = None
    parent_message_id: Optional[str] = None
    timestamp: Optional[str] = None


class TaskRequestData(BaseModel):
    id: Optional[str] = None
    sessionId: Optional[str] = None
    message: Optional[Union[GoogleA2AMessage, PythonA2AMessage, Dict[str, Any]]] = None # Allow dict for flexibility
    status: Optional[Dict[str, Any]] = None # For task updates, not typically in send
    # Allow any other fields for flexibility with different formats
    class Config:
        extra = "allow"

class TaskResponseData(TaskRequestData): # Response can echo request fields
    artifacts: Optional[List[Dict[str, Any]]] = None
    status: Dict[str, Any] # Status is mandatory in response

class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)
    id: Union[str, int, None] = 1


class A2AServer(BaseA2AServer):
    """
    Enhanced A2A server with protocol support, refactored for FastAPI.
    """

    def __init__(self, agent_card=None, message_handler=None, google_a2a_compatible=True, **kwargs):
        if agent_card:
            self.agent_card = agent_card
        else:
            self.agent_card = self._create_default_agent_card(**kwargs)

        self.message_handler = message_handler
        self._handle_message_impl = message_handler
        self.tasks: Dict[str, Task] = {}
        self.streaming_subscriptions: Dict[str, Any] = {} # Placeholder for actual subscription management
        self._use_google_a2a = google_a2a_compatible

        if not hasattr(self.agent_card, 'capabilities'):
            self.agent_card.capabilities = {}
        if isinstance(self.agent_card.capabilities, dict):
            self.agent_card.capabilities["google_a2a_compatible"] = google_a2a_compatible
            self.agent_card.capabilities["parts_array_format"] = google_a2a_compatible
            self.agent_card.capabilities["streaming"] = True

    def _create_default_agent_card(self, **kwargs):
        name = kwargs.get("name", getattr(self.__class__, "name", "A2A Agent"))
        description = kwargs.get("description", getattr(self.__class__, "description", "A2A-compatible agent"))
        url = kwargs.get("url", None)
        version = kwargs.get("version", getattr(self.__class__, "version", "1.0.0"))
        google_a2a_compatible = kwargs.get("google_a2a_compatible", True)
        capabilities = kwargs.get("capabilities", {
            "streaming": True,
            "pushNotifications": False,
            "stateTransitionHistory": False,
            "google_a2a_compatible": google_a2a_compatible,
            "parts_array_format": google_a2a_compatible
        })
        return AgentCard(
            name=name, description=description, url=url, version=version,
            authentication=kwargs.get("authentication", getattr(self.__class__, "authentication", None)),
            capabilities=capabilities,
            default_input_modes=kwargs.get("input_modes", ["text/plain"]),
            default_output_modes=kwargs.get("output_modes", ["text/plain"])
        )

    def handle_message(self, message: Message) -> Message:
        if hasattr(self, 'message_handler') and self.message_handler:
            return self.message_handler(message)
        if message.content.type == "text":
            return Message(
                content=TextContent(text=message.content.text),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
        elif message.content.type == "function_call":
            return Message(
                content=TextContent(
                    text=f"Received function call '{message.content.name}' with parameters, but no handler is defined."
                ),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
        else:
            return Message(
                content=TextContent(text="Received a non-text message"),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )

    def handle_task(self, task: Task) -> Task:
        message_data = task.message or {}
        has_message_handler = hasattr(self, 'handle_message') and self.handle_message != A2AServer.handle_message

        if has_message_handler or (hasattr(self, "_handle_message_impl") and self._handle_message_impl):
            try:
                message = None
                if isinstance(message_data, dict):
                    if "parts" in message_data and "role" in message_data and "content" not in message_data:
                        try:
                            message = Message.from_google_a2a(message_data)
                        except Exception: pass
                    if message is None:
                        try:
                            message = Message.from_dict(message_data)
                        except Exception:
                            text = ""
                            if "content" in message_data and isinstance(message_data["content"], dict):
                                content = message_data["content"]
                                text = content.get("text", content.get("message", ""))
                            elif "parts" in message_data:
                                for part in message_data.get("parts", []):
                                    if isinstance(part, dict) and part.get("type") == "text" and "text" in part:
                                        text = part["text"]
                                        break
                            message = Message(content=TextContent(text=text), role=MessageRole.USER)
                elif isinstance(message_data, Message):
                    message = message_data
                else: # Fallback for unexpected message_data type
                     message = Message(content=TextContent(text=str(message_data)), role=MessageRole.USER)


                response_message = self.handle_message(message) if has_message_handler else self._handle_message_impl(message)

                content_type = getattr(response_message.content, "type", None)
                parts = []
                if content_type == "text":
                    parts = [{"type": "text", "text": response_message.content.text}]
                elif content_type == "function_response":
                    parts = [{"type": "function_response", "name": response_message.content.name, "response": response_message.content.response}]
                elif content_type == "function_call":
                    params = [{"name": p.name, "value": p.value} for p in response_message.content.parameters]
                    parts = [{"type": "function_call", "name": response_message.content.name, "parameters": params}]
                elif content_type == "error":
                    parts = [{"type": "error", "message": response_message.content.message}]
                else:
                    parts = [{"type": "text", "text": str(response_message.content)}]
                task.artifacts = [{"parts": parts}]
            except Exception as e:
                task.artifacts = [{"parts": [{"type": "error", "message": f"Error in message handler: {str(e)}"}]}]
        else: # Basic echo if no handler
            content = message_data.get("content", {})
            text_to_echo = ""
            if isinstance(content, dict):
                content_type = content.get("type")
                if content_type == "text": text_to_echo = content.get("text", "")
                elif content_type == "function_call": text_to_echo = f"Received function call '{content.get('name', '')}' without handler"
                else: text_to_echo = f"Received message of type '{content_type}'"
            elif isinstance(message_data, dict) and "parts" in message_data: # Google A2A
                 for part in message_data.get("parts", []):
                    if isinstance(part, dict) and part.get("type") == "text" and "text" in part:
                        text_to_echo = part["text"]
                        break
            else:
                text_to_echo = str(content)
            task.artifacts = [{"parts": [{"type": "text", "text": text_to_echo}]}]

        task.status = TaskStatus(state=TaskState.COMPLETED)
        return task

    def setup_routes(self, app: FastAPI):
        async def _parse_request_data(request: Request) -> Dict[str, Any]:
            try:
                return await request.json()
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON payload")

        def _determine_google_format(data: Dict[str, Any], context: str = "message") -> bool:
            if context == "task" and "message" in data:
                msg_data = data["message"]
            elif context == "conversation" and "messages" in data and data["messages"]:
                msg_data = data["messages"][0]
            else: # context == "message"
                msg_data = data
            
            return isinstance(msg_data, dict) and "parts" in msg_data and "role" in msg_data and "content" not in msg_data


        @app.get("/")
        async def a2a_root_get():
            return {
                "name": self.agent_card.name,
                "description": self.agent_card.description,
                "agent_card_url": "/agent.json",
                "protocol": "a2a",
                "capabilities": self.agent_card.capabilities
            }

        @app.post("/")
        async def a2a_root_post(request: Request):
            data = await _parse_request_data(request)
            try:
                is_google_format_task = _determine_google_format(data, "task")
                is_google_format_conv = _determine_google_format(data, "conversation")
                is_google_format_msg = _determine_google_format(data, "message")

                if "id" in data and ("message" in data or "status" in data): # Task
                    return await self._handle_task_request_internal(data, is_google_format_task)
                if "messages" in data: # Conversation
                    return await self._handle_conversation_request_internal(data, is_google_format_conv)
                # Single message
                return await self._handle_message_request_internal(data, is_google_format_msg)
            except HTTPException:
                raise 
            except Exception as e:
                error_msg = f"Error processing request: {str(e)}"
                if self._use_google_a2a:
                    return JSONResponse(status_code=500, content={
                        "role": "agent", "parts": [{"type": "data", "data": {"error": error_msg}}]
                    })
                else:
                    return JSONResponse(status_code=500, content={
                        "content": {"type": "error", "message": error_msg}, "role": "system"
                    })

        @app.get("/a2a")
        async def a2a_index():
            return await a2a_root_get()

        @app.post("/a2a")
        async def a2a_post(request: Request):
            return await a2a_root_post(request)

        @app.get("/a2a/agent.json")
        async def a2a_agent_card():
            return self.agent_card.to_dict()

        @app.get("/agent.json")
        async def agent_card_root():
            return self.agent_card.to_dict()
        
        async def _process_task_send(params: Dict[str, Any], rpc_id: Optional[Union[str, int]] = None):
            is_google_format = _determine_google_format(params, "task")
            response_data = await self._handle_task_request_internal(params, is_google_format)
            
            # FastAPI returns JSONResponse directly, so extract content if it's one
            content_to_return = response_data.body if isinstance(response_data, JSONResponse) else response_data
            try: # Try to parse if it's bytes
                if isinstance(content_to_return, bytes):
                    content_to_return = json.loads(content_to_return.decode())
            except: pass


            if rpc_id is not None:
                return {"jsonrpc": "2.0", "id": rpc_id, "result": content_to_return}
            return content_to_return

        @app.post("/a2a/tasks/send")
        async def a2a_tasks_send(request_data: Union[JsonRpcRequest, TaskRequestData] = Body(...)):
            try:
                if isinstance(request_data, JsonRpcRequest): # JSON-RPC
                    return await _process_task_send(request_data.params, request_data.id)
                else: # Direct task submission
                    # FastAPI automatically parses to TaskRequestData if it matches
                    # If not, it might be a raw dict, convert for consistency
                    data_dict = request_data if isinstance(request_data, dict) else request_data.model_dump(exclude_none=True)
                    return await _process_task_send(data_dict)
            except HTTPException:
                raise
            except Exception as e:
                rpc_id = request_data.id if isinstance(request_data, JsonRpcRequest) else None
                error_payload = {"code": -32603, "message": f"Internal error: {str(e)}"}
                if rpc_id is not None:
                    return JSONResponse(status_code=500, content={"jsonrpc": "2.0", "id": rpc_id, "error": error_payload})
                else:
                    if self._use_google_a2a:
                        return JSONResponse(status_code=500, content={"role": "agent", "parts": [{"type": "data", "data": {"error": f"Error: {str(e)}"}}]})
                    else:
                        return JSONResponse(status_code=500, content={"content": {"type": "error", "message": f"Error: {str(e)}"}, "role": "system"})


        @app.post("/tasks/send")
        async def tasks_send_root(request_data: Union[JsonRpcRequest, TaskRequestData] = Body(...)):
            return await a2a_tasks_send(request_data)

        async def _process_task_get_or_cancel(params: Dict[str, Any], rpc_id: Optional[Union[str, int]], action: str):
            task_id = params.get("id")
            if not task_id:
                raise HTTPException(status_code=400, detail=f"Task ID ('id') missing in params for {action}")

            task = self.tasks.get(task_id)
            if not task:
                error_payload = {"code": -32000, "message": f"Task not found: {task_id}"}
                if rpc_id is not None:
                    return JSONResponse(status_code=404, content={"jsonrpc": "2.0", "id": rpc_id, "error": error_payload})
                raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

            if action == "cancel":
                task.status = TaskStatus(state=TaskState.CANCELED)
            
            task_dict = task.to_google_a2a() if self._use_google_a2a else task.to_dict()
            if rpc_id is not None:
                return {"jsonrpc": "2.0", "id": rpc_id, "result": task_dict}
            return task_dict

        @app.post("/a2a/tasks/get")
        async def a2a_tasks_get(request_data: Union[JsonRpcRequest, Dict[str, Any]] = Body(...)):
            try:
                if isinstance(request_data, JsonRpcRequest):
                    return await _process_task_get_or_cancel(request_data.params, request_data.id, "get")
                else: # Direct request
                    data_dict = request_data if isinstance(request_data, dict) else request_data.model_dump(exclude_none=True)
                    return await _process_task_get_or_cancel(data_dict, None, "get")
            except HTTPException:
                raise
            except Exception as e:
                rpc_id = request_data.id if isinstance(request_data, JsonRpcRequest) else None
                error_payload = {"code": -32603, "message": f"Internal error: {str(e)}"}
                if rpc_id is not None:
                    return JSONResponse(status_code=500, content={"jsonrpc": "2.0", "id": rpc_id, "error": error_payload})
                raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


        @app.post("/tasks/get")
        async def tasks_get_root(request_data: Union[JsonRpcRequest, Dict[str, Any]] = Body(...)):
            return await a2a_tasks_get(request_data)

        @app.post("/a2a/tasks/cancel")
        async def a2a_tasks_cancel(request_data: Union[JsonRpcRequest, Dict[str, Any]] = Body(...)):
            try:
                if isinstance(request_data, JsonRpcRequest):
                    return await _process_task_get_or_cancel(request_data.params, request_data.id, "cancel")
                else: # Direct request
                    data_dict = request_data if isinstance(request_data, dict) else request_data.model_dump(exclude_none=True)
                    return await _process_task_get_or_cancel(data_dict, None, "cancel")
            except HTTPException:
                raise
            except Exception as e:
                rpc_id = request_data.id if isinstance(request_data, JsonRpcRequest) else None
                error_payload = {"code": -32603, "message": f"Internal error: {str(e)}"}
                if rpc_id is not None:
                    return JSONResponse(status_code=500, content={"jsonrpc": "2.0", "id": rpc_id, "error": error_payload})
                raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

        @app.post("/tasks/cancel")
        async def tasks_cancel_root(request_data: Union[JsonRpcRequest, Dict[str, Any]] = Body(...)):
            return await a2a_tasks_cancel(request_data)

        @app.post("/a2a/tasks/stream")
        async def a2a_tasks_stream(request_data: JsonRpcRequest = Body(...)):
            try:
                method = request_data.method
                params = request_data.params
                rpc_id = request_data.id

                if method == "tasks/sendSubscribe":
                    return await self._handle_tasks_send_subscribe_internal(params, rpc_id)
                elif method == "tasks/resubscribe":
                    return await self._handle_tasks_resubscribe_internal(params, rpc_id)
                else:
                    return JSONResponse(status_code=404, content={
                        "jsonrpc": "2.0", "id": rpc_id,
                        "error": {"code": -32601, "message": f"Method '{method}' not found"}
                    })
            except Exception as e:
                rpc_id = request_data.id if hasattr(request_data, 'id') else None
                return JSONResponse(status_code=500, content={
                    "jsonrpc": "2.0", "id": rpc_id,
                    "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
                })
        
        @app.post("/tasks/stream")
        async def tasks_stream_root(request_data: JsonRpcRequest = Body(...)):
            return await a2a_tasks_stream(request_data)


    async def _handle_message_request_internal(self, data: Dict[str, Any], is_google_format: bool):
        try:
            message = Message.from_google_a2a(data) if is_google_format else Message.from_dict(data)
            response = self.handle_message(message)
            return response.to_google_a2a() if is_google_format or self._use_google_a2a else response.to_dict()
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            status_code = 500
            if is_google_format or self._use_google_a2a:
                content = {"role": "agent", "parts": [{"type": "data", "data": {"error": error_msg}}]}
            else:
                content = {"content": {"type": "error", "message": error_msg}, "role": "system"}
            raise HTTPException(status_code=status_code, detail=content)


    async def _handle_conversation_request_internal(self, data: Dict[str, Any], is_google_format: bool):
        try:
            conv = Conversation.from_google_a2a(data) if is_google_format else Conversation.from_dict(data)
            response = self.handle_conversation(conv) # Assuming handle_conversation exists
            return response.to_google_a2a() if is_google_format or self._use_google_a2a else response.to_dict()
        except Exception as e:
            error_msg = f"Error processing conversation: {str(e)}"
            status_code = 500
            conv_id = data.get("conversation_id", "")
            if is_google_format or self._use_google_a2a:
                content = {"conversation_id": conv_id, "messages": [{"role": "agent", "parts": [{"type": "data", "data": {"error": error_msg}}]}]}
            else:
                content = {"conversation_id": conv_id, "messages": [{"content": {"type": "error", "message": error_msg}, "role": "system"}]}
            raise HTTPException(status_code=status_code, detail=content)

    async def _handle_task_request_internal(self, data: Dict[str, Any], is_google_format: bool):
        try:
            task_id = data.get("id", str(uuid.uuid4())) # Ensure task_id is generated if not present
            data_with_id = {**data, "id": task_id} # Ensure data used for Task creation has an ID

            task = Task.from_google_a2a(data_with_id) if is_google_format else Task.from_dict(data_with_id)
            
            result_task = self.handle_task(task)
            self.tasks[result_task.id] = result_task
            return result_task.to_google_a2a() if is_google_format or self._use_google_a2a else result_task.to_dict()
        except Exception as e:
            error_msg = f"Error processing task: {str(e)}"
            error_response_content = {
                "id": data.get("id", ""), "sessionId": data.get("sessionId", ""),
                "status": {"state": "failed", "message": {"error": error_msg}, "timestamp": datetime.now().isoformat()}
            }
            # Do not raise HTTPException here if the protocol expects a 200 OK with error in body for tasks
            # However, typical REST APIs would use HTTP status codes. Assuming 500 for now.
            return JSONResponse(status_code=500, content=error_response_content)


    def get_metadata(self) -> Dict[str, Any]:
        metadata = super().get_metadata()
        metadata.update({
            "agent_type": "A2AServer", "capabilities": ["text"], "has_agent_card": True,
            "agent_name": self.agent_card.name, "agent_version": self.agent_card.version,
            "google_a2a_compatible": self._use_google_a2a
        })
        return metadata

    def use_google_a2a_format(self, use_google_format: bool = True):
        self._use_google_a2a = use_google_format
        if isinstance(self.agent_card.capabilities, dict):
            self.agent_card.capabilities["google_a2a_compatible"] = use_google_format
            self.agent_card.capabilities["parts_array_format"] = use_google_format

    def is_using_google_a2a_format(self) -> bool:
        return self._use_google_a2a

    async def _generate_sse_stream_send_subscribe(self, task: Task, rpc_id: Union[str, int]) -> AsyncGenerator[str, None]:
        initial_task_dict = task.to_dict() if not self._use_google_a2a else task.to_google_a2a()
        yield f"event: update\nid: {rpc_id}\ndata: {json.dumps(initial_task_dict)}\n\n"
        
        result_task = None
        try:
            result_task = self.handle_task(task) # This should be synchronous for now
        except Exception as e:
            task.status = TaskStatus(state=TaskState.FAILED, message={"error": str(e)})
            result_task = task
        
        self.tasks[result_task.id] = result_task
        complete_task_dict = result_task.to_dict() if not self._use_google_a2a else result_task.to_google_a2a()
        yield f"event: complete\nid: {rpc_id}\ndata: {json.dumps(complete_task_dict)}\n\n"

    async def _handle_tasks_send_subscribe_internal(self, params: Dict[str, Any], rpc_id: Union[str, int]):
        task_id = params.get("id", str(uuid.uuid4()))
        params_with_id = {**params, "id": task_id}
        task = Task.from_dict(params_with_id) # Assuming standard format for sendSubscribe params

        return StreamingResponse(
            self._generate_sse_stream_send_subscribe(task, rpc_id),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"}
        )

    async def _generate_sse_stream_resubscribe(self, task: Task, rpc_id: Union[str, int]) -> AsyncGenerator[str, None]:
        current_task_dict = task.to_dict() if not self._use_google_a2a else task.to_google_a2a()
        yield f"event: update\nid: {rpc_id}\ndata: {json.dumps(current_task_dict)}\n\n"

        if task.status.state not in [TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELED]:
            # In a real async implementation, this might await further updates.
            # For this synchronous handle_task, we assume it's mostly done.
            # If handle_task were async, this would be different.
            await asyncio.sleep(0.1) # Simulate a brief moment for any final processing if needed
            if task.status.state not in [TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELED]:
                 # If still not final, mark as completed for this example stream.
                 # A real system would have a mechanism to push further updates.
                task.status = TaskStatus(state=TaskState.COMPLETED)
        
        complete_task_dict = task.to_dict() if not self._use_google_a2a else task.to_google_a2a()
        yield f"event: complete\nid: {rpc_id}\ndata: {json.dumps(complete_task_dict)}\n\n"


    async def _handle_tasks_resubscribe_internal(self, params: Dict[str, Any], rpc_id: Union[str, int]):
        task_id = params.get("id")
        if not task_id:
            raise HTTPException(status_code=400, detail={"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32602, "message": "Missing required parameter: id"}})
        
        task = self.tasks.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail={"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32000, "message": f"Task not found: {task_id}"}})

        return StreamingResponse(
            self._generate_sse_stream_resubscribe(task, rpc_id),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"}
        )

# Example of how to integrate with a FastAPI app
# This would typically be done in the agent's main.py or similar
# from fastapi import FastAPI
# app = FastAPI()
# a2a_server = A2AServer()
# a2a_server.setup_routes(app)
#
# To run: uvicorn main:app --reload (if this code is in main.py)

# Need to import asyncio for sleep in streaming example
import asyncio
