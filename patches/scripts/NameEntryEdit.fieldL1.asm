; add: NameEntryEdit fieldL argc=1 table=methods
; reason: new method. Left edge x of name field f: -44 and 46 for the player name, -40 for the deck name. D-016.
push_nils 0
push_const float:-44.0
push_const float:4.0
push_ivar 0
op *
op +
push_const float:90.0
push_temp 0
op *
op +
return_top
return_self
