; target: TextLineC move argc=4 table=methods
; original-sha1: 1e0c3cbaabf5dc220a75096c40695da27e0e9c9b (94 bytes)
; reason: centred menu text: x of char i = (self xOf: i) - ((self xOf: n) - pitch)/2 instead of i*pitch - (n-1)*pitch/2.
;   Japanese advances stay pitch, so Japanese layout is unchanged.
push_nils 2
push_temp 0
send.b 0 idx:1
store_ivar 1
push_temp 1
send.b 0 idx:1
store_ivar 2
push_ivar 11
jump_if_false L005d
push_ivar 10
send.b 0 idx:0
store_temp 4
push_int 0
store_temp 5
L0020: push_temp 5
push_ivar 10
send.b 0 idx:0
push_int 1
op -
op <=
jump_if_false L005d
push_ivar 10
push_temp 5
at
push_self
push_temp 5
send 1 #xOf
push_self
push_temp 4
send 1 #xOf
push_ivar 3
op -
push_int 2
op /
op -
push_ivar 1
op +
push_ivar 2
push_temp 2
push_temp 3
send.b 4 idx:10
pop
push_temp 5
push_int 1
op +
store_temp 5
jump L0020
L005d: return_self
