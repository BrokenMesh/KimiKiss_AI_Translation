; target: TextLineC setText argc=1 table=methods
; original-sha1: 8f42d7513632c613cc8c975142848c2be9fdf8bb (116 bytes)
; reason: centred menu text: x of char i = (self xOf: i) - ((self xOf: n) - pitch)/2 instead of i*pitch - (n-1)*pitch/2.
;   Japanese advances stay pitch, so Japanese layout is unchanged.
push_nils 3
push_ivar 7
push_nil
not_identical
jump_if_false L000e
push_self
send_super.b 0 idx:5
pop
L000e: push_temp 0
store_ivar 7
push_temp 0
send.b 0 idx:0
store_temp 1
push_int 0
store_temp 2
L0019: push_temp 2
push_temp 1
push_int 1
op -
op <=
jump_if_false L0062
push_const.b idx:6
push_temp 0
push_temp 2
at
push_ivar 4
push_ivar 0
push_self
push_temp 2
send 1 #xOf
push_self
push_temp 1
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
send.b 7 idx:7
store_temp 3
push_ivar 10
push_temp 3
send.b 1 idx:8
pop
push_temp 2
push_int 1
op +
store_temp 2
jump L0019
L0062: push_temp 0
store_ivar 7
push_true
store_ivar 11
push_self
send_super.b 0 idx:3
pop
push_self
send_super.b 0 idx:4
pop
return_self
