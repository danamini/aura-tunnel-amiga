; Bounded independent-pose LZSS decoder. See tools/roto_codec.py.
; Inputs: a0 compressed start, a2 compressed end (exclusive),
;         a1 output start, d0 output byte count (3200 for an 80-row pose).
; Returns d0=0 success or -1 malformed stream; a0/a1 advance.
; Preserves d1-d7/a2-a4. Source pairs may be odd-aligned, so read bytes.
; Decode only when the pose changes, into a buffer NOT currently used by DMA.
roto_decode:
        movem.l d1-d7/a2-a4,-(sp)
        move.l a1,a3
        move.l a1,a4
        add.l d0,a4
        move.l a2,d6            ; retain source end without per-match stack I/O
.group:
        cmp.l a4,a1
        beq .complete
        cmp.l a2,a0
        bhs .bad
        moveq #0,d1
        move.b (a0)+,d1
        moveq #7,d7
.token:
        lsr.b #1,d1
        bcc.s .match
        cmp.l a2,a0
        bhs.s .bad
        move.b (a0)+,(a1)+
        bra.s .next
.match:
        move.l a0,d2
        addq.l #2,d2
        cmp.l a2,d2
        bhi.s .bad
        moveq #0,d2
        move.b (a0)+,d2
        lsl.w #8,d2
        move.b (a0)+,d2
        moveq #0,d3
        move.w d2,d3
        and.w #15,d3
        addq.w #3,d3
        lsr.w #4,d2
        addq.w #1,d2
        move.l a1,d4
        sub.l d2,d4
        cmp.l a3,d4
        blo.s .bad
        move.l a1,d5
        add.l d3,d5
        cmp.l a4,d5
        bhi.s .bad
        move.l d4,a2
        ; Each instruction below occupies one word. Enter the last N copies
        ; directly: matches remain sequential, including distance-one runs.
        ; Bounds were checked for the complete match before entering here.
        add.w d3,d3
        neg.w d3
        jmp .copy_end(pc,d3.w)
        rept 18
        move.b (a2)+,(a1)+
        endr
.copy_end:
        move.l d6,a2
.next:
        cmp.l a4,a1
        beq.s .complete
        dbra d7,.token
        bra .group
.complete:
        cmp.l a2,a0
        bne.s .bad
        moveq #0,d0
        bra.s .return
.bad:
        moveq #-1,d0
.return:
        movem.l (sp)+,d1-d7/a2-a4
        rts
