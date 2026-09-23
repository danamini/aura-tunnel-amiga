; Filled checker panels from the same ring vertices as the line renderer.
; Q6 edge stepping uses only 68000 integer arithmetic. Span scratch borrows
; the transition mask, which is rebuilt after the scene has been rendered.
tunnel_panels:
        movem.l d0-d7/a0-a4,-(sp)
        bsr wait_blit
        move.w FRAME(a5),d4
        lsr.w #TUNNEL_TICK_SHIFT,d4
        and.w #TUNNEL_PHASES-1,d4
        mulu #TUNNEL_RINGS,d4
        lsr.w #TUNNEL_PHASE_BITS,d4
        and.w #1,d4
        lea TUNNEL_RING_BYTES*TUNNEL_FIRST_FILLED_RING(a2),a2
        moveq #TUNNEL_FIRST_FILLED_RING,d7
.ring:
        moveq #0,d6
.sector:
        move.w d6,d0
        add.w d7,d0
        add.w d4,d0
        btst #0,d0
        bne .next
        move.l MASKBUF(a5),a0
        move.w d6,d0
        add.w d0,d0
        lea 2(a2,d0.w),a1
        bsr .vertex
        addq.l #2,a1
        bsr .vertex
        lea TUNNEL_RING_BYTES(a1),a1
        bsr .vertex
        subq.l #2,a1
        bsr .vertex
        move.l MASKBUF(a5),a0
        move.l (a0),16(a0)
        movem.l d4/d6-d7/a2,-(sp)
        bsr fill_tunnel_quad
        movem.l (sp)+,d4/d6-d7/a2
.next:
        addq.w #1,d6
        cmp.w #TUNNEL_SECTORS,d6
        blo .sector
        lea TUNNEL_RING_BYTES(a2),a2
        addq.w #1,d7
        cmp.w #TUNNEL_RINGS-1,d7
        blo .ring
        ; One descending exclusive area fill expands all parity edges.
        bsr wait_blit
        move.l #$09f00012,$40(a6)
        move.l #-1,$44(a6)
        clr.w $64(a6)
        clr.w $66(a6)
        move.l BACK(a5),d0
        add.l #PLANE+198*40-2,d0
        move.l d0,$50(a6)
        move.l d0,$54(a6)
        move.w #172*64+20,$58(a6)
        movem.l (sp)+,d0-d7/a0-a4
        rts
.vertex:
        moveq #0,d0
        move.b (a1),d0
        add.w d0,d0
        move.w d0,(a0)+
        moveq #0,d0
        move.b 1(a1),d0
        lsr.w #1,d0
        move.w d0,(a0)+
        rts

; Emit each non-horizontal edge directly as parity crossings. The upper
; endpoint is included and the lower endpoint excluded: shared vertices must
; contribute once, otherwise XOR area filling opens seams on their rows.
; Two display rows share one crossing, leaving the expensive broad fill to
; Agnus. No per-polygon span clear/min/max array or second row pass is needed.
fill_tunnel_quad:
        move.l MASKBUF(a5),a2
        moveq #3,d5
.edge:
        move.w (a2),d0
        move.w 2(a2),d1
        move.w 4(a2),d2
        move.w 6(a2),d3
        cmp.w d1,d3
        beq.s .edge_next
        bgt.s .ordered
        exg d0,d2
        exg d1,d3
.ordered:
        sub.w d1,d3
        sub.w d0,d2
        ext.l d2
        lsl.l #6,d2
        divs d3,d2
        lsl.w #6,d0
        ; Sample at the half-row centre, not at a polygon corner.
        move.w d2,d4
        asr.w #1,d4
        add.w d4,d0
        add.w #32,d0
        mulu #80,d1
        move.l BACK(a5),a3
        add.l #PLANE,a3
        add.l d1,a3
        subq.w #1,d3
.scan:
        move.w d0,d4
        asr.w #6,d4
        move.w d4,d1
        not.w d1
        lsr.w #3,d4
        ; Dynamic memory bit numbers are implicitly modulo eight on 68000.
        lea (a3,d4.w),a0
        bchg d1,(a0)
        bchg d1,40(a0)
        add.w d2,d0
        lea 80(a3),a3
        dbra d3,.scan
.edge_next:
        addq.l #4,a2
        dbra d5,.edge
        rts
