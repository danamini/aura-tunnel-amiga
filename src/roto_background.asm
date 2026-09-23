; Word-run decoder: roto_decode interface plus d4 = full-turn phase.
; Second half writes backwards with reversed bits, without an extra image pass.
; Long blank spans fill eight words per iteration, avoiding byte-token overhead.
roto_background_decode:
        movem.l d1-d7/a2-a4,-(sp)
        move.l d0,d6
        lsr.l #1,d6
        moveq #0,d7
        cmp.w #ROTO_BG_STEPS,d4
        blo.s .command
        moveq #1,d7
        add.l d0,a1
        move.l a4,a3
        add.l #REVERSE_BYTE,a3
.command:
        tst.w d6
        beq .complete
        move.l a0,d2
        addq.l #2,d2
        cmp.l a2,d2
        bhi .bad
        move.w (a0)+,d1
        move.w d1,d3
        and.w #$7fff,d1
        beq .bad
        sub.w d1,d6
        bcs .bad
        tst.w d3
        bmi.s .repeated
        moveq #0,d2
        move.w d1,d2
        add.w d2,d2
        move.l a0,d3
        add.l d2,d3
        cmp.l a2,d3
        bhi .bad
        subq.w #1,d1
        tst.w d7
        bne.s .literal_reverse
.literal:
        move.w (a0)+,(a1)+
        dbra d1,.literal
        bra .command
.literal_reverse:
        moveq #0,d0
        move.b (a0)+,d0
        move.b (a3,d0.w),-(a1)
        move.b (a0)+,d0
        move.b (a3,d0.w),-(a1)
        dbra d1,.literal_reverse
        bra .command
.repeated:
        move.l a0,d2
        addq.l #2,d2
        cmp.l a2,d2
        bhi .bad
        move.w (a0)+,d0
        tst.w d7
        beq.s .repeat_word
        moveq #0,d2
        move.b d0,d2
        move.b (a3,d2.w),d3
        lsl.w #8,d3
        lsr.w #8,d0
        move.b (a3,d0.w),d3
        move.w d3,d0
.repeat_word:
        move.w d0,d3
        swap d0
        move.w d3,d0
        tst.w d7
        bne.s .repeat_reverse
        move.w d1,d2
        and.w #7,d2
        beq.s .blocks
        subq.w #1,d2
.tail:
        move.w d0,(a1)+
        dbra d2,.tail
.blocks:
        lsr.w #3,d1
        beq .command
        subq.w #1,d1
.fill:
        rept 4
        move.l d0,(a1)+
        endr
        dbra d1,.fill
        bra .command
.repeat_reverse:
        move.w d1,d2
        and.w #7,d2
        beq.s .reverse_blocks
        subq.w #1,d2
.reverse_tail:
        move.w d0,-(a1)
        dbra d2,.reverse_tail
.reverse_blocks:
        lsr.w #3,d1
        beq .command
        subq.w #1,d1
.reverse_fill:
        rept 4
        move.l d0,-(a1)
        endr
        dbra d1,.reverse_fill
        bra .command
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
