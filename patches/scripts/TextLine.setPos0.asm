; target: TextLine setPos argc=0 table=methods
; original-sha1: 681ad49503ef6a5a0585220db0a9f198d1e370b0 (64 bytes)
; reason: menu text: x of char i = self xOf: i (sum of advances) instead of i*pitch.
;   Japanese advances stay pitch, so Japanese layout is unchanged.
push_nils 2
push_ivar 11
jump_if_false L003f
push_ivar 10
send.b 0 idx:6
store_temp 0
push_int 0
store_temp 1
L0012: push_temp 1
push_ivar 10
send.b 0 idx:6
push_int 1
op -
op <=
jump_if_false L003f
push_ivar 10
push_temp 1
at
push_self
push_temp 1
send 1 #xOf
push_ivar 1
op +
push_ivar 2
send.b 2 idx:15
pop
push_temp 1
push_int 1
op +
store_temp 1
jump L0012
L003f: return_self
