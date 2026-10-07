#!/usr/bin/env python3
"""Call GhidraMCP tools over MCP stdio from the command line.

Usage: ghidra_call.py <bridge-mcp-ghidra> <tool> [json-args] [<tool> [json-args]]...

Example:
  ghidra_call.py venv/bin/bridge-mcp-ghidra load_program_from_project '{"path": "/SLPS_258.50"}' \\
      get_xrefs_to '{"address": "0x002b16e0"}'

Runs the calls in order in one session and prints each result. Needs the
GhidraMCP headless server on 127.0.0.1:8089 and the bridge venv's Python.
"""
import asyncio
import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def parse_calls(argv):
    calls, i = [], 0
    while i < len(argv):
        tool = argv[i]
        args = {}
        if i + 1 < len(argv) and argv[i + 1].lstrip().startswith('{'):
            args = json.loads(argv[i + 1])
            i += 1
        calls.append((tool, args))
        i += 1
    return calls


async def main():
    bridge, calls = sys.argv[1], parse_calls(sys.argv[2:])
    params = StdioServerParameters(command=bridge, args=['--no-lazy'])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for tool, args in calls:
                result = await session.call_tool(tool, args)
                body = '\n'.join(c.text for c in result.content if getattr(c, 'text', None))
                print(f'== {tool} {json.dumps(args)}{" (error)" if result.isError else ""}')
                print(body)


if __name__ == '__main__':
    asyncio.run(main())
