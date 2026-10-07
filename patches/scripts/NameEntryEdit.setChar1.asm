; target: NameEntryEdit setChar argc=1 table=methods
; original-sha1: c7c53026b66e708c732a2712085eed39a56fff3f (365 bytes)
; reason: slot range 1..slots (was 1..6) and no 3-slot literals. A typed code goes through toEnglish: first (full-width
; letters, digits and symbols become English codes). A String (history entry) fills the field the cursor is in
; (8 slots, or 6 for the deck name), pads with blanks, and moves to the given-name field or the confirm button.
push_nils 5
push_ivar 11
push_int 0
op >
push_ivar 11
push_self
send 0 #slots
op <=
and
jump_if_false Lend33
push_temp 0
push_const class:String
send 1 #isKindOf
jump_if_false Lelse34
push_temp 0
send 0 #length
store_temp 1
push_self
send 0 #fieldN
store_temp 4
push_int 0
store_temp 3
push_ivar 0
push_int 0
identical
push_ivar 11
push_temp 4
op >
and
jump_if_false Lend35
push_temp 4
store_temp 3
Lend35:
push_int 0
store_temp 2
Lwh36:
push_temp 2
push_temp 4
op <
jump_if_false Lend36
push_temp 2
push_temp 1
op <
jump_if_false Lelse37
push_self
push_temp 0
push_temp 2
at
send 1 #toEnglish
store_temp 5
jump Lend37
Lelse37:
push_const int:0x8140
store_temp 5
Lend37:
push_ivar 14
push_temp 3
push_temp 2
op +
push_temp 5
at_put
pop
push_ivar 13
push_temp 3
push_temp 2
op +
at
push_temp 5
send 1 #setCode
pop
push_temp 2
push_int 1
op +
store_temp 2
jump Lwh36
Lend36:
push_ivar 0
push_int 0
identical
push_temp 3
push_int 0
identical
and
jump_if_false Lelse38
push_self
push_temp 4
push_int 1
op +
send 1 #moveCursor
pop
jump Lend38
Lelse38:
push_self
push_self
send 0 #slots
push_int 1
op +
send 1 #moveCursor
pop
Lend38:
jump Lend34
Lelse34:
push_self
push_temp 0
send 1 #toEnglish
store_temp 5
push_ivar 14
push_ivar 11
push_int 1
op -
push_temp 5
at_put
pop
push_ivar 13
push_ivar 11
push_int 1
op -
at
push_temp 5
send 1 #setCode
pop
push_self
send 0 #moveCursorR
pop
Lend34:
Lend33:
push_ivar 11
return_top
return_self
