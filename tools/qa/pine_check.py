#!/usr/bin/env python3
"""Gate G0 PINE check through mcp-pine (MCP stdio): liveness, run status, EE read.

Usage: pine_check.py <mcp-pine dist/index.js> <SLPS ELF> [socket path]

Reads the first words of the ELF's load segment from EE RAM and compares
them with the ELF file, so a pass proves the read hits real game memory.
Run while the game is booted with PINE enabled (slot 28011).

Every call is serial. pine_get_info is deliberately not used: it pipelines
five PINE opcodes, and PCSX2 drops replies under that load, which also
leaves mcp-pine's reply queue misaligned for later calls.
"""
import asyncio
import os
import re
import struct
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def text(result):
    return '\n'.join(c.text for c in result.content if getattr(c, 'text', None))


def first_segment(elf_path, words=4):
    data = open(elf_path, 'rb').read()
    phoff, = struct.unpack_from('<I', data, 0x1C)
    _, off, vaddr = struct.unpack_from('<3I', data, phoff)
    return vaddr, list(struct.unpack_from(f'<{words}I', data, off))


async def main():
    server, elf = sys.argv[1:3]
    env = dict(os.environ, PINE_TARGET='pcsx2', PINE_SLOT='28011')
    if len(sys.argv) > 3:
        env['PINE_SOCKET_PATH'] = sys.argv[3]
    params = StdioServerParameters(command='node', args=[server], env=env)
    vaddr, expect = first_segment(elf)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for tool in ('pine_ping', 'pine_get_status'):
                print(f'{tool}: {text(await session.call_tool(tool, {}))}')
            got = []
            for i in range(len(expect)):
                r = text(await session.call_tool('pine_read32', {'address': vaddr + 4 * i}))
                m = re.search(r'\((0x[0-9A-Fa-f]+)\)', r)  # "0x00100000: 666763248 (0x27BDFFF0)"
                if not m:
                    print(f'pine_read32 returned: {r}')
                    return False
                got.append(int(m.group(1), 16))
    print(f'EE {vaddr:#010x}: {[hex(v) for v in got]}')
    print(f'ELF          : {[hex(v) for v in expect]}')
    ok = got == expect
    print('PASS: PINE reads match the ELF in EE RAM' if ok else 'FAIL: EE RAM does not match the ELF')
    return ok


if __name__ == '__main__':
    try:
        ok = asyncio.run(main())
    except Exception as e:  # MCP errors arrive wrapped in exception groups
        while isinstance(e, BaseExceptionGroup):
            e = e.exceptions[0]
        print(f'FAIL: {type(e).__name__}: {e}')
        ok = False
    sys.exit(0 if ok else 1)
