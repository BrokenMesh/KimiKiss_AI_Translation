; add: NameEntryEdit fieldW argc=0 table=methods
; reason: new method. Width of one name field in px: 82 for each of the two player-name fields
; (x -44..38 and 46..128, between the two diamonds), 144 for the deck name (6 cells, as before). D-016.
push_nils 0
push_const float:82.0
push_const float:62.0
push_ivar 0
op *
op +
return_top
return_self
