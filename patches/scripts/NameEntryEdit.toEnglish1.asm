; add: NameEntryEdit toEnglish argc=1 table=methods
; reason: new method. Maps what the grid types to English codes: full-width digits 0x824F-0x8258, capitals 0x8260-0x8279
; and lower case 0x8281-0x829A all by +0x301 (Ａ 0x8260 -> 0x8561 A); full-width symbols with an ASCII twin
; (space, comma, period, ? ! - & quotes brackets ...) through the @EN_SYMBOLS table (0x8140-0x819E);
; every other code, English codes included, is returned unchanged. D-016.
push_nils 1
push_temp 0
push_const int:0x824f
op >=
push_temp 0
push_const int:0x8258
op <=
and
jump_if_false Lend2
push_temp 0
push_const int:0x301
op +
return_top
Lend2:
push_temp 0
push_const int:0x8260
op >=
push_temp 0
push_const int:0x8279
op <=
and
jump_if_false Lend3
push_temp 0
push_const int:0x301
op +
return_top
Lend3:
push_temp 0
push_const int:0x8281
op >=
push_temp 0
push_const int:0x829a
op <=
and
jump_if_false Lend4
push_temp 0
push_const int:0x301
op +
return_top
Lend4:
push_temp 0
push_const int:0x8140
op >=
push_temp 0
push_const int:0x819e
op <=
and
jump_if_false Lend5
push_const @EN_SYMBOLS
push_temp 0
push_const int:0x8140
op -
at
store_temp 1
push_temp 1
push_int 0
not_identical
jump_if_false Lend6
push_temp 1
return_top
Lend6:
Lend5:
push_temp 0
return_top
return_self
