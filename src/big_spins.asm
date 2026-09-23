; All rotating and upright poses retain 128 independently sampled columns.
spin_big_letters:
        move.w FRAME(a5),d0
        lsr.w #2,d0
        cmp.w BIGSPINPHASE(a5),d0
        beq .done
        move.w d0,BIGSPINPHASE(a5)
        bsr wait_blit
        moveq #0,d0
        move.w FRAME(a5),d0
        mulu #6,d0
        divu #HIWIDTH,d0
        swap d0
        move.w d0,BIGSCROLLX(a5)
        moveq #0,d7
.letter:
        ; Update only glyphs intersecting the 640-pixel viewport. Offscreen
        ; cached angles are refreshed before those glyphs become visible.
        move.w d7,d0
        lsl.w #7,d0
        sub.w BIGSCROLLX(a5),d0
        add.w #128,d0
        bpl.s .wrapped
        add.w #HIWIDTH,d0
.wrapped:
        cmp.w #HIWIDTH,d0
        blo.s .visible_test
        sub.w #HIWIDTH,d0
.visible_test:
        cmp.w #768,d0
        bhs .next
        move.l a4,a0
        add.l #BIG_SPIN_MAP,a0
        moveq #0,d3
        move.b (a0,d7.w),d3
        cmp.w #255,d3
        beq .next
        move.w d7,d4
        mulu #3,d4
        add.w BIGSPINPHASE(a5),d4
        and.w #31,d4
        cmp.w #16,d4
        blo.s .angle
        moveq #0,d4
.angle:
        lea BIGSPINANGLES(a5),a0
        cmp.b (a0,d7.w),d4
        beq .next
        move.b d4,(a0,d7.w)
        lsl.w #4,d3
        add.w d4,d3
        lsl.w #2,d3
        move.l a4,a2
        add.l #BIG_SPIN_INDEX,a2
        add.w d3,a2
        move.l a4,a0
        add.l #BIG_SPIN_PACKED,a0
        move.l (a2),d0
        move.l 4(a2),d1
        move.l a0,a2
        add.l d1,a2
        add.l d0,a0
        move.l GRAPHBUF(a5),a1
        move.l #640,d0
        bsr roto_decode
        move.l GRAPHBUF(a5),a0
        move.l OLD(a5),a1
        move.w d7,d0
        lsl.w #4,d0
        add.w d0,a1
        moveq #39,d6
.row:
        moveq #3,d5
.copy:
        move.l (a0)+,(a1)+
        dbra d5,.copy
        lea HI_STRIDE-16(a1),a1
        dbra d6,.row
.next:
        addq.w #1,d7
        cmp.w #BIG_TEXT_CHARS,d7
        blo .letter
        ; Refresh the source prefix at the wrapped fetch seam.
        move.l OLD(a5),a0
        move.l a0,a1
        add.l #HIWIDTH/8,a1
        moveq #39,d7
.wrap_row:
        moveq #40,d6
.wrap_word:
        move.w (a0)+,(a1)+
        dbra d6,.wrap_word
        lea HI_STRIDE-82(a0),a0
        lea HI_STRIDE-82(a1),a1
        dbra d7,.wrap_row
.done:  rts
