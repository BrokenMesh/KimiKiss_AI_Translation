; add: TextLine xOf argc=1 table=methods
; reason: new method. Returns the x offset (float) of character i of `text`:
;   the sum of the advances of characters 0..i-1. Japanese and other codes
;   advance by pitch; English codes 0x8540-0x859F by width*pitch/24, the
;   glyph's share of its 24 px cell (D-013). TextLineC inherits it.
; temps: 0 = i, 1 = sum, 2 = k, 3 = code
; ivars: 3 pitch, 7 text
        push_nils 3
        push_const float:0.0
        store_temp 1
        push_int 0
        store_temp 2
loop:
        push_temp 2
        push_temp 0
        op <
        jump_if_false done
        push_ivar 7
        push_temp 2
        at
        store_temp 3
        push_temp 3
        push_const int:0x8540
        op >=
        push_temp 3
        push_const int:0x859F
        op <=
        and
        jump_if_false fixed
        push_temp 1
        push_const @EN_WIDTHS
        push_temp 3
        push_const int:0x8540
        op -
        at
        push_ivar 3
        op *
        push_const float:24.0
        op /
        op +
        store_temp 1
        jump next
fixed:
        push_temp 1
        push_ivar 3
        op +
        store_temp 1
next:
        push_temp 2
        push_int 1
        op +
        store_temp 2
        jump loop
done:
        push_temp 1
        return_top
