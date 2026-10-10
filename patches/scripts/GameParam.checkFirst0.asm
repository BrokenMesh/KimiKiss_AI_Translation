; target: GameParam checkFirst argc=0 table=methods2
; original-sha1: 3c44276696e38ba599d93febbe7fb62444e05867
; reason: Easy mode (D-038) "Easier Meetings": the first encounter spot of a map move rolls the encounter
;   table (checkEncount: 0) again, up to 8 more times, until the roll names a girl who has been met
;   and is still in the game (Parson isEnable:). The table's people and weights are unchanged, so a
;   girl only appears where and when the game puts her. Flag off: one roll, as the original.
;   Only caller: GameMain>>kounai:, which takes this path only when no event is set for the move.
push_nils 2
push_const class:GameParam
push_int 0
send 1 #checkEncount
store_temp 0
push_const class:GameParam
push_int 4
send 1 #easy
jump_if_false done
push_int 0
store_temp 1
loop: push_temp 1
push_int 8
op <
jump_if_false done
push_temp 0
push_int 0
op >
jump_if_false retry
push_const class:Parson
push_temp 0
send 1 #isEnable
jump_if_false retry
jump done
retry: push_const class:GameParam
push_int 0
send 1 #checkEncount
store_temp 0
push_temp 1
push_int 1
op +
store_temp 1
jump loop
done: push_temp 0
return_top
return_self
