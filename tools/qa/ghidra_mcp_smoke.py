#!/usr/bin/env python3
"""Gate G1 check: decompile one function through the GhidraMCP bridge (MCP stdio).

Usage: ghidra_mcp_smoke.py <bridge-mcp-ghidra executable> [program path] [function address]

Requires the GhidraMCP headless server on 127.0.0.1:8089 with the project
that holds the analysed ELF (see docs/phase-0-status.md). Must run with the
Python that has the `mcp` package (the bridge's venv).
"""
import asyncio
import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def text(result):
    return '\n'.join(c.text for c in result.content if getattr(c, 'text', None))


async def main():
    bridge = sys.argv[1]
    program = sys.argv[2] if len(sys.argv) > 2 else '/SLPS_258.50'
    address = sys.argv[3] if len(sys.argv) > 3 else None
    params = StdioServerParameters(command=bridge, args=['--no-lazy'])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = {t.name: t for t in (await session.list_tools()).tools}
            print(f'{len(tools)} MCP tools')
            for name in ('load_program_from_project', 'decompile_function', 'list_functions'):
                if name not in tools:
                    print(f'FAIL: bridge does not expose {name}')
                    return False
                print(f'{name} params: {json.dumps(tools[name].inputSchema.get("properties", {}))}')

            props = tools['load_program_from_project'].inputSchema.get('properties', {})
            key = next(k for k in props if 'path' in k or 'name' in k or 'program' in k)
            print(text(await session.call_tool('load_program_from_project', {key: program}))[:300])

            if address is None:
                funcs = json.loads(text(await session.call_tool('list_functions', {})))['functions']
                print(f'{len(funcs)} functions in the program')
                entry = next((f for f in funcs if f['name'] == 'entry'), funcs[0])
                address = '0x' + entry['address']
            dprops = tools['decompile_function'].inputSchema.get('properties', {})
            dkey = 'address' if 'address' in dprops else next(iter(dprops))
            code = text(await session.call_tool('decompile_function', {dkey: address}))
            print(f'--- decompile_function({dkey}={address}) ---')
            print(code[:1500])
            ok = '(' in code and '{' in code
            print('PASS: decompiled through MCP' if ok else 'FAIL: no C output')
            return ok


if __name__ == '__main__':
    sys.exit(0 if asyncio.run(main()) else 1)
