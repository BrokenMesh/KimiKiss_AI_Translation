; target: TextLineC restart argc=0 table=methods
; original-sha1: e371eea3efc4c1c5409f88028da83ef2f2345d2f (100 bytes)
; reason: centred menu text: x of char i = (self xOf: i) - ((self xOf: n) - pitch)/2 instead of i*pitch - (n-1)*pitch/2.
;   Japanese advances stay pitch, so Japanese layout is unchanged.
push_nils 2
push_ivar 11
not
jump_if_false L0063
push_true
store_ivar 11
push_ivar 10
send.b 0 idx:0
store_temp 0
push_int 0
store_temp 1
L0016: push_temp 1
push_temp 0
push_int 1
op -
op <=
jump_if_false L0059
push_ivar 10
push_temp 1
at
push_ivar 7
push_temp 1
at
push_ivar 4
push_ivar 0
push_self
push_temp 1
send 1 #xOf
push_self
push_temp 0
send 1 #xOf
push_ivar 3
op -
push_int 2
op /
op -
push_ivar 1
op +
push_ivar 2
push_ivar 5
push_ivar 6
send.b 7 idx:2
pop
push_temp 1
push_int 1
op +
store_temp 1
jump L0016
L0059: push_self
send_super.b 0 idx:3
pop
push_self
send_super.b 0 idx:4
pop
L0063: return_self
