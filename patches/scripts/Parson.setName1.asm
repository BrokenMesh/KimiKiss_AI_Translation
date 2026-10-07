; target: Parson setName argc=1 table=methods
; original-sha1: e62e9fcd8ad87dafb7541ab7ac4d74d5e3175fef (58 bytes)
; reason: a scene's own plate for a minor character (女の子, リョウ, 食おば, ...) was cut to its first 3 characters
; (at: 0, 1, 2), so "Girl" showed as "Gir" and a name under 3 characters would index past the end. The plate is now
; the whole string, as setDispName (D-016). nil still clears it; a non-String still leaves it unchanged. D-027.
push_nils 0
push_temp 0
push_nil
not_identical
jump_if_false Lclear
push_temp 0
push_const class:String
send 1 #isKindOf
jump_if_false Lend
push_temp 0
store_ivar 14
Lend:
jump Lret
Lclear:
push_nil
store_ivar 14
Lret:
return_self
