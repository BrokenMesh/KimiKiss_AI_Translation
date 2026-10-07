; target: NameEntryEdit clrChar argc=0 table=methods
; original-sha1: e3c6a011b33aba33ae80e8ccfeda49a36ebc4cca (82 bytes)
; reason: confirm button index is slots+1 (was 7); after blanking the slot, moveCursor re-runs the layout.
push_nils 0
push_ivar 11
push_int 0
op >
jump_if_false Lend29
push_ivar 11
push_self
send 0 #slots
push_int 1
op +
identical
jump_if_false Lelse30
push_self
send 0 #moveCursorL
pop
jump Lend30
Lelse30:
push_ivar 14
push_ivar 11
push_int 1
op -
at
push_const int:0x8140
identical
jump_if_false Lend31
push_self
send 0 #moveCursorL
pop
Lend31:
Lend30:
push_ivar 11
push_int 0
op >
jump_if_false Lend32
push_ivar 14
push_ivar 11
push_int 1
op -
push_const int:0x8140
at_put
pop
push_ivar 13
push_ivar 11
push_int 1
op -
at
push_const int:0x8140
send 1 #setCode
pop
push_self
push_ivar 11
send 1 #moveCursor
pop
Lend32:
Lend29:
push_ivar 11
return_top
return_self
