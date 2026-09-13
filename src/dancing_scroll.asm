; Individual 16-pixel letters: masked by transparent source padding, OR-blitted
; into both playfield planes. Cached rotations borrow inactive hires buffers.
dancing_scroll:
        tst.w DANCEREADY(a5)
        bne.s .ready
        bsr wait_blit
        move.l a4,a0
        add.l #DANCE_PACKED,a0
        move.l a0,a2
        add.l #DANCE_PACKED_SIZE,a2
        move.l BASE(a5),a1
        add.l #hires_a-start,a1
        move.l #DANCE_RAW_SIZE,d0
        bsr roto_decode
        move.w #1,DANCEREADY(a5)
.ready:
        moveq #0,d7
.letter:
        movem.l d7,-(sp)
        moveq #0,d0
        move.w FRAME(a5),d0
        mulu #3,d0
        lsr.l #1,d0
        divu #12,d0
        move.l d0,d6
        swap d6
        and.l #$ffff,d0
        add.w d7,d0
        divu #DANCE_CHARS,d0
        swap d0
        and.l #$ffff,d0
        move.l a4,a0
        add.l #DANCE_MESSAGE,a0
        moveq #0,d5
        move.b (a0,d0.w),d5
        move.w d7,d4
        mulu #12,d4
        sub.w d6,d4
        bmi .next
        cmp.w #303,d4
        bhi .next
        ; Slow amplitude breathing plus a drifting spatial frequency.
        move.l a4,a3
        add.l #SINE,a3
        move.w FRAME(a5),d0
        lsr.w #2,d0
        and.w #255,d0
        add.w d0,d0
        move.w (a3,d0.w),d6
        add.w #26,d6             ; amplitude 10..42 pixels
        add.w #128,d0
        and.w #510,d0
        move.w (a3,d0.w),d1
        add.w #16,d1
        lsr.w #2,d1
        add.w #12,d1             ; phase spacing 12..20 per letter
        mulu d7,d1
        move.w FRAME(a5),d0
        mulu #6,d0
        neg.w d0
        add.w d1,d0
        and.w #255,d0
        add.w d0,d0
        move.w (a3,d0.w),d1
        muls d6,d1
        asr.l #4,d1
        add.w #120,d1
        move.w d1,d6
        ; A short travelling roll; each letter spends most time upright.
        move.w FRAME(a5),d0
        lsr.w #2,d0
        move.w d7,d1
        mulu #3,d1
        add.w d1,d0
        and.w #127,d0
        cmp.w #16,d0
        blo.s .angle
        moveq #0,d0
.angle:
        lsl.w #4,d5
        add.w d0,d5
        lsl.l #5,d5
        move.l BASE(a5),a2
        add.l #hires_a-start,a2
        add.l d5,a2
        bsr dance_letter
.next:
        movem.l (sp)+,d7
        addq.w #1,d7
        cmp.w #27,d7
        blo .letter
        rts

; a2 padded16x16 glyph; d4 x, d6 y. Both planes use same source for colour3.
dance_letter:
        ; Expand one compact rotation into a padded DMA mask after the prior
        ; blit finishes. Sixteen angles occupy the same cache as eight padded.
        bsr wait_blit
        move.l MASKBUF(a5),a0
        moveq #15,d0
.pad:
        move.w (a2)+,(a0)+
        clr.w (a0)+
        dbra d0,.pad
        move.l MASKBUF(a5),a2
        move.l BACK(a5),a3
        mulu #40,d6
        add.l d6,a3
        move.w d4,d0
        lsr.w #4,d0
        add.w d0,d0
        add.w d0,a3
        and.w #15,d4
        ror.w #4,d4
        or.w #$0bfa,d4
        moveq #1,d5
.plane:
        bsr wait_blit
        move.w d4,$40(a6)
        clr.w $42(a6)
        move.l #-1,$44(a6)
        clr.w $64(a6)
        move.w #36,$60(a6)
        move.w #36,$66(a6)
        move.l a2,$50(a6)
        move.l a3,$48(a6)
        move.l a3,$54(a6)
        move.w #16*64+2,$58(a6)
        lea PLANE(a3),a3
        dbra d5,.plane
        rts
