; target: TextLine move argc=4 table=methods
; original-sha1: a89a8551bb7e6b8b3cce10bd42b36cab880f505b (82 bytes)
; reason: menu text: x of char i = self xOf: i (sum of advances) instead of i*pitch.
;   Japanese advances stay pitch, so Japanese layout is unchanged.
push_nils 2
push_temp 0
send.b 0 idx:8
store_ivar 1
push_temp 1
send.b 0 idx:8
store_ivar 2
push_ivar 11
jump_if_false L0051
push_ivar 10
send.b 0 idx:6
store_temp 4
push_int 0
store_temp 5
L0020: push_temp 5
push_ivar 10
send.b 0 idx:6
push_int 1
op -
op <=
jump_if_false L0051
push_ivar 10
push_temp 5
at
push_self
push_temp 5
send 1 #xOf
push_ivar 1
op +
push_ivar 2
push_temp 2
push_temp 3
send.b 4 idx:16
pop
push_temp 5
push_int 1
op +
store_temp 5
jump L0020
L0051: return_self
