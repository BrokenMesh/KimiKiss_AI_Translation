; target: TopicPlayer getRemainder argc=0 table=methods2
; original-sha1: b18ba87235518b00ba9964efcb34741ac2be3506
; reason: Easy mode (D-038) "More Tries": the day's topic deck (dealt every evening) limits how much
;   the player can talk; a *_MST encounter script refuses a conversation when getRemainder is 0.
;   With the flag on, a used-up deck is dealt again (setDeck) and counted once more.
;   Flag off: the original count. Class side: ivar 6 = curDeck, 7 = deckPtr.
push_nils 2
push_ivar 6
push_nil
identical
jump_if_false count
push_int 0
return_top
count: push_int 0
store_temp 0
push_ivar 7
store_temp 1
L1: push_temp 1
push_ivar 6
send 0 #length
push_int 1
op -
op <=
jump_if_false L2
push_ivar 6
push_temp 1
at
push_int 0
op >
jump_if_false L3
push_temp 0
push_int 1
op +
store_temp 0
L3: push_temp 1
push_int 1
op +
store_temp 1
jump L1
L2: push_temp 0
push_int 0
op <=
jump_if_false ret
push_ivar 7
push_int 0
op >
jump_if_false ret
push_const class:GameParam
push_int 8
send 1 #easy
jump_if_false ret
push_self
send 0 #setDeck
pop
push_self
send 0 #getRemainder
return_top
ret: push_temp 0
return_top
return_self
