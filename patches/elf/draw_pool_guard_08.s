# Draw packet pool guard, part 2 of 6 (D-041): manager vtable +0x08 (0x0017e468, sprite
# and polygon packets, type 0x2000 | flags), code 0x0017e500-0x0017e56c replaced in place.
#
# The original stored the pool block from 0x001003c0 without looking at it. When the
# 512 KB pool is full that is 0: the header writer, the ordering-table link and the
# caller all write near address 0 (on a console the kernel area: freeze or crash; issue
# #9, the topic bag report). Now the node is still filled and registered (so it is
# recycled as usual) but owns no pool memory, and the caller gets the sink (0x1000
# bytes after the third ordering table, see draw_pool_sink.s), which is never linked:
# the sprite is skipped for that frame. A request larger than the sink keeps the old
# behaviour (returns 0). The original's stack round trip for the three node fields is
# gone; the node+4 store is dropped because registering (0x0017eb30) writes node+4.
        .set noreorder
        .set noat
        lui     $15, 0x2b
        addiu   $15, $15, -0x7bb0       # node vtable 0x002a8450
        sw      $15, 0x0($18)
        movz    $20, $zero, $2          # no block: the node frees nothing
        sw      $20, 0x8($18)           # pool
        sw      $2, 0xc($18)            # block
        sw      $16, 0x10($18)          # size in bytes
        lw      $4, 0x2d0($19)
        lw      $14, 0x0($4)
        lw      $15, 0x14($14)
        jalr    $15                     # register the node
        move    $5, $18
        lw      $17, 0xc($18)
        bnez    $17, ok
        move    $5, $21
        lw      $15, 0x270($19)         # pool full: the sink
        sltiu   $14, $16, 0x1001
        addiu   $17, $15, 0x410
        b       done
        movz    $17, $zero, $14         # too big for the sink: 0, as before
ok:     move    $6, $22
        jal     0x14be88                # packet header
        move    $4, $17
        lw      $4, 0x2ac($19)
        move    $5, $23
        jal     0x14ab38                # link into the ordering table
        move    $6, $17
done:   move    $2, $17
