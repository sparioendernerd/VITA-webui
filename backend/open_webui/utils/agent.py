import json
from typing import Any, Callable, Dict, List, Optional, Tuple

from fastapi import Request
from starlette.responses import Response

from open_webui.models.users import UserModel
from open_webui.socket.main import get_event_call, get_event_emitter
from open_webui.utils.chat import generate_chat_completion


ToolResultHandler = Callable[
    [
        Request,
        str,
        Any,
        str,
        bool,
        Dict[str, Any],
        Optional[UserModel],
    ],
    Tuple[str | None, List[Dict[str, Any]], List[Any]],
]


async def _response_to_dict(response: Response | Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(response, Response):
        body = response.body
        if isinstance(body, bytes):
            body = body.decode("utf-8", "replace")
        if isinstance(body, (str, bytes)):
            return json.loads(body)
        if isinstance(body, dict):
            return body
        raise ValueError("Unsupported response body type for agent execution")

    if isinstance(response, dict):
        return response

    raise ValueError("Unsupported response type for agent execution")


def _sanitize_arguments(raw_args: Any) -> Dict[str, Any]:
    if isinstance(raw_args, dict):
        return raw_args

    if isinstance(raw_args, str):
        raw_args = raw_args.strip()
        if not raw_args:
            return {}
        try:
            return json.loads(raw_args)
        except json.JSONDecodeError:
            return {}

    return {}


async def run_agent(
    request: Request,
    form_data: Dict[str, Any],
    metadata: Dict[str, Any],
    user: Optional[UserModel],
    tools: Dict[str, Dict[str, Any]],
    tool_result_handler: ToolResultHandler,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Execute an agent loop until the model returns a final response."""

    event_emitter = get_event_emitter(metadata)
    event_caller = get_event_call(metadata)

    agent_settings = metadata.get("agent_session", {})
    max_iterations = agent_settings.get("max_steps", 8)

    messages = list(form_data.get("messages", []))
    original_stream = form_data.get("stream", False)

    sources: List[Dict[str, Any]] = []
    skip_files = False

    if event_emitter:
        await event_emitter(
            {
                "type": "status",
                "data": {
                    "action": "agent_start",
                    "description": "Agent execution started",
                    "done": False,
                },
            }
        )

    for iteration in range(1, max_iterations + 1):
        payload = {
            **form_data,
            "stream": False,
            "messages": messages,
        }

        response = await generate_chat_completion(request, form_data=payload, user=user)
        response_data = await _response_to_dict(response)

        choices = response_data.get("choices", [])
        if not choices:
            raise RuntimeError("Agent model did not return any choices")

        assistant_message = choices[0].get("message", {})
        messages.append(assistant_message)

        tool_calls = assistant_message.get("tool_calls", [])
        if not tool_calls:
            # Final response from the agent
            if original_stream:
                # replay the final response via the event emitter to emulate streaming completion
                if event_emitter:
                    await event_emitter(
                        {
                            "type": "chat:completion",
                            "data": response_data,
                        }
                    )

            if event_emitter:
                await event_emitter(
                    {
                        "type": "status",
                        "data": {
                            "action": "agent_complete",
                            "description": "Agent execution completed",
                            "done": True,
                        },
                    }
                )

            form_data["messages"] = messages
            return response_data, ([{"sources": sources}] if sources else [])

        if event_emitter:
            await event_emitter(
                {
                    "type": "status",
                    "data": {
                        "action": "agent_step",
                        "description": f"Executing tools for step {iteration}",
                        "step": iteration,
                        "done": False,
                    },
                }
            )

        for tool_call in tool_calls:
            tool_call_id = tool_call.get("id")
            name = tool_call.get("function", {}).get("name")
            if not name or name not in tools:
                continue

            tool = tools[name]
            tool_type = tool.get("type", "")
            direct_tool = tool.get("direct", False)

            raw_args = tool_call.get("function", {}).get("arguments")
            parsed_args = _sanitize_arguments(raw_args)

            spec = tool.get("spec", {})
            allowed_params = (
                spec.get("parameters", {})
                .get("properties", {})
                .keys()
            )
            parsed_args = {k: v for k, v in parsed_args.items() if k in allowed_params}
            tool_call.setdefault("function", {})["arguments"] = json.dumps(parsed_args)

            if event_emitter:
                await event_emitter(
                    {
                        "type": "status",
                        "data": {
                            "action": "agent_tool_call",
                            "tool": name,
                            "params": parsed_args,
                            "done": False,
                        },
                    }
                )

            try:
                if direct_tool:
                    tool_result = await event_caller(
                        {
                            "type": "execute:tool",
                            "data": {
                                "id": tool_call_id,
                                "name": name,
                                "params": parsed_args,
                                "server": tool.get("server", {}),
                                "session_id": metadata.get("session_id"),
                            },
                        }
                    )
                else:
                    tool_callable = tool["callable"]
                    tool_result = await tool_callable(**parsed_args)
            except Exception as exc:  # noqa: BLE001
                tool_result = str(exc)

            tool_output, tool_files, tool_embeds = tool_result_handler(
                request,
                name,
                tool_result,
                tool_type,
                direct_tool,
                metadata,
                user,
            )

            if event_emitter:
                if tool_files:
                    await event_emitter(
                        {
                            "type": "files",
                            "data": {"files": tool_files},
                        }
                    )

                if tool_embeds:
                    await event_emitter(
                        {
                            "type": "embeds",
                            "data": {"embeds": tool_embeds},
                        }
                    )

                await event_emitter(
                    {
                        "type": "status",
                        "data": {
                            "action": "agent_tool_complete",
                            "tool": name,
                            "done": True,
                        },
                    }
                )

            if tool_output:
                tool_id = tool.get("tool_id", "")
                tool_name = f"{tool_id}/{name}" if tool_id else name

                sources.append(
                    {
                        "source": {"name": tool_name},
                        "document": [str(tool_output)],
                        "metadata": [
                            {
                                "source": tool_name,
                                "parameters": parsed_args,
                            }
                        ],
                        "tool_result": True,
                    }
                )

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "name": name,
                        "content": str(tool_output),
                    }
                )

                if tool.get("metadata", {}).get("file_handler"):
                    skip_files = True

        if skip_files and "files" in metadata:
            metadata.pop("files", None)

    raise RuntimeError("Agent loop reached maximum number of steps without completion")
