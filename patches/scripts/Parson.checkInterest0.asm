; target: Parson checkInterest argc=0 table=methods
; original-sha1: 36d0a8ddff9d4f6de71fb80ad2936e29022125de
; reason: Easy mode (D-038) "Fewer Rejections": when she is met on the map, the two rolls use
;   interest + 3 (the stored interest does not change). Refusal ("NG", no conversation) at the
;   starting interest 3 drops from 60 % to 28 %, at interest 0 from 100 % to 60 %, from 7 on it is 0.
;   With the flag off the method is the original: 2 = she comes to you, 0 = OK, 1 = NG.
push_nils 2
push_ivar 0
send 0 #getInterest
store_temp 0
push_const class:GameParam
push_int 2
send 1 #easy
jump_if_false roll
push_temp 0
push_int 3
op +
store_temp 0
roll: push_const class:Integer
push_int 20
send 1 #rnd
store_temp 1
push_temp 0
push_temp 1
op >
jump_if_false second
push_int 2
return_top
second: push_const class:Integer
push_int 10
send 1 #rnd
store_temp 1
push_temp 0
push_temp 1
op >
jump_if_false ng
push_int 0
return_top
ng: push_int 1
return_top
return_self
