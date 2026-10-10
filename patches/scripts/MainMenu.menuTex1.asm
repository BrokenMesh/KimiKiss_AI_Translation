; add: MainMenu menuTex argc=1 table=methods
; reason: Easy mode (D-038): sprite {id, n} of title-menu command c. Commands 0-5 come from the
;   original table (const 91); 6 (Easy Mode) is {114, 4}, sysgraph/menu_main4.
push_nils 1
push_temp 0
push_int 6
identical
jump_if_false table
push_const class:Array
push_int 2
send 1 #new
store_temp 1
push_temp 1
push_int 0
push_int 114
at_put
pop
push_temp 1
push_int 1
push_int 4
at_put
pop
push_temp 1
return_top
table: push_const idx:91
push_temp 0
at
return_top
return_self
