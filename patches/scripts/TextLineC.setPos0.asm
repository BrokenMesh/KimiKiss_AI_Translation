; target: TextLineC setPos argc=0 table=methods
; original-sha1: 6b24008e29e2df8a6dad192eaac7776b9e35c361 (76 bytes)
; reason: centred menu text: x of char i = (self xOf: i) - ((self xOf: n) - pitch)/2 instead of i*pitch - (n-1)*pitch/2.
;   Japanese advances stay pitch, so Japanese layout is unchanged.
push_nils 2
push_ivar 11
jump_if_false L004b
push_ivar 10
send.b 0 idx:0
store_temp 0
push_int 0
store_temp 1
L0012: push_temp 1
push_ivar 10
send.b 0 idx:0
push_int 1
op -
op <=
jump_if_false L004b
push_ivar 10
push_temp 1
at
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
send.b 2 idx:9
pop
push_temp 1
push_int 1
op +
store_temp 1
jump L0012
L004b: return_self
