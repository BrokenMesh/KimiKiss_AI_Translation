# Draw packet pool guard, part 4 of 6 (D-041): manager vtable +0x10 (type 0x7000, a fixed
# 176-byte packet that also holds a reference to a texture), code 0x0017e758-0x0017e83c replaced in place.
# Same change as draw_pool_guard_08.s. The original also built a temporary texture
# holder on the stack (+1 reference, then -1 and a delete if the count reached 0);
# with the node holding its own reference the count never reaches 0 there, so the net
# effect, one reference for the node, is now done directly.
        .set noreorder
        .set noat
        lw      $13, 0x4($21)          # texture
        lui     $12, 0x2a
        addiu   $12, $12, 0x7e88       # texture holder vtable 0x002a7e88
        lui     $14, 0x2b
        addiu   $14, $14, -0x7bc8      # node vtable 0x002a8438
        lw      $15, 0x4($13)
        addiu   $15, $15, 0x1
        sw      $15, 0x4($13)          # the node's reference
        sw      $14, 0x0($17)
        movz    $19, $zero, $2         # no block: the node frees nothing
        sw      $19, 0x8($17)
        sw      $2, 0xc($17)
        sw      $16, 0x10($17)
        sw      $12, 0x14($17)
        sw      $13, 0x18($17)
        lw      $4, 0x2d0($20)
        lw      $14, 0x0($4)
        lw      $15, 0x14($14)
        jalr    $15                     # register the node
        move    $5, $17
        lw      $16, 0xc($17)
        bnez    $16, ok
        nop
        lw      $16, 0x270($20)        # pool full: the sink
        b       done
        addiu   $16, $16, 0x410
ok:     jal     0x14c3e8                # packet header
        move    $4, $16
        lw      $4, 0x2ac($20)
        move    $5, $22
        jal     0x14ab38                # link into the ordering table
        move    $6, $16
        .rept 25
        nop
        .endr
done:   move    $2, $16
