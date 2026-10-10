; target: MatchHistory checkLose4 argc=0 table=methods
; original-sha1: b3fa13e07b884bfef89648c9830dcbf9578a45bc
; reason: Fewer Rejections: she does not walk off after 4 misses in a row; the talk runs to its normal end.
; Easy mode (D-038): the lines up to `orig:` are new; from `orig:` on it is the original method
; (70 bytes, listed with tools/reinsert/scfasm.py listing()). With the flag off it runs unchanged.
push_nils 0
push_const class:GameParam
push_int 2
send 1 #easy                ; easy mode "Fewer Rejections" on?
jump_if_false orig
push_false
return_top
orig:
push_classvar.b idx:0 9
push_int 4
op >=
jump_if_false.l L0043
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
push_classvar.b idx:0 11
push_classvar.b idx:0 9
push_int 3
op -
at
push_nil
identical
and
push_classvar.b idx:0 11
push_classvar.b idx:0 9
push_int 4
op -
at
push_nil
identical
and
jump_if_false.l L0043
push_true
return_top
L0043: push_false
return_top
return_self
