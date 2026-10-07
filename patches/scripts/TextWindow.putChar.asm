; target: TextWindow putChar argc=1 table=methods
; original-sha1: 97a7d8dee7859c458cac7ee8e11a089c97c86a9d (96 bytes)
; reason: variable-width English (decisions D-011..D-013). English codes
;   0x8540-0x859F advance by the width table; every other code keeps the
;   original fixed advance fontW*fontSclW + pitchX and the original wrap
;   test, so Japanese renders exactly as before.
; temps: 0 = code, 1 = width used by the wrap test, 2 = advance
; ivars: 0 layer, 1 posX, 3 width, 5 marginX, 7 pitchX, 9 fontW,
;   11 fontSclW, 12 fontSclH, 16 fontClut, 17 fontFade, 18 fontList,
;   32 curX, 33 curY
        push_nils 2
        push_ivar 9
        push_ivar 11
        op *
        store_temp 1
        push_temp 1
        push_ivar 7
        op +
        store_temp 2
        push_temp 0
        push_const int:0x8540
        op >=
        push_temp 0
        push_const int:0x859F
        op <=
        and
        jump_if_false measured
        push_const @EN_WIDTHS
        push_temp 0
        push_const int:0x8540
        op -
        at
        push_ivar 11
        op *
        store_temp 1
        push_temp 1
        store_temp 2
measured:
        push_ivar 32
        push_temp 1
        op +
        push_ivar 1
        push_ivar 3
        op +
        push_ivar 5
        op -
        op >
        jump_if_false draw
        push_self
        send 0 #crlf
        pop
draw:
        push_ivar 18
        push_const class:FontChar
        push_temp 0
        push_ivar 16
        push_ivar 0
        push_ivar 32
        push_ivar 9
        push_ivar 11
        op *
        push_const float:2.0
        op /
        op +
        push_ivar 33
        push_ivar 11
        push_ivar 12
        send 7 #new
        push_const float:0.0
        send 1 #setAlpha
        push_const float:1.0
        push_int 0
        push_ivar 17
        send 3 #fade
        send 1 #put
        pop
        push_ivar 32
        push_temp 2
        op +
        store_ivar 32
        return_self
