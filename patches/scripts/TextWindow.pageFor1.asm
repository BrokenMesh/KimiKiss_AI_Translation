; add: TextWindow pageFor argc=1 table=methods
; reason: new method, called by Parson>>message: before a message is printed. The scene scripts clear the
;   window themselves (K2_Script.WIN clear) and often let two or three short Japanese messages share the
;   3-row page; English rows differ. If the rows already used plus the rows of the new message (its
;   U+FF0F breaks + 1, inserted by the build's word wrap) exceed 3, the page is cleared first, as the
;   script's own clear does. A fresh page is never cleared. Japanese pages fit as authored and are
;   unchanged. D-024.
; temps: 0 = str, 1 = rows of str, 2 = i, 3 = length, 4 = rows used
; ivars: 2 posY, 6 marginY, 8 pitchY, 33 curY (erase sets curY = posY + marginY + pitchY/2; crlf adds pitchY)
        push_nils 4
        push_int 1
        store_temp 1
        push_int 0
        store_temp 2
        push_temp 0
        send 0 #length
        store_temp 3
loop:
        push_temp 2
        push_temp 3
        op <
        jump_if_false counted
        push_temp 0
        push_temp 2
        at
        push_const int:0x815E
        op =
        jump_if_false next
        push_temp 1
        push_int 1
        op +
        store_temp 1
next:
        push_temp 2
        push_int 1
        op +
        store_temp 2
        jump loop
counted:
        push_ivar 33
        push_ivar 2
        push_ivar 6
        op +
        push_ivar 8
        push_int 2
        op /
        op +
        op -
        push_ivar 8
        op /
        store_temp 4
        push_temp 4
        push_const float:0.5
        op >
        jump_if_false done
        push_temp 4
        push_temp 1
        op +
        push_const float:3.5
        op >
        jump_if_false done
        push_self
        send 0 #clear
        pop
done:
        return_self
