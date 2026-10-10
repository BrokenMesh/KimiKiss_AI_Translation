; add: GameParam easyFlags argc=0 table=methods2
; reason: Easy mode (D-038). The four switches are bits of an Integer in class variable 18, the
;   "autoSkip" setting the game sets to false, saves in the system data (config array [0]) and
;   never reads: 1 No Losses, 2 Fewer Rejections, 4 Easier Meetings, 8 More Tries.
;   nil (before init) and the Boolean of an old save or the original game read as 0.
push_nils 1
push_ivar 18                ; class side: class variable 18 (autoSkip)
store_temp 0
push_temp 0
push_nil
identical
jump_if_false notnil
push_int 0
return_top
notnil: push_temp 0
push_const class:Integer
send 1 #isKindOf
jump_if_false zero
push_temp 0
return_top
zero: push_int 0
return_top
return_self
