# Draw packet pool guard, part 3 of 6 (D-041): manager vtable +0x0c (0x0017e5a0, type
# 0x5000, a fixed 80-byte packet), code 0x0017e630-0x0017e698 replaced in place.
# Same change as draw_pool_guard_08.s; the packet always fits the sink.
        .set noreorder
        .set noat
        lui     $15, 0x2b
        addiu   $15, $15, -0x7bb0       # node vtable 0x002a8450
        sw      $15, 0x0($18)
        movz    $20, $zero, $2          # no block: the node frees nothing
        sw      $20, 0x8($18)
        sw      $2, 0xc($18)
        sw      $16, 0x10($18)
        lw      $4, 0x2d0($19)
        lw      $14, 0x0($4)
        lw      $15, 0x14($14)
        jalr    $15                     # register the node
        move    $5, $18
        lw      $16, 0xc($18)
        bnez    $16, ok
        move    $5, $21
        lw      $16, 0x270($19)         # pool full: the sink
        b       done
        addiu   $16, $16, 0x410
ok:     jal     0x14c5c8                # packet header
        move    $4, $16
        lw      $4, 0x2ac($19)
        move    $5, $22
        jal     0x14ab38                # link into the ordering table
        move    $6, $16
        nop
        nop
done:   move    $2, $16
