import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import AsyncExitStack
import shlex
from typing import Any, Optional

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamablehttp_client
from mcp.client.session import _default_message_handler
from mcp.types import ServerNotification


NotificationHandler = Callable[[ServerNotification], Awaitable[None]]


class MCPClient:
    def __init__(
        self,
        url: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
        transport: str = "http",
        stdio_server: Optional[StdioServerParameters] = None,
    ):
        self.url = url
        self.headers = headers or {}
        self.transport = transport
        self._stdio_server = stdio_server
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self._connect_lock = asyncio.Lock()
        self._streams_context = None
        self._session_context = None
        self._notification_queue: asyncio.Queue[ServerNotification] = asyncio.Queue()
        self._notification_handlers: list[NotificationHandler] = []
        self._capabilities: dict[str, Any] = {}

    @property
    def capabilities(self) -> dict[str, Any]:
        return self._capabilities

    async def connect(
        self,
        url: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
        transport: Optional[str] = None,
        command: Optional[str] = None,
    ) -> ClientSession:
        if transport is not None:
            self.transport = transport

        if self.transport == "command":
            if command:
                parts = shlex.split(command)
            else:
                parts = []

            if parts:
                base_command, *args = parts
            else:
                base_command = None
                args = []

            if base_command is None:
                raise RuntimeError(
                    "Command-based MCP client requires a non-empty command."
                )

            self._stdio_server = StdioServerParameters(
                command=base_command,
                args=args,
            )
        else:
            if url is not None:
                self.url = url
            if headers is not None:
                self.headers = headers

            if not self.url:
                raise RuntimeError("MCP client requires a URL before connecting.")

        async with self._connect_lock:
            if self.session is not None:
                return self.session

            try:
                if self.transport == "command":
                    if not self._stdio_server:
                        raise RuntimeError(
                            "Command-based MCP client requires stdio parameters."
                        )
                    self._streams_context = stdio_client(self._stdio_server)
                else:
                    self._streams_context = streamablehttp_client(
                        self.url,
                        headers=self.headers or None,
                    )

                transport = await self.exit_stack.enter_async_context(self._streams_context)
                read_stream, write_stream, _ = transport

                self._session_context = ClientSession(
                    read_stream,
                    write_stream,
                    message_handler=self._handle_session_message,
                )

                self.session = await self.exit_stack.enter_async_context(self._session_context)
                await self.session.initialize()
            except Exception:
                await self.disconnect()
                raise

        return self.session

    async def _ensure_session(self) -> ClientSession:
        if self.session is None:
            return await self.connect()
        return self.session

    async def _handle_session_message(self, message) -> None:
        await _default_message_handler(message)

        if isinstance(message, ServerNotification):
            await self._notification_queue.put(message)

            handlers = list(self._notification_handlers)
            for handler in handlers:
                try:
                    await handler(message)
                except Exception:
                    # Handler errors should not break the client – swallow but continue
                    pass

    async def notifications(self) -> AsyncIterator[ServerNotification]:
        while True:
            notification = await self._notification_queue.get()
            yield notification

    def add_notification_handler(self, handler: NotificationHandler) -> None:
        self._notification_handlers.append(handler)

    def remove_notification_handler(self, handler: NotificationHandler) -> None:
        if handler in self._notification_handlers:
            self._notification_handlers.remove(handler)

    async def describe(self) -> dict[str, Any]:
        session = await self._ensure_session()

        tools = await self._collect_paginated(session.list_tools, "tools")
        prompts = await self._collect_paginated(session.list_prompts, "prompts")
        resources = await self._collect_paginated(session.list_resources, "resources")
        resource_templates = await self._collect_paginated(
            session.list_resource_templates, "resourceTemplates"
        )

        self._capabilities = {
            "tools": tools,
            "prompts": prompts,
            "resources": resources,
            "resource_templates": resource_templates,
        }

        return self._capabilities

    async def list_tool_specs(self) -> list[dict[str, Any]]:
        session = await self._ensure_session()
        result = await session.list_tools()
        tool_specs: list[dict[str, Any]] = []
        for tool in result.tools:
            tool_specs.append(
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema or {},
                    "output": tool.outputSchema or None,
                }
            )
        return tool_specs

    async def call_tool(self, function_name: str, function_args: dict[str, Any]) -> list[dict[str, Any]]:
        session = await self._ensure_session()

        result = await session.call_tool(function_name, function_args)
        if not result:
            raise RuntimeError("No result returned from MCP tool call.")

        result_dict = result.model_dump(mode="json")
        if result.isError:
            raise RuntimeError(result_dict.get("content", {}))

        return result_dict.get("content", []) or []

    async def list_resources(self, cursor: Optional[str] = None) -> list[dict[str, Any]]:
        session = await self._ensure_session()
        result = await session.list_resources(cursor=cursor)
        return result.model_dump(mode="json").get("resources", [])

    async def read_resource(self, uri: str) -> dict[str, Any]:
        session = await self._ensure_session()
        result = await session.read_resource(uri)
        return result.model_dump(mode="json")

    async def list_prompts(self, cursor: Optional[str] = None) -> list[dict[str, Any]]:
        session = await self._ensure_session()
        result = await session.list_prompts(cursor=cursor)
        return result.model_dump(mode="json").get("prompts", [])

    async def get_prompt(self, name: str, arguments: Optional[dict[str, str]] = None) -> dict[str, Any]:
        session = await self._ensure_session()
        result = await session.get_prompt(name, arguments)
        return result.model_dump(mode="json")

    async def subscribe_resource(self, uri: str) -> None:
        session = await self._ensure_session()
        await session.subscribe_resource(uri)

    async def unsubscribe_resource(self, uri: str) -> None:
        if not self.session:
            return
        await self.session.unsubscribe_resource(uri)

    async def _collect_paginated(self, func, field: str) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        cursor: Optional[str] = None

        while True:
            result = await func(cursor=cursor)
            payload = result.model_dump(mode="json")
            items.extend(payload.get(field, []))
            cursor = payload.get("nextCursor")
            if not cursor:
                break

        return items

    async def disconnect(self) -> None:
        await self.exit_stack.aclose()
        self.session = None
        self._streams_context = None
        self._session_context = None

    async def __aenter__(self):
        await self.exit_stack.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.exit_stack.__aexit__(exc_type, exc_value, traceback)
        await self.disconnect()
