; target: TextLine setText argc=1 table=methods
; original-sha1: b053a469d383a19a781ace216c5ba12a9d2c6601 (260 bytes)
; reason: menu text: x of char i = self xOf: i (sum of advances) instead of i*pitch.
;   Japanese advances stay pitch, so Japanese layout is unchanged.
push_nils 3
push_temp 0
store_ivar 7
push_ivar 10
store_temp 1
push_temp 1
send.b 0 idx:6
store_temp 2
push_const.b idx:3
push_int 30
send.b 1 idx:4
store_ivar 10
push_int 0
store_temp 3
L001a: push_temp 3
push_temp 0
send.b 0 idx:6
push_int 1
op -
op <=
jump_if_false L00d3
push_temp 2
push_temp 3
op >
jump_if_false L0090
push_temp 1
push_temp 3
at
send.b 0 idx:11
jump_if_false L0051
push_ivar 10
push_temp 1
push_temp 3
at
push_temp 0
push_temp 3
at
send.b 1 idx:12
send.b 1 idx:13
pop
jump L008d
L0051: push_ivar 10
push_temp 1
push_temp 3
at
push_temp 0
push_temp 3
at
push_ivar 4
push_ivar 0
push_self
push_temp 3
send 1 #xOf
push_ivar 1
op +
push_ivar 2
push_ivar 5
push_ivar 6
send.b 7 idx:5
send.b 1 idx:13
pop
push_ivar 10
push_temp 3
at
push_ivar 9
push_ivar 9
push_ivar 9
send.b 3 idx:9
push_ivar 8
send.b 1 idx:10
pop
L008d: jump L00c9
L0090: push_ivar 10
push_const.b idx:14
push_temp 0
push_temp 3
at
push_ivar 4
push_ivar 0
push_self
push_temp 3
send 1 #xOf
push_ivar 1
op +
push_ivar 2
push_ivar 5
push_ivar 6
send.b 7 idx:4
send.b 1 idx:13
pop
push_ivar 10
push_temp 3
at
push_ivar 9
push_ivar 9
push_ivar 9
send.b 3 idx:9
push_ivar 8
send.b 1 idx:10
pop
L00c9: push_temp 3
push_int 1
op +
store_temp 3
jump L001a
L00d3: push_temp 0
send.b 0 idx:6
store_temp 3
L00da: push_temp 3
push_temp 2
push_int 1
op -
op <=
jump_if_false L00fc
push_ivar 10
push_temp 1
push_temp 3
at
send.b 0 idx:7
send.b 1 idx:13
pop
push_temp 3
push_int 1
op +
store_temp 3
jump L00da
L00fc: push_temp 0
store_ivar 7
push_true
store_ivar 11
push_self
send 0 #setPos
pop
return_self
