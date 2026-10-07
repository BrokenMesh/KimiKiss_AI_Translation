# String from C string (0x00116030, 80 instructions, replaced in place). D-027.
#
# The original sized the String's 16-bit code array by strlen (bytes), so a double-byte
# string took 4 bytes of VM object memory per character, half of it unused. English
# (D-012) is all double-byte codes, about twice the bytes of the Japanese, and the full
# script no longer fit in the fixed 0x940000-byte object space (boot hang).
# This version counts characters first (a byte with bit 7 set takes its trail byte, as
# in the fill loop) and allocates exactly that many slots. Calls, object layout, the
# GC root push/pop and the empty-string case (capacity 16, size 0) are unchanged.
        .set noreorder
        .set noat
        addiu   $sp, $sp, -0x30
        sd      $s0, 0x00($sp)
        sd      $s1, 0x08($sp)
        sd      $s2, 0x10($sp)
        sd      $s3, 0x18($sp)
        sd      $s4, 0x20($sp)
        sd      $ra, 0x28($sp)
        move    $s1, $a0                # s1 = source bytes
        move    $t0, $a0
        move    $s3, $zero              # s3 = character count
count:  lbu     $t6, 0($t0)
        beqz    $t6, counted
        srl     $t7, $t6, 7             # 1 for a lead byte
        addu    $t0, $t0, $t7           # skip its trail byte
        addiu   $t0, $t0, 1
        b       count
        addiu   $s3, $s3, 1
counted:
        jal     0x113258                # new object header
        nop
        move    $s2, $v0
        beqz    $s2, epilogue
        move    $v0, $zero
        # unchanged: 0x00116068-0x001160dc of the original
        lui     $t4, 0x2c
        lw      $t7, -0x72c($t4)
        sw      $t7, 4($s2)
        addiu   $t7, $zero, 0x300
        sw      $t7, 0($s2)
        lui     $s0, 0x2c
        lw      $t5, -0x74c($s0)
        sll     $t6, $t5, 2
        lui     $t7, 0x28
        addiu   $t7, $t7, -0x5598
        addu    $t6, $t6, $t7
        sw      $s2, 0($t6)
        addiu   $t5, $t5, 1
        sw      $t5, -0x74c($s0)
        sw      $zero, 8($s2)
        lw      $t7, -0x72c($t4)
        lw      $t7, 8($t7)
        lw      $a1, 0x10($t7)
        sra     $a1, $a1, 1
        jal     0x1129c4
        move    $a0, $s2
        addiu   $s4, $v0, 4
        addiu   $a0, $zero, 0x10
        jal     0x116be4                # code array, capacity = count (16 if empty)
        movn    $a0, $s3, $s3
        sw      $v0, 4($s4)
        lw      $t4, 0xc($v0)
        lw      $t7, -0x74c($s0)
        addiu   $t7, $t7, -1
        sw      $t7, -0x74c($s0)
        # fill: exactly s3 codes
        blez    $s3, filled
        move    $t5, $zero
fill:   lbu     $t6, 0($s1)
        addiu   $s1, $s1, 1
        andi    $t7, $t6, 0x80
        beqz    $t7, store
        sll     $t7, $t5, 1
        lbu     $t8, 0($s1)
        sll     $t6, $t6, 8
        addiu   $s1, $s1, 1
        or      $t6, $t6, $t8
store:  addu    $t7, $t7, $t4
        addiu   $t5, $t5, 1
        bne     $t5, $s3, fill
        sh      $t6, 0($t7)
filled: sll     $t7, $t5, 1
        ori     $t7, $t7, 1
        sw      $t7, 0($s4)
        move    $v0, $s2
epilogue:
        ld      $s0, 0x00($sp)
        ld      $s1, 0x08($sp)
        ld      $s2, 0x10($sp)
        ld      $s3, 0x18($sp)
        ld      $s4, 0x20($sp)
        ld      $ra, 0x28($sp)
        jr      $ra
        addiu   $sp, $sp, 0x30
