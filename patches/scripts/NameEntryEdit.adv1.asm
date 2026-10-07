; add: NameEntryEdit adv argc=1 table=methods
; reason: new method. Advance of the code in a name slot, px at scale 1.0: English codes 0x8540-0x859F by the width
; table (D-013), the empty marker 0x8140 by emptyW, every other code a full 24 px cell. D-016.
push_nils 0
push_temp 0
push_const int:0x8540
op >=
push_temp 0
push_const int:0x859f
op <=
and
jump_if_false Lend0
push_const @EN_WIDTHS
push_temp 0
push_const int:0x8540
op -
at
return_top
Lend0:
push_temp 0
push_const int:0x8140
identical
jump_if_false Lend1
push_self
send 0 #emptyW
return_top
Lend1:
push_const float:24.0
return_top
return_self
