; add: Configuration easyRowY argc=1 table=methods
; reason: Easy mode (D-038): y of row n (0..3) of the Easy Mode panel: -32 + 32 n.
push_nils 0
push_temp 0
send 0 #toFloat
push_const float:32.0
op *
push_const float:-32.0
op +
return_top
return_self
