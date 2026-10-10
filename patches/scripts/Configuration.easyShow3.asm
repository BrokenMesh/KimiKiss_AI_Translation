; add: Configuration easyShow argc=3 table=methods
; reason: Easy mode (D-038): shows "On" or "Off" in each row of the Easy Mode panel by fading the
;   row's two text lines, like the Rumble Yes/None switch of Settings. Args: ons, offs, flags.
push_nils 3
push_int 0
store_temp 3
push_int 1
store_temp 4
row: push_temp 3
push_int 3
op <=
jump_if_false done
push_temp 2
push_temp 4
op &
push_int 0
op <>
store_temp 5
push_temp 0
push_temp 3
at
push_temp 5
jump_if_false on0
push_const float:1.0
jump on1
on0: push_const float:0.0
on1: push_int 1
push_int 3
send 3 #fade
pop
push_temp 1
push_temp 3
at
push_temp 5
jump_if_false off0
push_const float:0.0
jump off1
off0: push_const float:1.0
off1: push_int 1
push_int 3
send 3 #fade
pop
push_temp 4
push_int 2
op *
store_temp 4
push_temp 3
push_int 1
op +
store_temp 3
jump row
done: return_self
