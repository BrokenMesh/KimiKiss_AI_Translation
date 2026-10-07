; target: Parson message argc=1 table=methods
; original-sha1: 994f301622215139bddd9cba46bcdc629ccb31c4 (518 bytes)
; reason: continuation lines after a speaker plate start at 5 cells (115 px) instead of 4 (92 px), so the English
; surname plates (Mizusawa 107 px, Satonaka/Kirishima 100 px) fit the indent. Glossary D9, D-023.
push_nils 4
push_const.b idx:171
push_temp 0
send.b 1 idx:5
store_temp 1
push_classvar.b idx:0 7
send.w 0 idx:172
pop
push_ivar 16
push_nil
not_identical
jump_if_false.l L0021
push_ivar 16
store_temp 2
jump.l L0025
L0021: push_ivar 15
store_temp 2
L0025: push_classvar.b idx:0 7
push_temp 2
send.w 1 idx:173
pop
push_ivar 13
push_nil
not_identical
push_ivar 14
push_nil
not_identical
or
jump_if_false.l L006b
push_classvar.b idx:0 7
push_int 0
send.w 1 idx:157
pop
push_ivar 14
push_nil
not_identical
jump_if_false.l L0053
push_ivar 14
store_temp 3
jump.l L0057
L0053: push_ivar 13
store_temp 3
L0057: push_classvar.b idx:0 7
push_temp 3
send.w 1 idx:153
pop
push_classvar.b idx:0 7
push_int 5  ; was 4: indent after the plate, 5 x 23 = 115 px (D9)
send.w 1 idx:174
pop
L006b: push_const.b idx:175
push_temp 0
push_ivar 8
push_temp 2
push_temp 3
send.w 4 idx:176
pop
push_ivar 17
push_int 2
identical
jump_if_false.l L0092
push_classvar.b idx:0 7
push_ivar 17
push_ivar 18
send.w 2 idx:157
pop
jump.l L009d
L0092: push_classvar.b idx:0 7
push_ivar 17
send.w 1 idx:157
pop
L009d: push_temp 1
send.w 0 idx:146
store_temp 4
L00a6: push_temp 4
push_nil
not_identical
jump_if_false.l L0205
push_temp 4
push_const.b idx:149
op <
push_temp 4
push_int 59
op >=
and
jump_if_false.l L01aa
push_temp 4
push_int 87
identical
jump_if_false.l L00ce
push_self
push_temp 1
send.w 1 idx:177
pop
jump.l L01a7
L00ce: push_temp 4
push_int 86
identical
jump_if_false.l L00e2
push_self
push_temp 1
send.w 1 idx:178
pop
jump.l L01a7
L00e2: push_temp 4
push_int 84
identical
jump_if_false.l L00f6
push_self
push_temp 1
send.w 1 idx:179
pop
jump.l L01a7
L00f6: push_temp 4
push_int 70
identical
jump_if_false.l L010a
push_self
push_temp 1
send.w 1 idx:180
pop
jump.l L01a7
L010a: push_temp 4
push_int 66
identical
jump_if_false.l L011e
push_self
push_temp 1
send.w 1 idx:181
pop
jump.l L01a7
L011e: push_temp 4
push_int 83
identical
jump_if_false.l L0132
push_self
push_temp 1
send.w 1 idx:182
pop
jump.l L01a7
L0132: push_temp 4
push_int 69
identical
jump_if_false.l L0146
push_self
push_temp 1
send.w 1 idx:183
pop
jump.l L01a7
L0146: push_temp 4
push_int 77
identical
jump_if_false.l L015a
push_self
push_temp 1
send.w 1 idx:184
pop
jump.l L01a7
L015a: push_temp 4
push_int 80
identical
jump_if_false.l L016e
push_self
push_temp 1
send.w 1 idx:185
pop
jump.l L01a7
L016e: push_temp 4
push_int 65
identical
jump_if_false.l L0182
push_self
push_temp 1
send.w 1 idx:186
pop
jump.l L01a7
L0182: push_temp 4
push_int 78
identical
jump_if_false.l L0196
push_self
push_temp 1
send.w 1 idx:187
pop
jump.l L01a7
L0196: push_temp 4
push_int 82
identical
jump_if_false.l L01a7
push_self
push_temp 1
send.w 1 idx:188
pop
L01a7: jump.l L01f9
L01aa: push_temp 4
push_const.b idx:189
identical
jump_if_false.l L01be
push_classvar.b idx:0 7
send.w 0 idx:190
pop
jump.l L01f9
L01be: push_temp 4
push_const.b idx:191
identical
jump_if_false.l L01d2
push_classvar.b idx:0 7
send.w 0 idx:192
pop
jump.l L01f9
L01d2: push_temp 4
push_const.b idx:193
identical
push_temp 4
push_const.b idx:194
identical
op |
jump_if_false.l L01ef
push_classvar.b idx:0 7
send.w 0 idx:172
push_ivar 17
send.w 1 idx:157
pop
L01ef: push_classvar.b idx:0 7
push_temp 4
send.w 1 idx:153
pop
L01f9: push_temp 1
send.w 0 idx:146
store_temp 4
jump.l L00a6
L0205: return_self
