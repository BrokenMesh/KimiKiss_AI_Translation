; target: TextLine restart argc=0 table=methods
; original-sha1: 42144c80b37f400dfcccd1fa547072f815376e70 (88 bytes)
; reason: menu text: x of char i = self xOf: i (sum of advances) instead of i*pitch.
;   Japanese advances stay pitch, so Japanese layout is unchanged.
push_nils 2
push_ivar 11
not
jump_if_false L0057
push_true
store_ivar 11
push_ivar 10
send.b 0 idx:6
store_temp 0
push_int 0
store_temp 1
L0016: push_temp 1
push_temp 0
push_int 1
op -
op <=
jump_if_false L004d
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
push_ivar 1
op +
push_ivar 2
push_ivar 5
push_ivar 6
send.b 7 idx:5
pop
push_temp 1
push_int 1
op +
store_temp 1
jump L0016
L004d: push_self
send.b 0 idx:9
pop
push_self
send.b 0 idx:10
pop
L0057: return_self
