; target: NameEntryEdit moveCursor argc=1 table=methods
; original-sha1: b53e36a8b399b4c3501110e9280b79afb1297286 (99 bytes)
; reason: clamp curX to 0..slots+1 (was 0..7), re-run layout (slot positions follow the glyph widths) and move the cursor:
; slots through layout, the back and confirm buttons (x -100 and 168, zoomed 1.8 x 0.8) here.
push_nils 0
push_temp 0
store_ivar 11
push_ivar 11
push_int 0
op <
jump_if_false Lend25
push_int 0
store_ivar 11
Lend25:
push_ivar 11
push_self
send 0 #slots
push_int 1
op +
op >
jump_if_false Lend26
push_self
send 0 #slots
push_int 1
op +
store_ivar 11
Lend26:
push_self
send 0 #layout
pop
push_ivar 11
push_int 0
identical
jump_if_false Lend27
push_ivar 10
push_const float:-100.0
push_const float:-160.0
push_int 1
push_const float:3.0
send 4 #move
pop
push_ivar 10
push_const float:1.8
push_const float:0.8
push_int 1
push_const float:3.0
send 4 #zoom
pop
Lend27:
push_ivar 11
push_self
send 0 #slots
push_int 1
op +
identical
jump_if_false Lend28
push_ivar 10
push_const float:168.0
push_const float:-160.0
push_int 1
push_const float:3.0
send 4 #move
pop
push_ivar 10
push_const float:1.8
push_const float:0.8
push_int 1
push_const float:3.0
send 4 #zoom
pop
Lend28:
push_ivar 11
return_top
return_self
