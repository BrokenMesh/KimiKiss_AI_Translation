# Draw packet pool guard, part 1 of 6 (D-041): the overflow sink.
#
# The draw manager (0x002c03e0) takes three 0x410-byte ordering tables from its own
# 512 KB packet pool when it is built (0x0017dfb0-0x0017dfd4) and never frees them. The
# third one is asked for 0x1410 bytes instead: its last 0x1000 bytes are a scratch area
# that the five packet entry points (draw_pool_guard_*.s) hand out when the pool is full.
# Nothing is ever linked from there, so the GS never reads it.
        .set noreorder
        .set noat
        addiu   $5, $zero, 0x1410       # was 0x410
