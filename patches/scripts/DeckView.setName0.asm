; target: DeckView setName argc=0 table=methods
; original-sha1: 8fe9cc463f3b6140de95f9d6f705eb4cd443f5ff (115 bytes)
; reason: deck name on the deck screen (D-017). The original puts up to 6 FontChars at a fixed 26 px pitch.
;   Now the positions come from a measuring TextLineC (pitch 26, scale 1.0) through `xOf:` (D-015), so
;   English is proportional. The 6-character cut becomes a pixel cut: characters are dropped from the end
;   while the line is wider than 156 px (6 x 26). For Japanese xOf: i is i*26, so the cut is still 6
;   characters and each glyph lands where i*26 - n*13 + 13 put it. The glyphs stay plain FontChars in
;   `name` (openName/closeName/change use their zoom/fade); the measuring line's own glyphs are destroyed.
; temps: 0 = deck name, 1 = n, 2 = i, 3 = measuring TextLineC, 4 = width of the n characters
        push_nils 5
        push_self
        send 0 #clrName
        pop
        push_const class:Vector
        push_int 6
        send 1 #new
        store_ivar 9
        push_const class:WadaiParam
        send 0 #getDeckName
        store_temp 0
        push_const class:TextLineC
        push_ivar 6
        push_int 1
        op +
        push_const float:0.0
        push_const float:50.0
        push_int 26
        push_int 0
        push_int 2
        send 6 #new
        store_temp 3
        push_temp 3
        push_temp 0
        send 1 #setText
        pop
        push_temp 0
        send 0 #length
        store_temp 1
cut:
        push_temp 3
        push_temp 1
        send 1 #xOf
        push_const float:156.0
        op >
        jump_if_false cutdone
        push_temp 1
        push_int 1
        op -
        store_temp 1
        jump cut
cutdone:
        push_temp 3
        push_temp 1
        send 1 #xOf
        store_temp 4
        push_int 0
        store_temp 2
loop:
        push_temp 2
        push_temp 1
        op <
        jump_if_false done
        push_ivar 9
        push_const class:FontChar
        push_temp 0
        push_temp 2
        at
        push_int 0
        push_ivar 6
        push_int 1
        op +
        push_temp 3
        push_temp 2
        send 1 #xOf
        push_temp 4
        push_int 26
        op -
        push_int 2
        op /
        op -
        push_const float:50.0
        push_const float:1.0
        push_const float:1.0
        send 7 #new
        push_const float:0.0
        send 1 #setAlpha
        send 1 #put
        pop
        push_temp 2
        push_int 1
        op +
        store_temp 2
        jump loop
done:
        push_temp 3
        send 0 #destruct
        pop
        return_self
