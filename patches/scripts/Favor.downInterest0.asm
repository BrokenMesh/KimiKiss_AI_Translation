; target: Favor downInterest argc=0 table=methods
; original-sha1: 8a9e2ce012e55c7b6337cb346be110a88e08c4e3
; reason: No Losses: the nightly interest -1 is skipped (fInter := true makes the original skip it);
;   the nightly tension and panic decay stay.
; Easy mode (D-038): the lines up to `orig:` are new; from `orig:` on it is the original method
; (48 bytes, listed with tools/reinsert/scfasm.py listing()). With the flag off it runs unchanged.
push_nils 0
push_const class:GameParam
push_int 1
send 1 #easy                ; easy mode "No Losses" on?
jump_if_false orig
push_true
store_ivar 12               ; fInter
orig:
push_self
push_self
send.b 0 idx:19
push_int 2
op /
send.b 1 idx:34
pop
push_self
push_int -2
send.b 1 idx:37
pop
push_ivar 12
push_false
identical
push_ivar 11
push_int 0
op >
and
jump_if_false.l L0029
push_ivar 11
push_int 1
op -
store_ivar 11
L0029: push_false
store_ivar 12
push_ivar 11
return_top
return_self
