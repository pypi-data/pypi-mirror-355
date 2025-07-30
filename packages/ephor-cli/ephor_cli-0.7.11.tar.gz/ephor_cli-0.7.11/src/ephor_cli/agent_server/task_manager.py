from typing import AsyncIterable
import asyncio
import logging
import traceback
import uuid
import json
from typing import Callable
from typing import Any

from google_a2a.common.server.task_manager import InMemoryTaskManager
from google_a2a.common.types import (
    JSONRPCResponse,
    Message,
    SendTaskRequest,
    SendTaskStreamingRequest,
    SendTaskStreamingResponse,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TaskSendParams,
    InternalError,
    TaskIdParams,
    CancelTaskRequest,
    CancelTaskResponse,
    Task,
)

from ephor_cli.agent_server.agent import Agent, get_tools
from ephor_cli.services import task_service, message_service
from ephor_cli.utils.message import (
    a2a_message_to_langchain_message,
    langchain_content_to_a2a_content,
)
from ephor_cli.types.task import TaskMetadata
from ephor_cli.types.agent import AgentInstance
from langchain_core.messages import BaseMessage
from langchain_core.messages.base import message_to_dict
from ephor_cli.utils.chunk_streamer import ChunkStreamer
from ephor_cli.utils.sanitize_message import sanitize_message
from ephor_cli.utils.attachments import process_attachments
from ephor_cli.services.s3 import S3Service

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - Line %(lineno)d - %(message)s"
)
logger.handlers[0].setFormatter(formatter)


