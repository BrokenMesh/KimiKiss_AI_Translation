; add: NameEntryEdit slots argc=0 table=methods
; reason: new method. Number of name slots: 16 (8 surname + 8 given name) for the player name (mode 0),
; 6 for the deck name (mode 1). D-016.
push_nils 0
push_int 16
push_int 10
push_ivar 0
op *
op -
return_top
return_self
