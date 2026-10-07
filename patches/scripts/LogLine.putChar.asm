; target: LogLine putChar argc=1 table=methods
; original-sha1: 88cb68a394256a791a549a7962827986dfafc127 (104 bytes)
; reason: backlog counterpart of TextWindow.putChar.asm. Same rule: English
;   codes 0x8540-0x859F use the width table, all other codes keep the
;   original 24*fSclW (+ pitchX) advance and the original right edge 276.
; temps: 0 = code, 1 = width used by the wrap test, 2 = advance
; LogLine class variables: 4 posX, 5 posY, 6 curX, 7 curY, 8 pitchX,
;   10 fClut, 11 fSclW, 12 fSclH; ivar 3 fList
        push_nils 2
        push_const float:24.0
        push_classvar class:LogLine 11
        op *
        store_temp 1
        push_temp 1
        push_classvar class:LogLine 8
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
        push_classvar class:LogLine 11
        op *
        store_temp 1
        push_temp 1
        store_temp 2
measured:
        push_classvar class:LogLine 6
        push_temp 1
        op +
        push_const float:276.0
        op >
        jump_if_false draw
        push_self
        send 0 #crlf
        pop
draw:
        push_ivar 3
        push_const class:FontCharEx
        push_temp 0
        push_classvar class:LogLine 10
        push_int 11
        push_classvar class:LogLine 6
        push_const float:24.0
        push_classvar class:LogLine 11
        op *
        push_const float:2.0
        op /
        op +
        push_classvar class:LogLine 7
        push_classvar class:LogLine 11
        push_classvar class:LogLine 12
        send 7 #new
        push_const float:0.0
        send 1 #setAlpha
        push_classvar class:LogLine 4
        push_classvar class:LogLine 5
        send 2 #setPos
        send 1 #put
        pop
        push_classvar class:LogLine 6
        push_temp 2
        op +
        store_classvar class:LogLine 6
        return_self
