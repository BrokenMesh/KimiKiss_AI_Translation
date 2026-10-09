; target: TextWindow initialize argc=7 table=methods
; original-sha1: c50b748d00ee1f4c7366e59fecce85d67eb96185 (277 bytes)
; reason: D-034. The message box shows 3 lines. With the original line pitch 44 and top margin 18, the English
; third line ends 7 px above the frame while the first line starts 22 px below it (English glyphs have
; descenders and no tall ink at the top). Pitch 40 and margin 16 centre the 3-line block (about 18 px above
; and below) and keep 20 px between a line's descenders and the next line's capitals, as the Japanese had.
; Only constants change; TextWindow is created once (Parson.messWin), so this affects the dialogue box only.
push_nils 0
push_temp 0
store_ivar 0
push_temp 1
store_ivar 1
push_temp 2
store_ivar 2
push_temp 3
store_ivar 3
push_temp 4
store_ivar 4
push_temp 5
store_ivar 9
push_temp 6
store_ivar 10
push_const.b idx:0
store_ivar 5
push_const float:16.0    ; marginY (was 18)
store_ivar 6
push_const.b idx:2
store_ivar 7
push_const float:40.0    ; pitchY (was 44)
store_ivar 8
push_const.b idx:4
push_int 2
at
push_int 0
at
store_ivar 11
push_const.b idx:4
push_int 2
at
push_int 1
at
store_ivar 12
push_const.b idx:5
push_int 2
at
store_ivar 14
push_const.b idx:5
push_int 2
at
store_ivar 15
push_int 0
store_ivar 16
push_const.b idx:5
push_int 1
at
push_const.b idx:6
op *
store_ivar 17
push_int 0
store_ivar 34
push_const.b idx:7
push_const.b idx:8
send.b 1 idx:9
store_ivar 19
push_const.b idx:7
push_const.b idx:8
send.b 1 idx:9
store_ivar 20
push_const.b idx:10
push_const.b idx:8
send.b 1 idx:9
store_ivar 18
push_false
store_ivar 28
push_false
store_ivar 21
push_false
store_ivar 29
push_nil
store_ivar 23
push_nil
store_ivar 24
push_false
store_ivar 22
push_int 0
store_ivar 25
push_false
store_ivar 26
push_true
store_ivar 27
push_const.b idx:11
push_int 1
push_int 0
push_temp 0
push_int 1
op -
send.b 3 idx:9
push_const.b idx:12
push_const.b idx:13
send.b 2 idx:14
push_const.b idx:12
send.b 1 idx:15
store_ivar 36
push_const.b idx:11
send.b 0 idx:9
store_ivar 37
push_const.b idx:11
send.b 0 idx:9
store_ivar 38
push_const.b idx:11
send.b 0 idx:9
store_ivar 39
push_const.b idx:11
send.b 0 idx:9
store_ivar 43
push_const.b idx:11
send.b 0 idx:9
store_ivar 40
push_int 0
store_ivar 30
push_int 0
store_ivar 31
push_ivar 1
push_ivar 5
op +
store_ivar 32
push_ivar 2
push_ivar 6
op +
push_ivar 8
push_int 2
op /
op +
store_ivar 33
push_ivar 32
store_ivar 35
push_int 0
store_ivar 13
push_const.b idx:16
push_ivar 0
push_const.b idx:12
push_const.b idx:13
send.b 3 idx:9
store_ivar 41
push_const.b idx:17
send.b 0 idx:9
push_self
send.b 1 idx:18
store_ivar 45
return_self