; add: Configuration easyMode argc=1 table=methods
; reason: Easy mode (D-038): the "Easy Mode" panel of the title menu (MainMenu command 6). A box with
;   four On/Off switches drawn with the text system (TextLine, no new textures): No Losses,
;   Fewer Rejections, Easier Meetings, More Tries. Up/down moves the cursor, circle or left/right
;   switches the row, cross closes. The switches are the bits of GameParam easyFlags (1, 2, 4, 8).
;   Argument 0 (title): when the switches changed, the game's "Settings changed. Save?" prompt
;   (ConfigSave, the same as after Settings) writes them to the system data.
;   Temps: 0 mode, 1 box, 2 title, 3 labels, 4 ons, 5 offs, 6 cursor, 7 row, 8 flags at open,
;   9 flags, 10 i, 11 circle guide, 12 cross guide, 13 names, 14 bit, 15 line.
push_nils 15
push_const class:GameParam
send 0 #easyFlags
store_temp 8
push_temp 8
store_temp 9
; ---- box and title
push_const class:DialogBox
push_int 3
push_const float:18.0
push_const float:11.0
push_int 15
send 4 #new
store_temp 1
push_temp 1
push_const float:40.0
push_const float:-8.0
send 2 #setPos
push_const float:0.0
send 1 #setAlpha
send 0 #restart
pop
push_const class:TextLineC
push_int 16
push_const float:40.0
push_const float:-72.0
push_int 24
push_int 0
push_int 2
send 6 #new
push_const float:0.0
send 1 #setAlpha
push_const en:"Easy Mode"
send 1 #setText
store_temp 2
; ---- rows
push_const class:Array
push_int 4
send 1 #new
store_temp 13
push_temp 13
push_int 0
push_const en:"No Losses"
at_put
pop
push_temp 13
push_int 1
push_const en:"Fewer Rejections"
at_put
pop
push_temp 13
push_int 2
push_const en:"Easier Meetings"
at_put
pop
push_temp 13
push_int 3
push_const en:"More Tries"
at_put
pop
push_const class:Array
push_int 4
send 1 #new
store_temp 3
push_const class:Array
push_int 4
send 1 #new
store_temp 4
push_const class:Array
push_int 4
send 1 #new
store_temp 5
push_int 0
store_temp 10
rows: push_temp 10
push_int 3
op <=
jump_if_false built
push_temp 3
push_temp 10
push_const class:TextLine
push_int 16
push_const float:-84.0
push_self
push_temp 10
send 1 #easyRowY
push_int 18
push_int 0
push_int 1
send 6 #new
push_const float:0.0
send 1 #setAlpha
push_temp 13
push_temp 10
at
send 1 #setText
at_put
pop
push_temp 4
push_temp 10
push_const class:TextLine
push_int 16
push_const float:120.0
push_self
push_temp 10
send 1 #easyRowY
push_int 18
push_int 0
push_int 1
send 6 #new
push_const float:0.0
send 1 #setAlpha
push_const en:"On"
send 1 #setText
at_put
pop
push_temp 5
push_temp 10
push_const class:TextLine
push_int 16
push_const float:120.0
push_self
push_temp 10
send 1 #easyRowY
push_int 18
push_int 0
push_int 1
send 6 #new
push_const float:0.0
send 1 #setAlpha
push_const en:"Off"
send 1 #setText
at_put
pop
push_temp 10
push_int 1
op +
store_temp 10
jump rows
built: push_const class:Sprite
push_int 98
push_int 0
push_int 17
send 3 #new
push_const float:0.0
send 1 #setAlpha
store_temp 6
push_int 0
store_temp 7
push_temp 6
push_const float:-104.0
push_self
push_int 0
send 1 #easyRowY
send 2 #setPos
pop
; ---- button hints: circle "OK", cross "Back" (as in Settings)
push_const class:ButtonGuide
push_int 13
push_const float:224.0
push_const float:-182.0
push_int 0
push_int 1
send 5 #new
store_temp 11
push_const class:ButtonGuide
push_int 13
push_const float:208.0
push_const float:-156.0
push_int 1
push_int 2
send 5 #new
store_temp 12
; ---- fade in
push_temp 1
push_const float:1.0
push_int 1
push_int 9
send 3 #fade
pop
push_temp 2
push_const float:1.0
push_int 1
push_int 9
send 3 #fade
pop
push_int 0
store_temp 10
fadein: push_temp 10
push_int 3
op <=
jump_if_false shown
push_temp 3
push_temp 10
at
push_const float:1.0
push_int 1
push_int 9
send 3 #fade
pop
push_temp 10
push_int 1
op +
store_temp 10
jump fadein
shown: push_self
push_temp 4
push_temp 5
push_temp 9
send 3 #easyShow
pop
push_temp 6
push_const float:1.0
push_int 1
push_int 9
send 3 #fade
pop
push_temp 11
send 0 #open
pop
push_temp 12
send 0 #open
pop
push_self
push_int 9
send 1 #sleep
pop
; ---- input loop
loop: push_self
push_int 1
send 1 #sleep
pop
push_const class:ControlPad
send 0 #trig
push_int 64
op &
push_int 0
op <>
jump_if_false notx
push_const class:Sound
push_int 23
send 1 #playSE
pop
jump close
notx: push_const class:ControlPad
send 0 #trig
push_int 32
op &
push_int 0
op <>
push_const class:ControlPad
send 0 #rapid
push_const int:40960
op &
push_int 0
op <>
or
jump_if_false notflip
push_int 1
store_temp 14
push_int 0
store_temp 10
bitloop: push_temp 10
push_temp 7
op <
jump_if_false bitdone
push_temp 14
push_int 2
op *
store_temp 14
push_temp 10
push_int 1
op +
store_temp 10
jump bitloop
bitdone: push_temp 9
push_temp 14
op &
push_int 0
op <>
jump_if_false seton
push_temp 9
push_temp 14
op -
store_temp 9
jump flipped
seton: push_temp 9
push_temp 14
op +
store_temp 9
flipped: push_const class:GameParam
push_temp 9
send 1 #setEasyFlags
pop
push_self
push_temp 4
push_temp 5
push_temp 9
send 3 #easyShow
pop
push_const class:Sound
push_int 12
send 1 #playSE
pop
jump loop
notflip: push_const class:ControlPad
send 0 #rapid
push_const int:4096
op &
push_int 0
op <>
jump_if_false notup
push_temp 7
push_int 3
op +
push_int 4
op %
store_temp 7
jump moved
notup: push_const class:ControlPad
send 0 #rapid
push_const int:16384
op &
push_int 0
op <>
jump_if_false loop
push_temp 7
push_int 1
op +
push_int 4
op %
store_temp 7
moved: push_temp 6
push_const float:-104.0
push_self
push_temp 7
send 1 #easyRowY
send 2 #setPos
pop
push_const class:Sound
push_int 12
send 1 #playSE
pop
jump loop
; ---- close: fade out, free everything
close: push_temp 11
send 0 #close
pop
push_temp 12
send 0 #close
pop
push_temp 1
push_const float:0.0
push_int 1
push_int 6
send 3 #fade
pop
push_temp 2
push_const float:0.0
push_int 1
push_int 6
send 3 #fade
pop
push_temp 6
push_const float:0.0
push_int 1
push_int 6
send 3 #fade
pop
push_int 0
store_temp 10
fadeout: push_temp 10
push_int 3
op <=
jump_if_false faded
push_temp 3
push_temp 10
at
push_const float:0.0
push_int 1
push_int 6
send 3 #fade
pop
push_temp 4
push_temp 10
at
push_const float:0.0
push_int 1
push_int 6
send 3 #fade
pop
push_temp 5
push_temp 10
at
push_const float:0.0
push_int 1
push_int 6
send 3 #fade
pop
push_temp 10
push_int 1
op +
store_temp 10
jump fadeout
faded: push_self
push_int 7
send 1 #sleep
pop
push_temp 11
send 0 #destruct
pop
push_temp 12
send 0 #destruct
pop
push_temp 1
send 0 #destruct
pop
push_temp 2
send 0 #destruct
pop
push_temp 6
send 0 #destruct
pop
push_int 0
store_temp 10
free: push_temp 10
push_int 3
op <=
jump_if_false freed
push_temp 3
push_temp 10
at
send 0 #destruct
pop
push_temp 4
push_temp 10
at
send 0 #destruct
pop
push_temp 5
push_temp 10
at
send 0 #destruct
pop
push_temp 10
push_int 1
op +
store_temp 10
jump free
freed: push_temp 0
push_int 0
identical
push_temp 9
push_temp 8
op <>
and
jump_if_false done
push_const class:ConfigSave
send 0 #new
send 0 #scriptMain
pop
done: return_self
