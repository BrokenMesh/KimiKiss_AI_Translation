; target: MainMenu makeMenu argc=0 table=methods
; original-sha1: 5dfd2687adb6e8b76029b938e4ca97a633c451e1
; reason: Easy mode (D-038): the title menu gets command 6 "Easy Mode" after Settings (texture
;   sysgraph/menu_main4, sprite 114 n 4: the unused "Options" item, relabelled in textures.toml).
;   The rest is the original method (scfasm listing); the changed lines are marked "new".
push_nils 2
push_ivar 0
push_true
identical
jump_if_false.l L0010
push_int 1
store_ivar 1
jump.l L0014
L0010: push_int 0
store_ivar 1
L0014: push_const.b idx:85
push_int 7
send.b 1 idx:18
store_ivar 3
push_ivar 3
push_int 0
send.b 1 idx:86
pop
push_ivar 3
push_int 1
send.b 1 idx:86
pop
push_ivar 3
push_int 2
send.b 1 idx:86
pop
push_const.b idx:54
send.b 0 idx:18
send.b 0 idx:87
push_int 0
op >
jump_if_false.l L004b
push_ivar 3
push_int 3
send.b 1 idx:86
pop
L004b: push_const.b idx:6
send.b 0 idx:88
push_int 0
op >
jump_if_false.l L005e
push_ivar 3
push_int 4
send.b 1 idx:86
pop
L005e: push_ivar 3
push_int 5
send.b 1 idx:86
pop
push_ivar 3                 ; new: command 6 = Easy Mode, after Settings
push_int 6
send 1 #put
pop
push_const.b idx:89
push_ivar 3
send.b 0 idx:90
send.b 1 idx:18
store_temp 0
push_int 0
store_temp 1
L0076: push_temp 1
push_temp 0
send.b 0 idx:90
push_int 1
op -
op <=
jump_if_false.l L009b
push_temp 0
push_temp 1
push_self                   ; new: the sprite pair comes from menuTex: (const 91 has no entry 6)
push_ivar 3
push_temp 1
at
send 1 #menuTex
at_put
pop
push_temp 1
push_int 1
op +
store_temp 1
jump.l L0076
L009b: push_const.b idx:92
push_temp 0
push_const.b idx:93
push_ivar 1
send.b 3 idx:18
store_ivar 2
return_self
