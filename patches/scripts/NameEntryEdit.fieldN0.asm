; add: NameEntryEdit fieldN argc=0 table=methods
; reason: new method. Slots per name field: 8 (player name) or 6 (deck name). D-016.
push_nils 0
push_int 8
push_int 2
push_ivar 0
op *
op -
return_top
return_self
