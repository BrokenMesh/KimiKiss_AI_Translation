; target: ConfirmDialog initialize argc=7 table=methods
; original-sha1: a50798a264782d6ca525bc4eed7c75e57ea89ecd (672 bytes)
; reason: box width from pixels instead of characters x 18 (D-017). When `width` is nil, the width
;   of the longest line is taken from the built TextLineC lines (`line xOf: text length`, D-015);
;   lines after the first add one pitch, as the original character count did (it counted the break
;   character). Japanese xOf: is exactly n*pitch, so an all-Japanese message gets the same box as
;   before. The first (character-count) pass stays: it still gives the wrap width for an explicit
;   `width`, and the engine's clamp (<128 -> 96, >608 -> 576, else -32) is untouched.
; temps: 19 = max pixel width (float), 20 = width of the current line, 21 = the TextLineC just built
push_nils 15
push_const float:0.0
store_temp 19
push_temp 5
store_ivar 5
push_const.b idx:0
push_const.b idx:1
push_int 1
at
push_int 0
at
op *
send.b 0 idx:2
store_temp 7
push_const.b idx:3
push_const.b idx:1
push_int 1
at
push_int 1
at
op *
send.b 0 idx:2
push_int 3
op +
store_temp 8
push_int 0
store_temp 11
push_temp 3
push_nil
identical
jump_if_false.l L0095
push_int 0
store_temp 12
push_int 0
store_temp 9
L003c: push_temp 9
push_temp 4
send.b 0 idx:4
push_int 1
op -
op <=
jump_if_false.l L007f
push_temp 4
push_temp 9
at
store_temp 10
push_temp 10
push_int 10
identical
push_temp 10
push_const.b idx:5
identical
or
jump_if_false.l L006f
push_temp 11
push_temp 12
op <
jump_if_false.l L006b
push_temp 12
store_temp 11
L006b: push_int 0
store_temp 12
L006f: push_temp 12
push_int 1
op +
store_temp 12
push_temp 9
push_int 1
op +
store_temp 9
jump.s L003c
L007f: push_temp 11
push_temp 12
op <
jump_if_false.l L008b
push_temp 12
store_temp 11
L008b: push_temp 11
push_temp 7
op *
store_temp 11
jump.l L00ba
L0095: push_temp 3
push_const.b idx:6
op <
jump_if_false.l L00a4
push_int 96
store_temp 11
jump.l L00ba
L00a4: push_temp 3
push_const.b idx:7
op >
jump_if_false.l L00b3
push_const.b idx:8
store_temp 11
jump.l L00ba
L00b3: push_temp 3
push_int 32
op -
store_temp 11
L00ba: push_temp 11
push_temp 7
op /
store_temp 13
push_const.b idx:9
send.b 0 idx:10
store_temp 14
push_const.b idx:11
send.b 0 idx:10
store_temp 15
push_int 0
store_temp 9
L00d3: push_temp 9
push_temp 4
send.b 0 idx:4
push_int 1
op -
op <=
jump_if_false.l L0142
push_temp 4
push_temp 9
at
store_temp 10
push_temp 10
push_int 10
identical
push_temp 10
push_const.b idx:5
identical
or
jump_if_false.l L0108
push_temp 14
push_temp 15
send.b 1 idx:12
pop
push_const.b idx:11
send.b 0 idx:10
store_temp 15
jump.l L0139
L0108: push_temp 15
send.b 0 idx:4
push_temp 13
op >=
jump_if_false.l L012f
push_temp 15
push_temp 10
send.b 0 idx:13
op +
store_temp 15
push_temp 14
push_temp 15
send.b 1 idx:12
pop
push_const.b idx:11
send.b 0 idx:10
store_temp 15
jump.l L0139
L012f: push_temp 15
push_temp 10
send.b 0 idx:13
op +
store_temp 15
L0139: push_temp 9
push_int 1
op +
store_temp 9
jump.s L00d3
L0142: push_temp 15
send.b 0 idx:4
push_int 0
op >
jump_if_false.l L0155
push_temp 14
push_temp 15
send.b 1 idx:12
pop
L0155: push_temp 14
send.b 0 idx:4
store_temp 16
push_const.b idx:9
push_temp 16
send.b 1 idx:10
store_ivar 2
push_ivar 5
push_int 0
identical
jump_if_false.l L017a
push_temp 16
push_temp 8
op *
send.b 0 idx:14
store_temp 17
jump.l L0187
L017a: push_temp 16
push_int 2
op +
push_temp 8
op *
send.b 0 idx:14
store_temp 17
L0187: push_temp 2
push_temp 17
push_temp 8
op -
push_const.b idx:15
op /
op -
store_temp 18
push_int 0
store_temp 9
L0198: push_temp 9
push_temp 16
push_int 1
op -
op <=
jump_if_false.l L01e8
push_temp 14
push_temp 9
at
send.b 0 idx:4
push_int 0
op >
jump_if_false.l L01d8
push_ivar 2
push_const.b idx:16
push_temp 0
push_int 1
op +
push_temp 1
push_temp 18
push_temp 7
push_int 0
push_int 1
send.b 6 idx:10
push_const.b idx:17
send.b 1 idx:18
push_temp 14
push_temp 9
at
send.b 1 idx:19
store_temp 21
push_temp 21
send.b 1 idx:12
pop
push_temp 21
push_temp 14
push_temp 9
at
send.b 0 idx:4
send 1 #xOf
store_temp 20
jump.s Lw
L01d8: push_const float:0.0
store_temp 20
Lw: push_temp 9
push_int 0
op >
jump_if_false.s Lnp
push_temp 20
push_temp 7
op +
store_temp 20
Lnp: push_temp 19
push_temp 20
op <
jump_if_false.s Lnm
push_temp 20
store_temp 19
Lnm: push_temp 18
push_temp 8
op +
store_temp 18
push_temp 9
push_int 1
op +
store_temp 9
jump.s L0198
L01e8: push_temp 3
push_nil
identical
jump_if_false.s Lkeep
push_temp 19
store_temp 11
Lkeep: push_const.b idx:20
push_temp 6
push_temp 11
send.b 0 idx:14
push_const.b idx:21
op /
push_temp 17
push_const.b idx:21
op /
push_temp 0
send.b 4 idx:10
store_ivar 1
push_ivar 1
push_temp 1
push_temp 2
send.b 2 idx:22
push_const.b idx:17
send.b 1 idx:18
send.b 0 idx:23
pop
push_temp 18
push_const.b idx:24
op +
store_temp 18
push_ivar 5
push_int 2
identical
jump_if_false.l L0252
push_const.b idx:25
push_temp 0
push_int 1
op +
push_temp 1
push_const.b idx:26
op -
push_temp 18
push_int 0
push_int 4
send.b 5 idx:10
store_ivar 3
push_const.b idx:25
push_temp 0
push_int 1
op +
push_temp 1
push_const.b idx:0
op +
push_temp 18
push_int 1
push_int 5
send.b 5 idx:10
store_ivar 4
jump.l L0271
L0252: push_ivar 5
push_int 1
identical
jump_if_false.l L0271
push_const.b idx:25
push_temp 0
push_int 1
op +
push_temp 1
push_const.b idx:21
op -
push_temp 18
push_int 0
push_int 16
send.b 5 idx:10
store_ivar 3
L0271: push_const.b idx:27
push_int 0
push_temp 0
send.b 2 idx:10
push_const.b idx:17
send.b 1 idx:18
store_ivar 0
push_ivar 0
push_const.b idx:17
push_const.b idx:17
push_const.b idx:28
push_const.b idx:29
send.b 4 idx:30
push_const.b idx:17
push_const.b idx:17
send.b 2 idx:22
push_const.b idx:17
push_const.b idx:17
push_const.b idx:17
send.b 3 idx:31
pop
return_self
