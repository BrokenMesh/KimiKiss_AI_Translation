; target: ShioriListItem initialize argc=2 table=methods
; original-sha1: fcc1c59e3e9acaf993d95269587d1ab912189dac (184 bytes)
; reason: names in the save list: the surname and given name are measured with xOf: (English is proportional); when both
; together are wider than 150 px (the row box; 3 + 3 Japanese characters are exactly 150) the two TextLines use
; font scale 0.75 (pitch 18) or 0.5 (pitch 12). name0X is the left edge -76 plus half a cell; name1X follows the
; surname width plus a 6 px gap (was the {-70,-34,-10,14}[min(length,3)] table). Japanese names of up to 3 + 3
; characters are placed exactly as before. D-016.
push_nils 7
push_temp 0
store_ivar 0
push_temp 1
push_int 1
op +
store_ivar 1
push_const.b idx:0
push_temp 1
send.b 1 idx:1
store_ivar 2
push_const.b idx:2
push_int 4
push_const.b idx:3
push_const.b idx:4
push_temp 0
send.b 4 idx:5
store_ivar 3
push_const.b idx:6
push_temp 0
push_int 1
op +
send.b 1 idx:5
push_ivar 2
send.b 0 idx:7
send.b 1 idx:8
send.b 0 idx:9
store_ivar 4
push_const.b idx:6
push_temp 0
push_int 1
op +
send.b 1 idx:5
push_ivar 2
send.b 0 idx:10
send.b 1 idx:8
send.b 0 idx:9
store_ivar 5
push_ivar 4
push_ivar 2
send 0 #getMyouji
send 0 #length
send 1 #xOf
store_temp 2
push_ivar 5
push_ivar 2
send 0 #getNamae
send 0 #length
send 1 #xOf
store_temp 3
push_temp 2
push_temp 3
op +
push_const float:6.0
op +
store_temp 4
push_int 2
store_temp 5
push_int 24
store_temp 6
push_temp 4
push_const float:150.0
op >
jump_if_false Lend8
push_int 1
store_temp 5
push_int 18
store_temp 6
Lend8:
push_temp 4
push_const float:200.0
op >
jump_if_false Lend9
push_int 0
store_temp 5
push_int 12
store_temp 6
Lend9:
push_ivar 4
push_temp 5
send 1 #setFontScale
pop
push_ivar 4
push_temp 6
send 1 #setPitch
pop
push_ivar 5
push_temp 5
send 1 #setFontScale
pop
push_ivar 5
push_temp 6
send 1 #setPitch
pop
push_const float:-76.0
push_const float:0.5
push_temp 6
op *
op +
store_ivar 9
push_const float:-76.0
push_temp 2
push_const float:6.0
op +
push_temp 6
op *
push_const float:24.0
op /
op +
push_const float:0.5
push_temp 6
op *
op +
store_ivar 10
push_const.b idx:14
push_int 12
send.b 1 idx:5
store_ivar 6
push_int 0
store_temp 3
L0081: push_temp 3
push_int 11
op <=
jump_if_false L009d
push_ivar 6
push_temp 3
push_const.b idx:15
send.b 0 idx:5
at_put
pop
push_temp 3
push_int 1
op +
store_temp 3
jump L0081
L009d: push_false
store_ivar 13
push_self
push_const.b idx:16
send.b 1 idx:17
pop
push_self
push_const.b idx:18
send.b 1 idx:19
pop
push_self
push_const.b idx:16
push_const.b idx:16
send.b 2 idx:20
pop
return_self