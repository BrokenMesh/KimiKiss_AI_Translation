; target: MatchHistory checkLose3 argc=0 table=methods
; original-sha1: 1102b66929af6119b01bca95bf393642b584a11f
; reason: Fewer Rejections: no "bored" reaction (3 misses in a row: -12 tension and a note).
; Easy mode (D-038): the lines up to `orig:` are new; from `orig:` on it is the original method
; (73 bytes, listed with tools/reinsert/scfasm.py listing()). With the flag off it runs unchanged.
push_nils 0
push_const class:GameParam
push_int 2
send 1 #easy                ; easy mode "Fewer Rejections" on?
jump_if_false orig
push_false
return_top
orig:
push_classvar.b idx:0 9
push_int 2
op >=
jump_if_false.l L0046
push_classvar.b idx:0 11
push_classvar.b idx:0 9
push_int 1
op -
at
push_nil
identical
push_classvar.b idx:0 11
push_classvar.b idx:0 9
push_int 2
op -
at
push_nil
identical
and
jump_if_false.l L0046
push_classvar.b idx:0 9
push_int 2
identical
jump_if_false.l L0035
push_true
return_top
jump.l L0046
L0035: push_classvar.b idx:0 11
push_classvar.b idx:0 9
push_int 3
op -
at
push_nil
not_identical
jump_if_false.l L0046
push_true
return_top
L0046: push_false
return_top
return_self