class AgentTaskManager(InMemoryTaskManager):
    def __init__(self, agent_instance: AgentInstance, context: str):
        super().__init__()
        self.agent_instance = agent_instance
        self.chunk_streamer = ChunkStreamer()
        self.context = context

    async def _get_session_history(self, task: TaskMetadata) -> list[BaseMessage]:
        tasks = task_service.list_tasks(
            task.user_id,
            task.project_id,
            task.conversation_id,
            self.agent_instance.agent.name,
        )

        history = []
        for task in tasks:
            messages = message_service.list_messages(
                task.user_id, task.project_id, task.conversation_id, task.id
            )
            history.extend(messages)
        return history

    async def _get_task_history(self, task: TaskMetadata) -> list[BaseMessage]:
        messages = message_service.list_messages(
            task.user_id, task.project_id, task.conversation_id, task.id
        )
        return messages

    async def _add_new_messages(
        self,
        task: TaskMetadata,
        last_user_message: BaseMessage,
        new_messages: list[BaseMessage],
    ):
        last_message_id = last_user_message.id
        for new_message in new_messages:
            new_message.id = str(uuid.uuid4())
            new_message.additional_kwargs.update({"last_message_id": last_message_id})
            message_service.add_message(
                task.user_id,
                task.project_id,
                task.conversation_id,
                new_message,
                task.id,
            )
            last_message_id = new_message.id

    async def _run_streaming_agent(self, task: TaskMetadata, cleanup: Callable):
        
        # Track tool calls and their completion status
        tool_call_states = {}
        
        # Create a wrapper to detect when tools complete
        def send_tool_completion(tool_call_id: str, tool_name: str):
            """Send a completion event for a tool that has finished."""
            try:
                from langchain_core.messages import ToolMessage
                
                logger.info(f"✅ Sending completion event for tool: {tool_name} (id: {tool_call_id})")
                
                completion_metadata: dict[str, Any] = {
                    "type": "tool_progress",
                    "tool_call_id": tool_call_id,
                    "tool_name": tool_name,
                    "is_complete": True,
                    "message": "Tool execution completed"
                }
                
                completion_chunk = ToolMessage(
                    content="",
                    tool_call_id=tool_call_id,
                    additional_kwargs={"progress": completion_metadata},
                )
                
                # Wrap for A2A format
                completion_status_message = Message(
                    role="agent",
                    parts=[
                        {
                            "type": "text",
                            "text": json.dumps(message_to_dict(completion_chunk)),
                        }
                    ],
                    metadata=completion_metadata,
                )
                
                completion_task_status = TaskStatus(state=TaskState.WORKING, message=completion_status_message)
                
                completion_task_update_event = TaskStatusUpdateEvent(
                    id=task.id, status=completion_task_status
                )
                
                # Send completion event via SSE
                asyncio.create_task(
                    self.enqueue_events_for_sse(task.id, completion_task_update_event)
                )
                
            except Exception as e:
                logger.error(f"Error sending tool completion event: {e}")
        
        # Create progress callback that immediately streams progress updates
        def on_tool_progress(
            tool_call_id: str,
            tool_name: str,
            progress: float | None,
            total: float | None,
            message: str | None,
        ):
            """Handle progress updates (and completion) coming from tools.

            We forward percentage *and* an `is_complete` flag so the front-end
            doesn't have to infer completion from progress/total.
            """
            
            # Track this tool call
            if tool_call_id not in tool_call_states:
                tool_call_states[tool_call_id] = {
                    "name": tool_name,
                    "completed": False,
                    "has_total": total is not None
                }
                logger.info(f"🆕 Started tracking tool: {tool_name} (id: {tool_call_id})")

            # Calculate percentage only when we have both values
            percentage: float | None = None
            is_complete = False
            
            if progress is not None and total is not None and total != 0:
                percentage = progress / total * 100
                # Check if tool is complete based on progress
                if progress >= total:
                    is_complete = True
                    tool_call_states[tool_call_id]["completed"] = True

            logger.info(
                f"🚀 Tool progress: {tool_name} | progress={progress} | total={total} | pct={percentage} | msg={message} | complete={is_complete}"
            )

            try:
                from langchain_core.messages import ToolMessage

                progress_metadata: dict[str, Any] = {
                    "type": "tool_progress",
                    "tool_call_id": tool_call_id,
                    "tool_name": tool_name,
                    "is_complete": is_complete,
                }

                if percentage is not None:
                    progress_metadata["percentage"] = percentage
                if message is not None:
                    progress_metadata["message"] = message

                progress_chunk = ToolMessage(
                    content="", 
                    tool_call_id=tool_call_id,
                    additional_kwargs={"progress": progress_metadata},
                )

                # Wrap for A2A format
                progress_status_message = Message(
                    role="agent",
                    parts=[
                        {
                            "type": "text",
                            "text": json.dumps(message_to_dict(progress_chunk)),
                        }
                    ],
                    metadata=progress_metadata,
                )

                progress_task_status = TaskStatus(state=TaskState.WORKING, message=progress_status_message)

                progress_task_update_event = TaskStatusUpdateEvent(
                    id=task.id, status=progress_task_status
                )

                # send via SSE (schedule asynchronously)
                asyncio.create_task(
                    self.enqueue_events_for_sse(task.id, progress_task_update_event)
                )

            except Exception as e:
                logger.error(f"Error streaming progress update: {e}")
        
        # Monkey-patch the callback registration to detect tool completion
        from ephor_cli.mcp_adapters import tools as mcp_tools
        original_unregister = mcp_tools.unregister_progress_callback
        
        def patched_unregister(tool_call_id: str):
            # Call original unregister
            original_unregister(tool_call_id)
            
            # If we're tracking this tool and haven't sent completion yet
            if tool_call_id in tool_call_states:
                tool_state = tool_call_states[tool_call_id]
                # Only send completion if we haven't already (e.g., via progress >= total)
                if not tool_state["completed"]:
                    logger.info(f"🔔 Tool callback unregistered, sending completion: {tool_state['name']}")
                    send_tool_completion(tool_call_id, tool_state["name"])
                    tool_state["completed"] = True
        
        # Apply the patch
        mcp_tools.unregister_progress_callback = patched_unregister
        
        try:
            async with get_tools(
                self.agent_instance.agent.mcpServers, 
                self.agent_instance.hiveInstances,
                progress_callback=on_tool_progress
            ) as tools:
                message = a2a_message_to_langchain_message(task.status.message)
                session_history = await self._get_session_history(task)
                session_history = sanitize_message(session_history)
                task_history = await self._get_task_history(task)

                # Process attachments from task metadata
                if task.status.message.metadata:
                    attachments = task.status.message.metadata.get("attachments", [])
                    conversation_attachments = task.status.message.metadata.get("conversation_attachments", [])
                    
                    # Add attachments to message additional_kwargs
                    if attachments or conversation_attachments:
                        message.additional_kwargs["attachments"] = attachments
                        message.additional_kwargs["conversation_attachments"] = conversation_attachments
                        
                        # Process attachments using the same function as conversation server
                        s3_service = S3Service()
                        message = process_attachments(
                            message,
                            s3_service,
                            user_id=task.user_id,
                            project_id=task.project_id,
                            conversation_id=task.conversation_id
                        )

                # Use primary model if configured, otherwise default to Claude
                model = (
                    self.agent_instance.agent.primaryModel
                    if self.agent_instance.agent.primaryModel
                    else "claude-3-5-sonnet-20240620"
                )

                agent = Agent(
                    name=self.agent_instance.agent.name,
                    prompt=self.agent_instance.agent.prompt,
                    model=model,
                    fallback_models=self.agent_instance.agent.fallbackModels,
                    tools=tools,
                    initial_state=session_history,
                    context=self.context,
                )
                logger.info(f"Initiated agent: {agent}")
                if not message.id:
                    message.id = str(uuid.uuid4())
                if task_history:
                    message.additional_kwargs["last_message_id"] = task_history[-1].id
                message_service.add_message(
                    task.user_id, task.project_id, task.conversation_id, message, task.id
                )
                try:
                    logger.info(f"Updating task status to WORKING for task: {task.id}")
                    task_service.update_task(
                        task.user_id,
                        task.project_id,
                        task.conversation_id,
                        self.agent_instance.agent.name,
                        task.id,
                        {"status": TaskStatus(state=TaskState.WORKING)},
                    )
                    logger.info(f"Running streaming agent for task: {task.id}")

                    self.chunk_streamer.reset()
                    async for chunk in self.chunk_streamer.process(
                        agent.stream(message, task.conversation_id)
                    ):
                        # Stream the regular chunk
                        task_state = TaskState.WORKING
                        status_message = Message(
                            role="agent",
                            parts=[
                                {
                                    "type": "text",
                                    "text": json.dumps(message_to_dict(chunk)),
                                }
                            ],
                        )
                        task_status = TaskStatus(state=task_state, message=status_message)
                        task_update_event = TaskStatusUpdateEvent(
                            id=task.id, status=task_status
                        )

                        await self.enqueue_events_for_sse(task.id, task_update_event)

                    messages = self.chunk_streamer.messages
                    await self._add_new_messages(task, message, messages)

                    # Send final event
                    final_response: BaseMessage = messages[-1]
                    task_state = TaskState.COMPLETED
                    parts = langchain_content_to_a2a_content(final_response.content)
                    status_message = Message(role="agent", parts=parts)
                    task_status = TaskStatus(state=task_state, message=status_message)
                    task_service.update_task(
                        task.user_id,
                        task.project_id,
                        task.conversation_id,
                        self.agent_instance.agent.name,
                        task.id,
                        {"status": task_status},
                    )
                    task_update_event = TaskStatusUpdateEvent(
                        id=task.id, status=task_status, final=True
                    )
                    await self.enqueue_events_for_sse(task.id, task_update_event)
                    print(f"Successfully completed task: {task.id}")
                except Exception as e:
                    logger.error(f"An error occurred while streaming the response: {e}")
                    print(traceback.format_exc())
                    await self.enqueue_events_for_sse(
                        task.id,
                        InternalError(
                            message=f"An error occurred while streaming the response: {e}"
                        ),
                    )
                finally:
                    cleanup()
        finally:
            # Restore the original unregister function
            mcp_tools.unregister_progress_callback = original_unregister
            logger.info("Restored original unregister_progress_callback function")

    async def on_cancel_task(self, request: CancelTaskRequest):
        self.chunk_streamer.cancel()

        return CancelTaskResponse(
            result=Task(
                id=request.params.id, status=TaskStatus(state=TaskState.CANCELED)
            )
        )

    async def on_send_task_subscribe(
        self, request: SendTaskStreamingRequest, cleanup: Callable
    ) -> AsyncIterable[SendTaskStreamingResponse] | JSONRPCResponse:
        try:
            task_send_params: TaskSendParams = request.params
            logger.info(
                f"Received new task with subscription request: {task_send_params.model_dump_json(exclude_none=True)}"
            )
            task = task_service.create_task(
                task_id=task_send_params.id,
                user_id=task_send_params.metadata["user_id"],
                project_id=task_send_params.metadata["project_id"],
                conversation_id=task_send_params.metadata["conversation_id"],
                agent_name=self.agent_instance.agent.name,
                tool_call_id=task_send_params.metadata["tool_call_id"],
                status=TaskStatus(
                    state=TaskState.SUBMITTED,
                    message=task_send_params.message,
                ),
                metadata=task_send_params.metadata,
            )
            sse_event_queue = await self.setup_sse_consumer(task_send_params.id, False)

            asyncio.create_task(self._run_streaming_agent(task, cleanup))

            return self.dequeue_events_for_sse(
                request.id, task_send_params.id, sse_event_queue
            )
        except Exception as e:
            logger.error(f"Error in SSE stream: {e}")
            print(traceback.format_exc())
            return JSONRPCResponse(
                id=request.id,
                error=InternalError(
                    message="An error occurred while streaming the response"
                ),
            )

    async def on_resubscribe_to_task(
        self, request
    ) -> AsyncIterable[SendTaskStreamingResponse] | JSONRPCResponse:
        task_id_params: TaskIdParams = request.params
        try:
            sse_event_queue = await self.setup_sse_consumer(task_id_params.id, True)
            return self.dequeue_events_for_sse(
                request.id, task_id_params.id, sse_event_queue
            )
        except Exception as e:
            logger.error(f"Error while reconnecting to SSE stream: {e}")
            return JSONRPCResponse(
                id=request.id,
                error=InternalError(
                    message=f"An error occurred while reconnecting to stream: {e}"
                ),
            )

    def on_send_task(self, request: SendTaskRequest):
        raise NotImplementedError("on_send_task is not implemented")
