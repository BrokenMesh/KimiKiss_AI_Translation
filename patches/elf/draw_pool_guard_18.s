# Draw packet pool guard, part 6 of 6 (D-041): manager vtable +0x18 (0x0017ea08, type
# 0x9000, count + 2 quadwords), code 0x0017ea98-0x0017eb00 replaced in place.
# Same change as draw_pool_guard_08.s, with the same size check.
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
        lw      $17, 0xc($18)
        bnez    $17, ok
        move    $5, $21
        lw      $15, 0x270($19)         # pool full: the sink
        sltiu   $14, $16, 0x1001
        addiu   $17, $15, 0x410
        b       done
        movz    $17, $zero, $14         # too big for the sink: 0, as before
ok:     jal     0x14c758                # packet header
        move    $4, $17
        lw      $4, 0x2ac($19)
        move    $5, $22
        jal     0x14ab38                # link into the ordering table
        move    $6, $17
done:   move    $2, $17
