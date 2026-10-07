; target: NameEntryEdit getStr argc=0 table=methods
; original-sha1: 61a4b08067f9ff510b18b6cac708c8ddd6b0a952 (110 bytes)
; reason: deck name = slots 0..5 through getStr:to: (was a 110-byte copy of the same trimming loop).
push_nils 0
push_self
push_int 0
push_self
send 0 #slots
send 2 #getStr
return_top
return_self
