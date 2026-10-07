; add: NameEntryEdit emptyW argc=0 table=methods
; reason: new method. Width (px at scale 1.0) reserved for an empty slot: 13 in the player name, 24 (a full cell,
; the original geometry) in the deck name. D-016.
push_nils 0
push_const float:13.0
push_const float:11.0
push_ivar 0
op *
op +
return_top
return_self
