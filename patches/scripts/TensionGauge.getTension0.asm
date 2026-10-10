; target: TensionGauge getTension argc=0 table=methods
; original-sha1: e24b1e407a8a612abf240be619b82d348993de47
; reason: Fewer Rejections: the conversation checks see the gauge 32 higher: walk-home and kiss need 68
;   instead of 100, and the "flustered" thresholds drop by 32. The gauge picture is unchanged.
; Easy mode (D-038): the lines up to `orig:` are new; from `orig:` on it is the original method
; (7 bytes, listed with tools/reinsert/scfasm.py listing()). With the flag off it runs unchanged.
push_nils 0
push_const class:GameParam
push_int 2
send 1 #easy                ; easy mode "Fewer Rejections" on?
jump_if_false orig
push_classvar class:TensionGauge 8   ; tension
push_int 32
op +
return_top
orig:
push_classvar.b idx:2 8
return_top
return_self
