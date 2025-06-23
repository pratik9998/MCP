import asyncio
import http.client
import json 
import os
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from dotenv import load_dotenv

load_dotenv() 

class MCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.host = os.getenv("LLM_API_HOST")
        self.port = os.getenv("LLM_API_PORT")
        self.conn = http.client.HTTPConnection(self.host, self.port)
    
    async def connect_to_server(self, server_script_path: str):
        is_python = server_script_path.endswith(".py")
        if not is_python:
            raise ValueError("Server script must be a Python file")
        
        command = "python"
        server_params = StdioServerParameters(
            command = command,
            args = [server_script_path],
            env = None
        )
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def process_query(self, query: str) -> str:
        response = await self.session.list_tools()
        available_tools = [{
            "name" : tool.name,
            "description" : tool.description,
            "input_schema" : tool.inputSchema
        } for tool in response.tools]

        payload = json.dumps({
            "model": "fk-gpt-large-v3",
            "messages": [
                {
                    "role": "user",
                    "content": query,
                    "tools" : available_tools
                }
            ],
            "max_tokens": 1024,
            "temperature": 0,
            "top_p": 1
        })
        headers = {
            'Content-Type': 'application/json'
        }

        messages = [
            {
                "role": "user",
                "content": query
            }
        ]

        # initial LLM API Call
        self.conn.request("POST", os.getenv("LLM_API_ENDPOINT"), payload, headers)
        res = self.conn.getresponse()
        response = res.read()
        print(response)
        # Process response and handle tool calls
        final_text = []

        assistant_message_content = []
        for content in response.choices[0].message["content"]:
            if content.type == 'text':
                final_text.append(content.text)
                assistant_message_content.append(content)
            elif content.type == 'tool_use':
                tool_name = content.name
                tool_args = content.input

                # Execute tool call
                result = await self.session.call_tool(tool_name, tool_args)
                final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                assistant_message_content.append(content)
                messages.append({
                    "role": "assistant",
                    "content": assistant_message_content
                })
                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": content.id,
                            "content": result.content
                        }
                    ]
                })

                # get next response from LLM
                payload["messages"] = messages
                self.conn.request("POST", os.getenv("LLM_API_ENDPOINT"), payload, headers)
                res = self.conn.getresponse()
                response = res.read()
                final_text.append(response.choices[0].message["content"])

        return "\n".join(final_text)
    
    async def chat_loop(self):
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")
        while True:
            try:
                query = input("\nQuery: ").strip()
                if query.lower() == 'quit':
                    break
                response = await self.process_query(query)
                print("\n" + response)
            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()


async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())







