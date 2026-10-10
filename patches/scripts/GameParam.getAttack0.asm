; target: GameParam getAttack argc=0 table=methods
; original-sha1: 3a41007ded616eb64ea6e276f24fedc8be118247
; reason: More Tries: the Attack stock always shows full (atkMax), so it is available even when the flag
;   was switched on after the day's Attack was used.
; Easy mode (D-038): the lines up to `orig:` are new; from `orig:` on it is the original method
; (6 bytes, listed with tools/reinsert/scfasm.py listing()). With the flag off it runs unchanged.
push_nils 0
push_const class:GameParam
push_int 8
send 1 #easy                ; easy mode "More Tries" on?
jump_if_false orig
push_ivar 15                ; atkMax
return_top
orig:
push_ivar 16
return_top
return_self
