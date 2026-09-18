; AURA TUNNEL / A500 OCS. Position independent, disk-loaded into CHIP RAM.
; Two planar buffers, a frozen transition frame, Copper raster palettes,
; blitter copies and masks, four Paula DMA loops and four hardware meters.
        include "build/assets.i"
PLANE equ 10240
SCREEN equ 20480
FRONT equ 0
BACK equ 4
OLD equ 8
COP equ 12
TICK equ 16
ENTER equ 20
FRAME equ 24
SCENE equ 26
LAST equ 28
RENDERS equ 32
MUTE equ 36
BUTTONS equ 38
VOLUMES equ 40
SPRITES equ 48
GRAPHBUF equ 52
GX equ 56
GY equ 58
HORIZON equ 60
TRANS equ 64
BASE equ 68
MASKBUF equ 72
PERF equ 76
COPSPR equ 80
COPRASTER equ 84
COPMODE equ 88
COPPAL equ 92
PENDING_L equ 96
PENDING_R equ 100
LASTSCENE equ 104
RBUFPTR equ 108
BODIES equ 112
RHELD equ 114
COPEXTRA equ 116
HIBACK equ 120
HIFRONT equ 124
HICOP equ 128
LOCOP equ 132
PARABUF equ 136
PAUSED equ 140
HIWORK equ 144
COPINDEX equ 148
ROMODINDEX equ 152
ROENTRY equ 156
ROEXIT equ 160
ROMODE equ 164
GRAPHTICKS equ 166
GRAPHSTART equ 168
ROFRONT equ 172
ROBACK equ 176
ROPOSE equ 180
ROVALID equ 182
SPACEBANK equ 184
TEXTCOP equ 188
TEXTEND equ 192
TEXTMODE equ 196
TRAIN_CITY_Y equ 32
TRAINART equ 200
TRAINREADY equ 202
HIFONTREADY equ 204
DANCEREADY equ 206
BIGSPINPHASE equ 208
BIGSPINANGLES equ 212

start:
        move.l a4,d7
        move.l 4.w,a6
        jsr -150(a6)           ; SuperState before touching SR/vectors
        move.w #$2700,sr
        move.l d7,a4
        move.l a4,d0
        add.l #program_end-start+4080,d0
        move.l d0,sp
        lea state(pc),a5
        move.l a4,BASE(a5)
        lea $dff000,a6
        move.w #$7fff,$9a(a6)
        move.w #$7fff,$96(a6)
        move.w #$7fff,$9c(a6)
        lea irq(pc),a0
        move.l a0,$6c.w
        move.l a4,d0
        add.l #screen_a-start,d0
        move.l d0,FRONT(a5)
        add.l #SCREEN,d0
        move.l d0,BACK(a5)
        add.l #SCREEN,d0
        move.l d0,OLD(a5)
        move.l a4,d0
        add.l #copper-start,d0
        move.l d0,COP(a5)
        move.l a4,d0
        add.l #sprite_data-start,d0
        move.l d0,SPRITES(a5)
        move.l a4,d0
        add.l #graph_data-start,d0
        move.l d0,GRAPHBUF(a5)
        move.l a4,d0
        add.l #horizon_data-start,d0
        move.l d0,HORIZON(a5)
        move.l a4,d0
        add.l #mask_data-start,d0
        move.l d0,MASKBUF(a5)
        move.l a4,d0
        add.l #perf_data-start,d0
        move.l d0,PERF(a5)
        add.l #assets-start,a4
        move.l BASE(a5),d0
        add.l #right_fighter_data-start,d0
        move.l d0,RBUFPTR(a5)
        move.l BASE(a5),d0
        add.l #hires_a-start,d0
        move.l d0,HIBACK(a5)
        add.l #5760,d0
        move.l d0,HIFRONT(a5)
        move.l BASE(a5),d0
        add.l #parallax_data-start,d0
        move.l d0,PARABUF(a5)
        move.l BASE(a5),d0
        add.l #hires_work-start,d0
        move.l d0,HIWORK(a5)
        move.l BASE(a5),d0
        add.l #copper_index-start,d0
        move.l d0,COPINDEX(a5)
        add.l #208,d0
        move.l d0,ROMODINDEX(a5)
        move.l BASE(a5),d0
        add.l #roto_a-start,d0
        move.l d0,ROFRONT(a5)
        add.l #3200,d0
        move.l d0,ROBACK(a5)
        bsr build_copper
        clr.w MUTE(a5)
        move.w #1,BODIES(a5)
        move.w #1,TRAINART(a5)
        bsr init_audio
        move.l COP(a5),$80(a6)
        clr.w $88(a6)
        move.w #$83ef,$96(a6)   ; master, bitplanes, Copper, blitter, sprites, audio
        move.w #$c020,$9a(a6)   ; VBL only; sound and time never follow render speed
        move.w #$2000,sr
        move.w #$ffff,LASTSCENE(a5)
        move.w #$ffff,TRANS(a5)
        bsr scene_init
main:
        move.l TICK(a5),d0
        sub.l ENTER(a5),d0
        move.w d0,FRAME(a5)
        moveq #0,d1
        move.w SCENE(a5),d1
        add.w d1,d1
        move.l a4,a0
        add.l #DURATIONS,a0
        cmp.w (a0,d1.w),d0
        blo.s .render
        bsr next_scene
.render:
        bsr buttons
        bsr keyboard
        bsr clear_back
        bsr draw_common
        move.w SCENE(a5),d0
        add.w d0,d0
        lea dispatch(pc),a0
        move.w (a0,d0.w),d0
        jsr (a0,d0.w)
        bsr draw_fps
        bsr transition
        bsr wait_blit
        move.l TICK(a5),d0
.wait:
        cmp.l TICK(a5),d0
        beq.s .wait
        move.l BACK(a5),d0
        move.l FRONT(a5),BACK(a5)
        move.l d0,FRONT(a5)
        move.l HIBACK(a5),d0
        move.l HIFRONT(a5),HIBACK(a5)
        move.l d0,HIFRONT(a5)
        bsr publish_scene
        addq.l #1,RENDERS(a5)
        cmp.w #40,FRAME(a5)
        bls.s .unmeasured
        move.w SCENE(a5),d0
        lsl.w #3,d0
        move.l PERF(a5),a0
        addq.l #1,(a0,d0.w)
.unmeasured:
        bsr meters
        bra main

dispatch:
        dc.w briefing-dispatch,tunnel-dispatch,roto-dispatch,snake-dispatch
        dc.w bigscroll-dispatch,cubes-dispatch,runner-dispatch,space-dispatch
        dc.w graphs-dispatch,train-dispatch

irq:
        movem.l d0-d7/a0-a6,-(sp)
        lea state(pc),a5
        lea $dff000,a6
        move.w $1e(a6),d0
        btst #5,d0
        beq.s .end
        move.w #$20,$9c(a6)
        move.w #$20,$9c(a6)
        addq.l #1,TICK(a5)
        tst.w PAUSED(a5)
        beq.s .running
        addq.l #1,ENTER(a5)
.running:
        move.l BASE(a5),a4
        add.l #assets-start,a4
        bsr music
        move.l TICK(a5),d0
        sub.l ENTER(a5),d0
        cmp.l #40,d0
        bls.s .end
        move.w SCENE(a5),d0
        lsl.w #3,d0
        move.l PERF(a5),a0
        addq.l #1,4(a0,d0.w)
.end:
        movem.l (sp)+,d0-d7/a0-a6
        rte

wait_blit:
        tst.w 2(a6)            ; required first access on old Agnus
.wait:  btst #6,2(a6)
        bne.s .wait
        rts

; A->D rectangle: a0 source, a1 dest, d0 words, d1 rows, d2/d3 modulos.
copy_inverted:
        bsr wait_blit
        move.l #$090f0000,$40(a6)
        bra.s copy_config
copy:
        bsr wait_blit
        move.l #$09f00000,$40(a6)
copy_config:
        move.l #-1,$44(a6)
        move.w d2,$64(a6)
        move.w d3,$66(a6)
        move.l a0,$50(a6)
        move.l a1,$54(a6)
        lsl.w #6,d1
        or.w d0,d1
        move.w d1,$58(a6)
        rts

clear_back:
        bsr wait_blit
        move.l #$01000000,$40(a6)
        clr.w $66(a6)
        move.l BACK(a5),$54(a6)
        move.w #$8014,$58(a6)
        rts

draw_common:
        move.w SCENE(a5),d0
        mulu #320,d0
        move.l a4,a0
        add.l #HEADERS,a0
        add.l d0,a0
        move.l BACK(a5),a1
        add.l #320,a1
        moveq #20,d0
        moveq #8,d1
        moveq #0,d2
        moveq #0,d3
        bsr copy
        move.l a4,a0
        add.l #FOOTER,a0
        cmp.w #6,SCENE(a5)
        bne.s .train_help
        move.l a4,a0
        add.l #RUN_HELP,a0
        bra.s .footer
.train_help:
        cmp.w #9,SCENE(a5)
        bne.s .footer
        move.l a4,a0
        add.l #TRAIN_HELP,a0
.footer:
        move.l BACK(a5),a1
        add.l #8000,a1
        moveq #20,d0
        moveq #8,d1
        bsr copy
        move.l a4,a0
        add.l #HUD_ON,a0
        tst.w MUTE(a5)
        beq.s .hud
        add.l #640,a0
.hud:
        move.l BACK(a5),a1
        add.l #8480,a1
        moveq #20,d0
        moveq #16,d1
        bra copy

draw_fps:
        bsr wait_blit
        move.w SCENE(a5),d0
        lsl.w #3,d0
        move.l PERF(a5),a0
        add.w d0,a0
        move.l (a0),d0
        move.l 4(a0),d1
        beq.s .none
        ; Keep the quotient safe across many hours of repeated shows.
.scale:
        cmp.l #60000,d1
        blo.s .calc
        lsr.l #1,d0
        lsr.l #1,d1
        bra.s .scale
.calc:
        mulu #50,d0
        divu d1,d0
        and.l #$ffff,d0
        cmp.w #50,d0
        bls.s .digits
        moveq #50,d0
        bra.s .digits
.none:  moveq #0,d0
.digits:
        divu #10,d0
        move.l d0,d6
        and.w #$ffff,d0
        move.l BACK(a5),a1
        lea 8677(a1),a1
        bsr decimal_digit
        move.l d6,d0
        swap d0
        addq.l #1,a1
decimal_digit:
        and.l #$ffff,d0
        add.w #16,d0
        lsl.w #3,d0
        move.l a4,a0
        add.w d0,a0
        moveq #7,d7
        move.l a1,a2
.row:
        move.b (a0)+,(a2)
        lea 40(a2),a2
        dbra d7,.row
        rts

briefing:
        move.l a4,a2
        add.l #BRIEF,a2
        move.l BACK(a5),a3
        add.l #1600,a3
        moveq #0,d6
.line:
        move.w FRAME(a5),d0
        sub.w d6,d0
        ble.s .done
        lsr.w #1,d0
        cmp.w #20,d0
        bls.s .width
        moveq #20,d0
.width:
        tst.w d0
        beq.s .done
        moveq #40,d2
        sub.w d0,d2
        sub.w d0,d2
        move.w d2,d3
        moveq #8,d1
        move.l a2,a0
        move.l a3,a1
        bsr copy
        add.l #960,a2
        add.l #960,a3
        add.w #36,d6
        cmp.w #216,d6
        blo.s .line
.done:
        rts

tunnel:
        move.w FRAME(a5),d0
        and.w #127,d0
        lsl.w #2,d0
        move.l a4,a0
        add.l #TUNNEL_INDEX,a0
        move.l (a0,d0.w),d0
        move.l a4,a2
        add.l #TUNNEL,a2
        add.l d0,a2
        bsr tunnel_panels
        bsr wait_blit
        move.l #-1,$44(a6)
        move.w #40,$60(a6)
        move.w #40,$66(a6)
        move.l a2,-(sp)
        moveq #9,d7
.ring:
        ; Filled checker boundaries already describe the middle rings.
        ; Keep only distant outlines; near walls pass beyond the viewport.
        cmp.w #7,d7
        bhs.s .outline
        lea 20(a2),a2
        bra .ring_next
.outline:
        move.w (a2)+,-(sp)
        move.w #$ffff,d5
        moveq #7,d6
.edge:
        moveq #0,d4
        cmp.w #2,(sp)
        bne.s .bright
        move.w #PLANE,d4
.bright:
        moveq #0,d0
        moveq #0,d1
        moveq #0,d2
        moveq #0,d3
        move.b (a2),d0
        add.w d0,d0
        move.b 1(a2),d1
        move.b 2(a2),d2
        add.w d2,d2
        move.b 3(a2),d3
        bsr blitter_line
        cmp.w #3,(sp)
        bne.s .one
        bsr wait_blit
        moveq #0,d0
        moveq #0,d1
        move.b (a2),d0
        add.w d0,d0
        move.b 1(a2),d1
        bsr point
.one:
        addq.l #2,a2
        dbra d6,.edge
        addq.l #2,a2
        addq.l #2,sp
.ring_next:
        dbra d7,.ring
        move.l (sp)+,a2
        rts

        include "src/tunnel_fill.asm"

; OCS line DMA. Endpoints d0/d1 -> d2/d3; d4 plane byte offset,
; d5 texture. Preserve stream counters; endpoints are scratch registers.
blitter_line:
        movem.l d6-d7,-(sp)
        bsr wait_blit
        move.l BACK(a5),a0
        add.w d4,a0
        move.w d1,d4
        mulu #40,d4
        add.l d4,a0
        move.w d0,d4
        lsr.w #4,d4
        add.w d4,d4
        add.w d4,a0
        sub.w d0,d2
        sub.w d1,d3
        moveq #0,d6
        tst.w d2
        bpl.s .right
        neg.w d2
        addq.w #1,d6
.right:
        tst.w d3
        bpl.s .down
        neg.w d3
        addq.w #2,d6
.down:
        cmp.w d3,d2
        blo.s .steep
        addq.w #4,d6
        bra.s .octant
.steep:
        exg d2,d3
.octant:
        lea line_octants(pc),a1
        moveq #0,d7
        move.b (a1,d6.w),d7
        move.w d3,d4
        lsl.w #2,d4
        move.w d4,$62(a6)
        sub.w d2,d4
        sub.w d2,d4
        move.w d4,$52(a6)
        clr.w $50(a6)
        tst.w d4
        bpl.s .positive
        or.w #$40,d7
.positive:
        sub.w d2,d3
        lsl.w #2,d3
        move.w d3,$64(a6)
        and.w #15,d0
        ror.w #4,d0
        or.w #$0bca,d0
        move.w d0,$40(a6)
        move.w d7,$42(a6)
        move.w #$8000,$74(a6)
        move.w d5,$72(a6)
        move.l a0,$48(a6)
        move.l a0,$54(a6)
        addq.w #1,d2
        lsl.w #6,d2
        or.w #2,d2
        move.w d2,$58(a6)
        movem.l (sp)+,d6-d7
        rts
line_octants: dc.b 1,9,5,13,17,21,25,29
        even
point_stream:
        bsr wait_blit
        move.l BACK(a5),a1
        move.w (a2)+,d7
        subq.w #1,d7
.point:
        move.w (a2)+,d0
        cmp.w #2,SCENE(a5)
        bne.s .no_bob
        move.w FRAME(a5),d2
        and.w #255,d2
        add.w d2,d2
        move.l a4,a0
        add.l #SINE,a0
        move.w (a0,d2.w),d2
        asr.w #1,d2
        muls #40,d2
        add.w d2,d0
.no_bob:
        move.b (a2)+,d1
        addq.l #1,a2
        or.b d1,(a1,d0.w)
        add.w #PLANE,d0
        or.b d1,(a1,d0.w)
        dbra d7,.point
        rts

; Decompress only a changed pose, never into the buffer being scanned out.
prepare_roto:
        move.w FRAME(a5),d4
        lsr.w #2,d4
        and.w #63,d4
        tst.w ROVALID(a5)
        beq.s .decode
        cmp.w ROPOSE(a5),d4
        beq.s .done
.decode:
        move.w d4,-(sp)
        lsl.w #2,d4
        move.l a4,a3
        add.l #ROTO_INDEX,a3
        move.l a4,a0
        add.l #ROTO_COMPRESSED,a0
        move.l a0,a2
        add.l (a3,d4.w),a0
        add.l 4(a3,d4.w),a2
        move.l ROBACK(a5),a1
        move.w #3200,d0
        bsr roto_decode
        move.w (sp)+,d4
        tst.w d0
        bne.s .done
        move.l ROFRONT(a5),d0
        move.l ROBACK(a5),ROFRONT(a5)
        move.l d0,ROBACK(a5)
        move.w d4,ROPOSE(a5)
        move.w #1,ROVALID(a5)
.done:  rts
        include "src/roto_decode.asm"

roto:
        bsr prepare_roto
        cmp.w #32,FRAME(a5)
        bhs roto_dots
roto_legacy:
        bsr prepare_roto
        move.l ROFRONT(a5),a2
        move.l BACK(a5),a3
        add.l #1280,a3
        move.w FRAME(a5),d0
        and.w #255,d0
        add.w d0,d0
        move.l a4,a0
        add.l #SINE,a0
        move.w (a0,d0.w),d0
        asr.w #1,d0
        muls #40,d0
        add.l d0,a3
        moveq #79,d7
.row:
        move.l a2,a0
        move.l a3,a1
        moveq #20,d0
        moveq #2,d1
        moveq #-40,d2
        moveq #0,d3
        bsr copy
        move.l a2,a0
        lea PLANE(a3),a1
        moveq #20,d0
        moveq #2,d1
        bsr copy_inverted
        lea 40(a2),a2
        lea 80(a3),a3
        dbra d7,.row
roto_dots:
        move.w FRAME(a5),d0
        lsr.w #2,d0
        and.w #63,d0
        lsl.w #2,d0
        move.l a4,a0
        add.l #ROTO_DOTS_INDEX,a0
        move.l (a0,d0.w),d0
        move.l a4,a2
        add.l #ROTO_DOTS,a2
        add.l d0,a2
        bra point_stream

; Generated sparse 68000 column painters keep the original per-pixel sine.
; Each source column selects straight-line ORs for its lit pixels only.
bigscroll:
        bsr prepare_hi_font
        bsr spin_big_letters
        move.l HIBACK(a5),d0
        move.l HIWORK(a5),HIBACK(a5)
        move.l d0,HIWORK(a5)
        bsr wait_blit
        move.l #$01000000,$40(a6)
        clr.w $66(a6)
        move.l HIBACK(a5),$54(a6)
        move.w #72*64+40,$58(a6)
        bsr hires_columns
        move.l HIBACK(a5),d0
        move.l HIWORK(a5),HIBACK(a5)
        move.l d0,HIWORK(a5)
        bsr stretch_hires
        bra stars
prepare_hi_font:
        tst.w HIFONTREADY(a5)
        bne.s .done
        bsr wait_blit
        move.l a4,a0
        add.l #HI_BITMAP_PACKED,a0
        move.l a0,a2
        add.l #HI_BITMAP_PACKED_SIZE,a2
        move.l OLD(a5),a1
        move.l #HI_BITMAP_SIZE,d0
        bsr roto_decode
        move.w #1,HIFONTREADY(a5)
        move.w #$ffff,BIGSPINPHASE(a5)
        lea BIGSPINANGLES(a5),a0
        moveq #6,d0
.reset_angles:
        clr.l (a0)+
        dbra d0,.reset_angles
.done:  rts

        include "src/big_spins.asm"

hires_columns:
        moveq #0,d5
        move.w FRAME(a5),d5
        mulu #6,d5
        divu #HIWIDTH,d5
        swap d5
        and.l #$ffff,d5
        move.w FRAME(a5),d7
        lsl.w #4,d7
        neg.w d7
        and.w #2047,d7
        moveq #0,d6
        move.l OLD(a5),a2
        move.l a4,a3
        add.l #HI_WAVE_RUNS,a3
.group:
        move.w (a3,d7.w),d0
        move.w #640,d1
        sub.w d6,d1
        cmp.w d1,d0
        bls.s .length
        move.w d1,d0
.length:
        move.w d0,d4
        move.w 2(a3,d7.w),d1
        movem.l d4-d7/a2-a3,-(sp)
        bsr blit_wave_group
        movem.l (sp)+,d4-d7/a2-a3
        add.w d4,d6
        lsl.w #1,d4
        add.w d4,d7
        and.w #2047,d7
        cmp.w #640,d6
        blo.s .group
        rts

; Exact equal-height runs from the sine table. A repeats a short word mask;
; B is shifted text; C preserves neighbouring columns at different heights.
blit_wave_group:
        bsr wait_blit
        move.w d0,d7
        move.l HIBACK(a5),a1
        add.w d1,a1
        move.w d6,d2
        and.w #15,d2
        move.w d6,d3
        lsr.w #4,d3
        add.w d3,d3
        add.w d3,a1
        add.w d6,d5
        move.w d5,d4
        and.w #15,d5
        lsr.w #4,d4
        add.w d4,d4
        add.w d4,a2
        move.w d2,d6
        sub.w d5,d6
        moveq #0,d4
        tst.w d6
        bpl.s .shift
        add.w #16,d6
        moveq #1,d4
        subq.l #2,a1
.shift:
        move.w d2,d5
        add.w d7,d5
        add.w #15,d5
        lsr.w #4,d5
        move.w d5,d3
        add.w d4,d3
        move.l MASKBUF(a5),a0
        tst.w d4
        beq.s .first
        clr.w (a0)+
.first:
        moveq #-1,d0
        lsr.w d2,d0
        move.w d0,(a0)+
        subq.w #1,d5
        beq.s .last
        subq.w #1,d5
.full:
        move.w #$ffff,(a0)+
        dbra d5,.full
.last:
        add.w d7,d2
        and.w #15,d2
        beq.s .setup
        moveq #16,d0
        sub.w d2,d0
        moveq #-1,d1
        lsl.w d0,d1
        and.w d1,-2(a0)
.setup:
        move.w #$0fca,$40(a6)
        ror.w #4,d6
        move.w d6,$42(a6)
        move.l #-1,$44(a6)
        move.l MASKBUF(a5),$50(a6)
        move.l a2,$4c(a6)
        move.l a1,$48(a6)
        move.l a1,$54(a6)
        move.w d3,d0
        add.w d0,d0
        neg.w d0
        move.w d0,$64(a6)
        move.w d0,d1
        add.w #HI_STRIDE,d1
        move.w d1,$62(a6)
        add.w #80,d0
        move.w d0,$60(a6)
        move.w d0,$66(a6)
        or.w #HI_GLYPH_HEIGHT*64,d3
        move.w d3,$58(a6)
        rts

stretch_hires:
        move.w FRAME(a5),d0
        lsr.w #1,d0
        and.w #63,d0
        add.w d0,d0
        move.l a4,a0
        add.l #HI_STRETCH_INDEX,a0
        moveq #0,d1
        move.w (a0,d0.w),d1
        move.l a4,a2
        add.l #HI_STRETCH,a2
        add.l d1,a2
.run:
        move.w (a2)+,d0
        cmp.w #$ffff,d0
        beq.s .done
        move.l HIWORK(a5),a0
        cmp.w #$fffe,d0
        bne.s .source
        move.l a4,a0
        add.l #ZERO_ROW,a0
        bra.s .dest
.source:
        add.w d0,a0
.dest:
        move.l HIBACK(a5),a1
        add.w (a2)+,a1
        move.w (a2)+,d1
        move.w (a2)+,d2
        moveq #40,d0
        moveq #0,d3
        bsr copy
        bra.s .run
.done:  rts
snake:
        bsr stars
        bsr dancing_scroll
        move.w FRAME(a5),d0
        lsr.w #2,d0
        and.w #31,d0
        mulu #192,d0
        move.l a4,a2
        add.l #MINICUBES,a2
        add.l d0,a2
        move.w #144,d4
        moveq #44,d5
        moveq #2,d6
        moveq #16,d7
        bsr bob2
        moveq #0,d7
.orbit:
        movem.w d7,-(sp)
        move.w FRAME(a5),d0
        add.w d7,d0
        and.w #255,d0
        add.w d0,d0
        move.l a4,a0
        add.l #SINE,a0
        move.w (a0,d0.w),d4
        lsl.w #2,d4
        add.w #152,d4
        add.w #128,d0
        and.w #510,d0
        move.w (a0,d0.w),d5
        add.w #58,d5
        move.w FRAME(a5),d0
        lsr.w #1,d0
        and.w #31,d0
        mulu #192,d0
        move.l a4,a2
        add.l #MINICUBES,a2
        add.l d0,a2
        moveq #2,d6
        moveq #16,d7
        bsr bob2
        movem.w (sp)+,d7
        add.w #85,d7
        cmp.w #255,d7
        blo.s .orbit
        rts
        include "src/dancing_scroll.asm"

; Planar BOB with a transparent padding word, shifted by blitter barrel shifter.
; a2 planes, d4 x, d5 y, d6 width words (incl pad), d7 height.
bob2:
        move.l BACK(a5),a3
        mulu #40,d5
        add.l d5,a3
        move.w d4,d0
        lsr.w #4,d0
        add.w d0,d0
        add.w d0,a3
        and.w #15,d4
        ror.w #4,d4
        move.w d6,d0
        lsl.w #2,d0
        mulu d7,d0
        move.l a2,a0
        add.l d0,a0          ; third asset plane is the silhouette mask
        bsr .plane
        move.w d6,d0
        add.w d0,d0
        mulu d7,d0
        add.l d0,a2
        lea PLANE(a3),a3
.plane:
        bsr wait_blit
        move.w d4,d0
        or.w #$0fca,d0       ; mask A, image B, existing C, output D
        move.w d0,$40(a6)
        move.w d4,$42(a6)
        move.l #-1,$44(a6)
        clr.w $64(a6)
        clr.w $62(a6)
        moveq #40,d0
        sub.w d6,d0
        sub.w d6,d0
        move.w d0,$60(a6)
        move.w d0,$66(a6)
        move.l a0,$50(a6)
        move.l a2,$4c(a6)
        move.l a3,$48(a6)
        move.l a3,$54(a6)
        move.w d7,d0
        lsl.w #6,d0
        or.w d6,d0
        move.w d0,$58(a6)
        rts

cubes:
        move.w FRAME(a5),d0
        lsr.w #1,d0
        and.w #31,d0
        mulu #1152,d0
        move.l a4,a2
        add.l #CUBES,a2
        add.l d0,a2
        move.w #136,d4
        moveq #80,d5
        moveq #4,d6
        moveq #48,d7
        bsr bob2
        moveq #0,d7
.sat:
        movem.l d7,-(sp)
        move.w FRAME(a5),d0
        add.w d7,d0
        and.w #255,d0
        add.w d0,d0
        move.l a4,a0
        add.l #SINE,a0
        move.w (a0,d0.w),d4
        lsl.w #2,d4
        add.w #152,d4
        add.w #128,d0
        and.w #510,d0
        move.w (a0,d0.w),d5
        lsl.w #2,d5
        add.w #104,d5
        move.w FRAME(a5),d0
        lsr.w #1,d0
        move.w d7,d1
        lsr.w #3,d1
        add.w d1,d0
        and.w #31,d0
        mulu #192,d0
        move.l a4,a2
        add.l #MINICUBES,a2
        add.l d0,a2
        moveq #2,d6
        moveq #16,d7
        bsr bob2
        movem.l (sp)+,d7
        add.w #32,d7
        cmp.w #256,d7
        blo.s .sat
        rts

stars:
        bsr wait_blit
        move.l a4,a2
        add.l #STARS,a2
        moveq #47,d7
.star:
        moveq #0,d0
        move.w FRAME(a5),d0
        mulu 4(a2),d0
        cmp.w #9,SCENE(a5)
        bne.s .star_speed
        lsr.l #3,d0
.star_speed:
        add.w (a2),d0
        divu #320,d0
        swap d0
        move.w 2(a2),d1
        cmp.w #9,SCENE(a5)
        bne.s .space_occlusion
        tst.w TRAINART(a5)
        beq.s .old_skyline
        cmp.w #TRAIN_CITY_Y,d1
        bhs.s .hidden
.old_skyline:
        cmp.w #88,d1          ; All background stars stay above the skyline.
        bhs.s .hidden
.space_occlusion:
        cmp.w #7,SCENE(a5)
        bne.s .visible
        move.l a4,a0
        add.l #PLANET_SPANS,a0
        move.w d1,d2
        lsl.w #2,d2
        lea (a0,d2.w),a0
        cmp.w (a0),d0
        blo.s .visible
        cmp.w 2(a0),d0
        blo.s .hidden
.visible:
        cmp.w #4,SCENE(a5)
        bne.s .lowstar
        cmp.w #40,d1
        blo.s .lowstar
        cmp.w #184,d1
        blo.s .hidden
.lowstar:
        bsr point
.hidden:
        lea 6(a2),a2
        dbra d7,.star
        rts

space:
        bsr stars
        eor.w #696,SPACEBANK(a5)
        move.l RBUFPTR(a5),a1
        add.w SPACEBANK(a5),a1
        move.l a1,PENDING_L(a5)
        move.l a4,a0
        add.l #SPACE_FLYERS,a0
        move.w #35,d0
.sprite_copy:
        move.l (a0)+,(a1)+
        dbra d0,.sprite_copy
        move.l PENDING_L(a5),a1
        moveq #0,d7
.flyer:
        move.w FRAME(a5),d0
        move.w d7,d1
        addq.w #5,d1
        mulu d1,d0
        move.w d7,d1
        mulu #175,d1
        add.l d1,d0
        divu #352,d0
        swap d0
        move.w d0,d3
        add.w #113,d0
        move.w d7,d1
        mulu #70,d1
        add.w #80,d1
        move.w d0,d2
        and.w #1,d2
        lsr.w #1,d0
        lsl.w #8,d1
        or.w d1,d0
        move.w d0,(a1)
        add.w #$1000,d1
        or.w d2,d1
        move.w d1,2(a1)
        lea 72(a1),a1
        addq.w #1,d7
        cmp.w #2,d7
        blo.s .flyer
        rts

hires_star:
        cmp.w #128,d1
        blo.s .out
        cmp.w #184,d1
        bhs.s .out
        move.w d1,d2
        sub.w #128,d2
        mulu #80,d2
        move.w d0,d3
        lsr.w #2,d3
        add.w d3,d2
        move.w d0,d3
        and.w #3,d3
        add.w d3,d3
        move.l HIBACK(a5),a0
        move.w #$c0,d4
        lsr.w d3,d4
        or.b d4,(a0,d2.w)
.out:   rts

; White pixel, clipped at the scene stage. Scratch d0-d3,a0-a1.
point:
        cmp.w #320,d0
        bhs.s .out
        cmp.w #200,d1
        bhs.s .out
        cmp.w #24,d1
        blo.s .out
        move.w d0,d2
        not.w d2
        and.w #7,d2
        lsr.w #3,d0
        mulu #40,d1
        add.w d0,d1
        move.l BACK(a5),a1
        bset d2,(a1,d1.w)
        add.w #PLANE,d1
        bset d2,(a1,d1.w)
.out:   rts

runner:
        move.l a4,a2
        add.l #RUN_RIDGE,a2
        move.w FRAME(a5),d4
        lsr.w #3,d4
        and.w #511,d4
        moveq #0,d5
        moveq #56,d6
        bsr parallax_plane
        bsr wait_blit
        moveq #0,d0
        move.w FRAME(a5),d0
        lsr.w #1,d0
        divu #12,d0
        swap d0
        bsr cached_figure
        move.w FRAME(a5),d0
        lsr.w #3,d0
        and.w #7,d0
        add.w #12,d0
        bsr cached_figure
        move.w FRAME(a5),d0
        lsr.w #1,d0
        addq.w #3,d0
        and.w #7,d0
        add.w #20,d0
        bsr cached_figure
        bsr ground
        move.l a4,a0
        add.l #RUN_SPEEDS,a0
        move.l BACK(a5),a1
        add.l #1120,a1
        moveq #20,d0
        moveq #8,d1
        moveq #0,d2
        moveq #0,d3
        bsr copy
        ; Both dynamic planes make the controls and speed labels warm white.
        bsr wait_blit
        move.l BACK(a5),a0
        lea 1120(a0),a0
        move.l a0,a1
        add.l #PLANE,a1
        moveq #20,d0
        moveq #8,d1
        bsr copy
        move.l a4,a0
        add.l #RUN_HELP,a0
        move.l BACK(a5),a1
        add.l #PLANE+8000,a1
        moveq #20,d0
        moveq #8,d1
        moveq #0,d2
        moveq #0,d3
        bra copy
cached_figure:
        tst.w BODIES(a5)
        bne body_figure
        add.w d0,d0
        move.l a4,a0
        add.l #RUN_CACHE_INDEX,a0
        move.w (a0,d0.w),d0
        move.l a4,a2
        add.l #RUN_CACHE,a2
        add.w d0,a2
        move.l BACK(a5),a1
        move.w (a2)+,d7
        subq.w #1,d7
.p:
        move.w (a2)+,d0
        move.b (a2)+,d1
        addq.l #1,a2
        or.b d1,(a1,d0.w)
        dbra d7,.p
        rts

body_figure:
        lsl.w #2,d0
        move.l a4,a0
        add.l #BODY_INDEX,a0
        move.l (a0,d0.w),d0
        move.l a4,a2
        add.l #BODY_DATA,a2
        add.l d0,a2
        move.l BACK(a5),a1
.run:
        move.w (a2)+,d0
        bmi.s .done
        move.w (a2)+,d7
        subq.w #1,d7
        lea (a1,d0.w),a0
.words:
        move.w (a2)+,(a0)+
        dbra d7,.words
        bra.s .run
.done:  rts

figure:
        move.w (a2)+,d7
        subq.w #1,d7
.p:
        moveq #0,d0
        moveq #0,d1
        move.b (a2)+,d0
        move.b (a2)+,d1
        add.w d4,d0
        add.w d5,d1
        movem.w d0-d1,-(sp)
        bsr point
        movem.w (sp),d0-d1
        addq.w #1,d0
        bsr point
        movem.w (sp)+,d0-d1
        addq.w #1,d1
        bsr point
        dbra d7,.p
        rts

ground:
        cmp.w #6,SCENE(a5)
        beq.s runner_ground
        bsr wait_blit
        move.l BACK(a5),a1
        lea 7440(a1),a1
        move.w FRAME(a5),d0
        and.w #15,d0
        move.w #$f00f,d1
        ror.w d0,d1
        moveq #19,d7
.line:
        move.w d1,(a1)+
        dbra d7,.line
        rts
runner_ground:
        bsr wait_blit
        moveq #0,d6
.band:
        move.l a4,a0
        add.l #GROUND_PATTERN,a0
        move.w FRAME(a5),d0
        cmp.w #2,d6
        bhs.s .near
        lsr.w #2,d0
        add.l #128,a0
.near:
        lea ground_rows(pc),a2
        move.w d6,d1
        lsl.w #2,d1
        add.w 2(a2,d1.w),d0
        and.w #63,d0
        add.w d0,a0
        move.w d6,d1
        lsl.w #2,d1
        move.w (a2,d1.w),d1
        move.l BACK(a5),a1
        add.w d1,a1
        moveq #39,d7
.bytes:
        move.b (a0)+,d0
        move.b d0,(a1)
        cmp.w #2,d6
        blo.s .dim
        move.b d0,PLANE(a1)
.dim:
        addq.l #1,a1
        dbra d7,.bytes
        addq.w #1,d6
        cmp.w #6,d6
        blo.s .band
        rts
ground_rows: dc.w 184*40,0,186*40,17,190*40,0,192*40,11,195*40,23,197*40,30

graphs:
        cmp.w #128,FRAME(a5)
        bhs .baked
        bsr wait_blit
        tst.w GRAPHTICKS(a5)
        bne.s .calculated
        ; Measure the entire job, including buffer/horizon initialisation.
        ; VBL is independent of the render loop; round elapsed time upward.
        move.l TICK(a5),GRAPHSTART(a5)
        bsr scene_init
.evaluate:
        bsr graph_live
        cmp.w #140,GY(a5)
        bls.s .evaluate
        move.l TICK(a5),d0
        sub.l GRAPHSTART(a5),d0
        addq.w #1,d0
        move.w d0,GRAPHTICKS(a5)
.calculated:
        move.l GRAPHBUF(a5),a0
        move.l BACK(a5),a1
        add.l #2880,a1
        moveq #20,d0
        move.w #116,d1
        moveq #0,d2
        moveq #0,d3
        bsr copy
        move.l a4,a0
        add.l #GRAPH_LIVE_TITLE,a0
        bra .label
.baked:
        move.w FRAME(a5),d4
        sub.w #128,d4
        move.w d4,d5
        and.w #127,d5
        lsl.w #1,d5
        cmp.w #116,d5
        bls.s .offset
        move.w #116,d5
.offset:
        lsr.w #7,d4
        mulu #5120,d4
        move.l a4,a2
        add.l #GRAPHS,a2
        add.l d4,a2
        cmp.w #116,d5
        beq.s .incoming
        move.l GRAPHBUF(a5),a0
        tst.w d4
        beq.s .outgoing
        move.l a2,a0
        sub.l #5120,a0
.outgoing:
        move.w d5,d0
        mulu #40,d0
        add.l d0,a0
        move.l BACK(a5),a1
        add.l #2880,a1
        move.w #116,d1
        sub.w d5,d1
        moveq #20,d0
        moveq #0,d2
        moveq #0,d3
        bsr copy
.incoming:
        tst.w d5
        beq.s .slide_done
        move.l a2,a0
        move.l BACK(a5),a1
        move.w #116,d0
        sub.w d5,d0
        mulu #40,d0
        add.l #2880,d0
        add.l d0,a1
        move.w d5,d1
        moveq #20,d0
        moveq #0,d2
        moveq #0,d3
        bsr copy
.slide_done:
        move.l a4,a0
        add.l #GRAPH_BAKED_TITLE,a0
.label:
        move.l BACK(a5),a1
        add.l #960,a1
        moveq #20,d0
        moveq #8,d1
        moveq #0,d2
        moveq #0,d3
        bsr copy
        move.l a4,a0
        add.l #GRAPH_COMPARE,a0
        move.l BACK(a5),a1
        add.l #1440,a1
        moveq #20,d0
        moveq #36,d1
        bsr copy
        bsr wait_blit
        moveq #0,d0
        move.w GRAPHTICKS(a5),d0
        mulu #20,d0
        move.l BACK(a5),a1
        lea 1937(a1),a1
        bsr graph_number
        move.l #7957,d0       ; floor(159.150836 seconds * 50 Hz)
        move.w GRAPHTICKS(a5),d1
        beq.s .done
        divu d1,d0
        and.l #$ffff,d0
        move.l BACK(a5),a1
        lea 1949(a1),a1
        bsr graph_number
.done:  rts

; Four decimal digits, written right to left at the supplied screen byte.
graph_number:
        moveq #3,d5
.number:
        divu #10,d0
        move.l d0,d4
        swap d0
        bsr decimal_digit
        subq.l #1,a1
        moveq #0,d0
        move.w d4,d0
        dbra d5,.number
        rts

; Actual live fixed-point surface evaluation: exp(-r) ~= (1-r/256)^256.
; Eight Q14 squarings; no height lookup and no baked graph pixels here.
graph_live:
        cmp.w #140,GY(a5)
        bhi .done
        move.w GX(a5),d0
        sub.w #70,d0
        muls d0,d0
        move.w GY(a5),d1
        sub.w #70,d1
        muls d1,d1
        add.l d1,d0
        lsl.l #6,d0
        divu #1400,d0
        move.w #16384,d2
        sub.w d0,d2
        moveq #7,d7
.square:
        mulu d2,d2
        lsr.l #7,d2
        lsr.l #7,d2
        dbra d7,.square
        mulu #78,d2
        lsr.l #7,d2
        lsr.l #7,d2
        move.w GY(a5),d0
        mulu #181,d0
        lsr.l #8,d0
        add.w GX(a5),d0
        add.w #41,d0
        move.w GY(a5),d1
        mulu #181,d1
        lsr.l #8,d1
        add.w d2,d1
        lsr.w #1,d1          ; Same display-only half-height as Spectrum preview.
        move.w #115,d2
        sub.w d1,d2
        bmi.s .next
        cmp.w #127,d2
        bhi.s .next
        move.l HORIZON(a5),a0
        move.b (a0,d0.w),d1
        move.b d2,(a0,d0.w)  ; BASIC updates M on every candidate, even hidden ones.
        cmp.b d1,d2
        bhi.s .next
        mulu #40,d2
        move.w d0,d1
        not.w d1
        and.w #7,d1
        lsr.w #3,d0
        add.w d0,d2
        move.l GRAPHBUF(a5),a0
        bset d1,(a0,d2.w)
.next:
        addq.w #3,GX(a5)
        cmp.w #140,GX(a5)
        bls.s .done
        clr.w GX(a5)
        addq.w #5,GY(a5)
.done:  rts

; Decompress independent fighter poses into inactive DMA banks borrowed from
; the roto scene. No second full animation copy in CHIP RAM.
train:
        bsr prepare_train_art
        bsr stars
        bsr train_parallax
        moveq #0,d0
        bsr fighter_pose
        move.l BASE(a5),a1
        add.l #roto_a-start,a1
        move.l BACK(a5),d1
        cmp.l FRONT(a5),d1
        blo.s .left_bank
        lea FIGHTER_POSE(a1),a1
.left_bank:
        move.l a1,PENDING_L(a5)
        bsr decode_fighter
        moveq #1,d0
        bsr fighter_pose
        move.l BASE(a5),a1
        add.l #roto_b-start,a1
        bsr decode_fighter
        move.l BASE(a5),a2
        add.l #roto_b-start,a2
        bsr mirror_fighter
        bsr ground
        bsr wait_blit
        move.l BACK(a5),a1
        move.w FRAME(a5),d0
        lsr.w #2,d0
        and.w #1,d0
        mulu #40,d0
        lea 6400(a1),a1
        tst.w TRAINART(a5)
        beq.s .deck_y
        sub.l #960,a1
        moveq #0,d0
.deck_y:
        add.w d0,a1
        moveq #19,d7
.deck:
        move.w #$ffff,(a1)
        move.w #$9999,160(a1)
        addq.l #2,a1
        dbra d7,.deck
        rts

fighter_pose:
        tst.w TRAINART(a5)
        beq.s .original
        add.w d0,d0
        move.w FRAME(a5),d1
        lsr.w #1,d1
        and.w #255,d1
        lsl.w #2,d1
        add.w d0,d1
        move.l a4,a0
        add.l #FIGHT_POSES,a0
        moveq #0,d0
        move.w (a0,d1.w),d0
        rts
.original:
        mulu #17,d0
        move.w FRAME(a5),d1
        lsr.w #1,d1
        divu #5,d1
        add.w d1,d0
        divu #47,d0
        swap d0
        and.l #$ffff,d0
        rts

decode_fighter:
        lsl.l #2,d0
        move.l a4,a2
        add.l #FIGHTER_INDEX,a2
        add.l d0,a2
        move.l a4,a0
        add.l #FIGHTER_COMPRESSED,a0
        move.l 4(a2),d0
        move.l (a2),d1
        move.l a0,a2
        add.l d0,a2
        add.l d1,a0
        move.l #FIGHTER_POSE,d0
        bra roto_decode

prepare_train_art:
        tst.w TRAINREADY(a5)
        bne.s .done
        tst.w TRAINART(a5)
        beq.s .done
        bsr wait_blit
        move.l a4,a0
        add.l #TRAIN_ART0,a0
        move.l a0,a2
        add.l #TRAIN_ART0_SIZE,a2
        move.l OLD(a5),a1
        move.l #19968,d0
        bsr roto_decode
        move.l a4,a0
        add.l #TRAIN_ART1,a0
        move.l a0,a2
        add.l #TRAIN_ART1_SIZE,a2
        move.l BASE(a5),a1
        add.l #hires_a-start,a1
        move.l #9984,d0
        bsr roto_decode
        move.w #1,TRAINREADY(a5)
.done:  rts

train_parallax:
        lea parallax_layers(pc),a3
        moveq #0,d7
.layer:
        move.w FRAME(a5),d4
        lsl.w d7,d4
        lsr.w #1,d4
        and.w #511,d4
        move.l a4,a2
        add.l (a3)+,a2
        move.w (a3)+,d5
        move.w (a3)+,d6
        tst.w TRAINART(a5)
        beq.s .original
        tst.w TRAINREADY(a5)
        beq.s .original
        cmp.w #2,d7
        beq .done
        and.w #255,d4
        move.l OLD(a5),a2
        moveq #TRAIN_CITY_Y,d5
        moveq #104,d6
        tst.w d7
        bne.s .car
        lsr.w #2,d4
        bra.s .original
.car:
        ; The carriage is the near layer. Restore one source pixel per VBL
        ; after the shared half-speed setup; the city remains deliberately slow.
        add.w d4,d4
        move.l BASE(a5),a2
        add.l #hires_a-start,a2
        move.w #144,d5
        moveq #52,d6
.original:
        movem.l d4-d7/a2-a3,-(sp)
        bsr parallax_plane
        movem.l (sp),d4-d7/a2-a3
        move.w d6,d0
        mulu #128,d0
        tst.w TRAINART(a5)
        beq.s .plane_offset
        tst.w TRAINREADY(a5)
        beq.s .plane_offset
        move.w d6,d0
        mulu #96,d0
.plane_offset:
        add.l d0,a2
        add.w #256,d5
        bsr parallax_plane
        movem.l (sp)+,d4-d7/a2-a3
        addq.w #1,d7
        cmp.w #3,d7
        blo .layer
 .done: rts

parallax_plane:
        bsr wait_blit
        move.w d4,d0
        and.w #15,d0
        moveq #0,d7
        tst.w d0
        beq.s .aligned
        moveq #16,d7
        sub.w d0,d7
        ror.w #4,d7
.aligned:
        or.w #$09f0,d7
        move.w d7,$40(a6)
        clr.w $42(a6)
        move.l #-1,$44(a6)
        move.w #86,$64(a6)
        cmp.w #9,SCENE(a5)
        bne.s .stride_ready
        tst.w TRAINART(a5)
        beq.s .stride_ready
        tst.w TRAINREADY(a5)
        beq.s .stride_ready
        move.w #54,$64(a6)
.stride_ready:
        clr.w $66(a6)
        lsr.w #4,d4
        add.w d4,d4
        add.w d4,a2
        move.l a2,$50(a6)
        move.l PARABUF(a5),$54(a6)
        move.w d6,d1
        lsl.w #6,d1
        or.w #21,d1
        move.w d1,$58(a6)
        move.l PARABUF(a5),a0
        tst.w d0
        beq.s .copy
        addq.l #2,a0
.copy:
        move.l BACK(a5),a1
        cmp.w #6,SCENE(a5)
        bne.s .train_dest
        move.l HIBACK(a5),a1
.train_dest:
        mulu #40,d5
        add.l d5,a1
        moveq #20,d0
        move.w d6,d1
        moveq #2,d2
        moveq #0,d3
        bra copy
parallax_layers:
        dc.l TRAIN_LAYER0
        dc.w 88,20
        dc.l TRAIN_LAYER1
        dc.w 132,18
        dc.l TRAIN_LAYER2
        dc.w 170,16

fighter_sprites:
        moveq #2,d7
.segment:
        move.w d4,d2
        lsr.w #1,d2
        move.b d2,1(a2)
        move.w d4,d2
        and.w #1,d2
        move.b d2,3(a2)
        add.w #16,d4
        move.w FRAME(a5),d1
        lsr.w #2,d1
        and.w #1,d1
        add.w #148,d1
        tst.w TRAINART(a5)
        beq.s .fighter_y
        moveq #124,d1
.fighter_y:
        move.b d1,(a2)
        add.w #FIGHTER_HEIGHT,d1
        move.b d1,2(a2)
        move.l a2,d0
        move.w d0,6(a0)
        swap d0
        move.w d0,2(a0)
        ; Apply now too: the frame's opening Copper MOVEs have already run.
        moveq #0,d2
        move.w (a0),d2
        move.l a2,(a6,d2.w)
        lea FIGHTER_SEGMENT(a2),a2
        lea 8(a0),a0
        dbra d7,.segment
        rts

mirror_fighter:
        move.l a2,a3
        move.l RBUFPTR(a5),a2
        move.l BACK(a5),d0
        cmp.l FRONT(a5),d0
        blo.s .bank
        lea FIGHTER_POSE(a2),a2
.bank:
        move.l a2,PENDING_R(a5)
        move.l a4,a0
        add.l #REVERSE_BYTE,a0
        moveq #0,d7
.segment:
        move.w d7,d0
        lsl.w #4,d0
        add.w #297,d0
        move.w d0,d1
        lsr.w #1,d0
        or.w #$9400,d0
        move.w d0,(a2)+
        and.w #1,d1
        or.w #$cc00,d1
        move.w d1,(a2)+
        moveq #2,d0
        sub.w d7,d0
        mulu #FIGHTER_SEGMENT,d0
        move.l a3,a1
        add.l d0,a1
        addq.l #4,a1
        move.w #FIGHTER_HEIGHT*2-1,d6
.word:
        moveq #0,d0
        move.b (a1)+,d0
        moveq #0,d1
        move.b (a1)+,d1
        move.b (a0,d1.w),d2
        lsl.w #8,d2
        move.b (a0,d0.w),d2
        move.w d2,(a2)+
        dbra d6,.word
        clr.l (a2)+
        addq.w #1,d7
        cmp.w #3,d7
        blo.s .segment
        rts

next_scene:
        move.l FRONT(a5),a0
        move.l OLD(a5),a1
        moveq #20,d0
        move.w #512,d1
        moveq #0,d2
        moveq #0,d3
        bsr copy
        bsr wait_blit
        cmp.w #4,SCENE(a5)
        bne.s .captured
        ; Pack alternate hires pixels into the outgoing 320-column bitmap.
        move.l HIFRONT(a5),a2
        move.l OLD(a5),a3
        lea 1600(a3),a3
        moveq #71,d7
.expand:
        moveq #39,d6
.byte:
        move.w (a2)+,d0
        moveq #0,d1
        moveq #7,d2
.pixel:
        add.w d0,d0
        addx.b d1,d1
        add.w d0,d0
        dbra d2,.pixel
        move.b d1,(a3)
        move.b d1,40(a3)
        addq.l #1,a3
        dbra d6,.byte
        lea 40(a3),a3
        dbra d7,.expand

.captured:
        cmp.w #2,SCENE(a5)
        bne.s .next
        ; Reconstruct just once for the outgoing two-plane transition.
        move.l BACK(a5),-(sp)
        move.l OLD(a5),BACK(a5)
        bsr roto_legacy
        bsr wait_blit
        move.l (sp)+,BACK(a5)
.next:
        addq.w #1,SCENE(a5)
        cmp.w #10,SCENE(a5)
        blo.s .ok
        clr.w SCENE(a5)
.ok:
        move.l TICK(a5),ENTER(a5)
        clr.w FRAME(a5)
        clr.w TRANS(a5)
scene_init:
        clr.w DANCEREADY(a5)
        clr.w ROVALID(a5)       ; fighter poses borrow roto buffers between scenes
        clr.w HIFONTREADY(a5)
        clr.w TRAINREADY(a5)
        clr.w GRAPHTICKS(a5)
        clr.w GX(a5)
        clr.w GY(a5)
        move.l GRAPHBUF(a5),a0
        move.w #1279,d0
.clear:
        clr.l (a0)+
        dbra d0,.clear
        move.l HORIZON(a5),a0
        moveq #79,d0
.h:
        move.l #$7f7f7f7f,(a0)+
        dbra d0,.h
        rts

; Incoming scene is composed normally, then masked against a frozen outgoing
; frame. A is mask, B incoming, C frozen, D back: (A&B)|(~A&C) = $CA.
transition:
        cmp.w #4,SCENE(a5)
        beq .done
        cmp.w #9,SCENE(a5)
        bne.s .normal_transition
        tst.w TRAINART(a5)
        bne .done
.normal_transition:
        tst.w TRANS(a5)
        bmi .done
        move.w FRAME(a5),d0
        cmp.w #32,d0
        bhs .finished
        bsr wait_blit
        lsr.w #1,d0
        addq.w #1,d0
        move.l MASKBUF(a5),a1
        btst #0,SCENE+1(a5)
        beq.s .dissolve
        mulu #640,d0
        move.w d0,d1
        lsr.w #2,d1
        subq.w #1,d1
.white:
        move.l #-1,(a1)+
        dbra d1,.white
        move.w #PLANE,d1
        sub.w d0,d1
        beq.s .maskdone
        lsr.w #2,d1
        subq.w #1,d1
.black:
        clr.l (a1)+
        dbra d1,.black
        bra.s .maskdone
.dissolve:
        mulu #160,d0
        move.l a4,a2
        add.l #DISSOLVE,a2
        add.l d0,a2
        moveq #63,d7
.repeat:
        move.l a2,a0
        moveq #39,d6
.row:
        move.l (a0)+,(a1)+
        dbra d6,.row
        dbra d7,.repeat
.maskdone:
        move.l BACK(a5),a2
        move.l OLD(a5),a3
        bsr .blend
        lea PLANE(a2),a2
        lea PLANE(a3),a3
        bsr .blend
        rts
.blend:
        bsr wait_blit
        move.l #$0fca0000,$40(a6)
        move.l #-1,$44(a6)
        clr.l $60(a6)
        clr.l $64(a6)
        move.l MASKBUF(a5),$50(a6)
        move.l a2,$4c(a6)
        move.l a3,$48(a6)
        move.l a2,$54(a6)
        move.w #$4014,$58(a6)
        rts
.finished:
        move.w #$ffff,TRANS(a5)
.done:  rts

keyboard:
        btst #3,$bfed01
        beq .done
        move.b $bfec01,d0
        not.b d0
        ror.b #1,d0
        bset #6,$bfee01
        ; Three scanline crossings guarantee the keyboard's >=85us ACK.
        moveq #2,d2
.ack:
        move.b $dff006,d1
.line:
        cmp.b $dff006,d1
        beq.s .line
        dbra d2,.ack
        bclr #6,$bfee01
        cmp.b #$93,d0
        bne.s .down
        clr.w RHELD(a5)
        rts
.down:
        cmp.b #$40,d0
        bne.s .select
        eor.w #1,PAUSED(a5)
        rts
.select:
        cmp.b #1,d0
        blo.s .runner_key
        cmp.b #10,d0
        bhi.s .runner_key
        and.w #$ff,d0
        subq.w #1,d0
        move.w d0,SCENE(a5)
        move.l TICK(a5),ENTER(a5)
        clr.w FRAME(a5)
        clr.w PAUSED(a5)
        move.w #$ffff,TRANS(a5)
        move.w #$ffff,LASTSCENE(a5)
        bra scene_init
.runner_key:
        cmp.b #$13,d0
        bne.s .done
        tst.w RHELD(a5)
        bne.s .done
        move.w #1,RHELD(a5)
        cmp.w #9,SCENE(a5)
        bne.s .body_toggle
        eor.w #1,TRAINART(a5)
        bra.s .changed
.body_toggle:
        eor.w #1,BODIES(a5)
.changed:
        move.w #$ffff,LASTSCENE(a5)
.done:  rts

buttons:
        moveq #0,d0
        btst #6,$bfe001
        bne.s .right
        bset #0,d0
.right:
        move.w $16(a6),d1
        btst #10,d1
        bne.s .edges
        bset #1,d0
.edges:
        move.w BUTTONS(a5),d1
        move.w d0,BUTTONS(a5)
        not.w d1
        and.w d0,d1
        btst #1,d1
        beq.s .left
        eor.w #1,MUTE(a5)
.left:
        btst #0,d1
        beq.s .done
        bsr next_scene
.done:  rts

init_audio:
        move.l a4,a0
        add.l #LEAD_SAMPLE,a0
        move.l a0,$a0(a6)
        move.w #32,$a4(a6)
        move.l a4,a0
        add.l #BASS_SAMPLE,a0
        move.l a0,$b0(a6)
        move.w #32,$b4(a6)
        move.l a4,a0
        add.l #PAD_SAMPLE,a0
        move.l a0,$c0(a6)
        move.w #32,$c4(a6)
        move.l a4,a0
        add.l #DRUM_SAMPLE,a0
        move.l a0,$d0(a6)
        move.w #128,$d4(a6)
        move.w #428,$a6(a6)
        move.w #856,$b6(a6)
        move.w #428,$c6(a6)
        move.w #150,$d6(a6)
        clr.w $a8(a6)
        clr.w $b8(a6)
        clr.w $c8(a6)
        clr.w $d8(a6)
        rts

music:
        move.l TICK(a5),d0
        divu #2560,d0
        swap d0
        and.l #$ffff,d0
        divu #10,d0
        move.w d0,d1
        swap d0
        add.w d0,d0
        move.l a4,a2
        add.l #VOLUME_ENV,a2
        add.w d0,a2
        lsl.w #3,d1
        move.l a4,a0
        add.l #SCORE,a0
        add.w d1,a0
        lea $a0(a6),a1
        lea VOLUMES(a5),a3
        moveq #3,d7
.voice:
        move.w (a0)+,d0
        move.w (a2),d1
        tst.w d0
        beq.s .silent
        move.w d0,6(a1)
        tst.w MUTE(a5)
        beq.s .volume
.silent:
        moveq #0,d1
.volume:
        move.w d1,8(a1)
        move.w d1,(a3)+
        lea 16(a1),a1
        lea 20(a2),a2
        dbra d7,.voice
        rts

; Four independent hardware sprites visualize the four actual Paula volumes.
meters:
        move.l SPRITES(a5),a0
        lea VOLUMES(a5),a1
        moveq #0,d6
.sprite:
        move.w d6,d0
        mulu #72,d0
        add.w #169,d0        ; screen x=40 plus DIW horizontal start
        move.w d0,d1
        lsr.w #1,d0
        or.w #$1000,d0       ; physical y=272 (screen y=228)
        move.w d0,(a0)+
        and.w #1,d1
        or.w #$2806,d1       ; stop y=296, high VSTART/VSTOP bits
        move.w d1,(a0)+
        move.w (a1)+,d1
        lsr.w #1,d1
        moveq #23,d7
.bar:
        moveq #0,d0
        cmp.w d1,d7
        bhs.s .blank
        move.w #$fffe,d0
.blank:
        move.w d0,(a0)+
        clr.w (a0)+
        dbra d7,.bar
        clr.l (a0)+
        addq.w #1,d6
        cmp.w #4,d6
        blo.s .sprite
        rts

publish_scene:
        move.l COP(a5),a0
        move.l FRONT(a5),d0
        moveq #1,d7
        move.w #$e0,d6
        cmp.w #6,SCENE(a5)
        beq.s .runner_bg
        cmp.w #7,SCENE(a5)
        bne.s .normal
        move.l a4,d0
        add.l #SPACE_BACKGROUND,d0
        bra.s .four
.runner_bg:
        move.l a4,d0
        add.l #SUNSET,d0
        tst.w BODIES(a5)
        beq.s .four
        moveq #4,d7
        move.l COPMODE(a5),a1
        move.w #$5200,2(a1)
        move.w #$5200,$100(a6)
        bra.s .planes
.four:
        moveq #3,d7
        move.l COPMODE(a5),a1
        move.w #$4200,2(a1)
        move.w #$4200,$100(a6)
        bra.s .planes
.normal:
        move.l COPMODE(a5),a1
        move.w #$2200,2(a1)
        move.w #$2200,$100(a6)
.planes:
        move.w d0,6(a0)
        swap d0
        move.w d0,2(a0)
        swap d0
        move.l d0,(a6,d6.w)
        add.l #PLANE,d0
        cmp.w #7,SCENE(a5)
        bne.s .runner_ptr
        cmp.w #2,d7
        bne.s .advance
        move.l FRONT(a5),d0
        bra.s .advance
.runner_ptr:
        cmp.w #6,SCENE(a5)
        bne.s .advance
        moveq #1,d1
        add.w BODIES(a5),d1
        cmp.w d1,d7
        bne.s .advance
        move.l FRONT(a5),d0
.advance:
        addq.w #4,d6
        lea 8(a0),a0
        dbra d7,.planes
        move.w SCENE(a5),d0
        cmp.w LASTSCENE(a5),d0
        beq.s .sprite_state
        move.w d0,LASTSCENE(a5)
        bsr palette
.sprite_state:
        cmp.w #7,SCENE(a5)
        beq .space_sprites
        cmp.w #9,SCENE(a5)
        bne .reset
        move.w FRAME(a5),d0
        lsr.w #1,d0
        and.w #255,d0
        lsl.w #2,d0
        move.l a4,a0
        add.l #FIGHT_X,a0
        move.w (a0,d0.w),d4
        move.w 2(a0,d0.w),d5
        move.l COPSPR(a5),a0
        move.l PENDING_L(a5),a2
        bsr fighter_sprites
        move.l COPSPR(a5),a0
        ; Leave sprite 3 empty so the fighters have separate colour pairs.
        move.l BASE(a5),d0
        add.l #dummy_sprite-start,d0
        move.w d0,30(a0)
        move.w d0,62(a0)
        swap d0
        move.w d0,26(a0)
        move.w d0,58(a0)
        lea 32(a0),a0
        move.l PENDING_R(a5),a2
        move.w d5,d4
        bsr fighter_sprites
        bra publish_hires
.space_sprites:
        move.l COPSPR(a5),a0
        move.l PENDING_L(a5),d0
        moveq #1,d7
.flyptr:
        move.w d0,6(a0)
        swap d0
        move.w d0,2(a0)
        swap d0
        lea 8(a0),a0
        add.l #72,d0
        dbra d7,.flyptr
        move.l BASE(a5),d0
        add.l #dummy_sprite-start,d0
        moveq #5,d7
        bra.s .reset_sprites
.reset:
        move.l COPSPR(a5),a0
        move.l BASE(a5),d0
        add.l #dummy_sprite-start,d0
        moveq #7,d7
.reset_sprites:
        move.w d0,6(a0)
        swap d0
        move.w d0,2(a0)
        swap d0
        moveq #0,d2
        move.w (a0),d2
        move.l d0,(a6,d2.w)
        lea 8(a0),a0
        dbra d7,.reset_sprites
        bra publish_hires

publish_hires:
        bsr publish_roto
        bsr animate_colours
        bsr text_modulos
        move.l HICOP(a5),a0
        move.l LOCOP(a5),a1
        moveq #4,d7
.off_hi:
        move.w #$1fe,(a0)
        addq.l #4,a0
        dbra d7,.off_hi
        moveq #6,d7
.off_lo:
        move.w #$1fe,(a1)
        addq.l #4,a1
        dbra d7,.off_lo
        move.l TEXTCOP(a5),a0
        moveq #4,d7
.off_text:
        move.w #$1fe,(a0)
        addq.l #4,a0
        dbra d7,.off_text
        move.l TEXTEND(a5),a0
        moveq #7,d7
.off_text_end:
        move.w #$1fe,(a0)
        addq.l #4,a0
        dbra d7,.off_text_end
        cmp.w #6,SCENE(a5)
        beq .ridge
        cmp.w #4,SCENE(a5)
        bne.s .done
        move.l TEXTCOP(a5),a0
        move.l #$01009200,(a0)+
        move.l #$0092003c,(a0)+
        move.l #$009400d4,(a0)+
        move.l HIFRONT(a5),d0
        move.w #$e0,(a0)+
        swap d0
        move.w d0,(a0)+
        move.w #$e2,(a0)+
        swap d0
        move.w d0,(a0)+
        move.l TEXTEND(a5),a0
        move.l #$01002200,(a0)+
        move.l #$00920038,(a0)+
        move.l #$009400d0,(a0)+
        move.l FRONT(a5),d0
        add.l #7360,d0
        move.w #$e0,d1
        moveq #1,d7
.restore:
        move.w d1,(a0)+
        swap d0
        move.w d0,(a0)+
        swap d0
        addq.w #2,d1
        move.w d1,(a0)+
        move.w d0,(a0)+
        addq.w #2,d1
        add.l #PLANE,d0
        dbra d7,.restore
        move.l #$01080000,(a0)+
.done:  rts
.ridge:
        move.l HICOP(a5),a0
        move.l HIFRONT(a5),d0
        move.w #$e0,(a0)
        swap d0
        move.w d0,2(a0)
        move.w #$e2,4(a0)
        swap d0
        move.w d0,6(a0)
        move.l #$018a0112,8(a0)
        move.l #$018e0112,12(a0)
        move.l LOCOP(a5),a0
        move.l a4,d0
        add.l #SUNSET+7360,d0
        move.w #$e0,(a0)
        swap d0
        move.w d0,2(a0)
        move.w #$e2,4(a0)
        swap d0
        move.w d0,6(a0)
        move.l #$018a0856,8(a0)
        move.l #$018e0ffe,12(a0)
        rts

; Repeat compact rotated rows twice with Copper-controlled DMA. The even
; plane remains a full-height dot overlay; the odd plane advances every other line.
publish_roto:
        moveq #0,d5
        cmp.w #2,SCENE(a5)
        bne.s .mode
        cmp.w #32,FRAME(a5)
        blo.s .mode
        moveq #1,d5
.mode:
        move.w ROMODE(a5),d0
        or.w d5,d0
        beq .done
        move.w d5,ROMODE(a5)
        moveq #0,d6
        tst.w d5
        beq.s .bands
        move.w FRAME(a5),d0
        and.w #255,d0
        add.w d0,d0
        move.l a4,a0
        add.l #SINE,a0
        move.w (a0,d0.w),d6
        asr.w #1,d6
.bands:
        move.l COPINDEX(a5),a2
        move.l ROMODINDEX(a5),a3
        moveq #0,d7
.band:
        move.l (a2)+,a0
        move.w d7,d0
        lsl.w #2,d0
        add.w #44,d0
        cmp.w #50,d7
        bhs.s .late_band
        add.w d6,d0
        bra.s .time
.late_band:
        ; Keep footer waits after the bobbed band 49, still before line 252.
        move.w d7,d1
        add.w #191,d1
        add.w d6,d1
        cmp.w d1,d0
        bhs.s .time
        move.w d1,d0
.time:
        lsl.w #8,d0
        or.w #7,d0
        move.w d0,(a0)
        move.l (a3)+,d0
        beq.s .next
        move.l d0,a1
        tst.w d5
        beq.s .mods
        move.w #$57b,6(a0)
        move.w 18(a0),14(a0)
.mods:
        move.w (a0),d0
        moveq #0,d2
.modrow:
        move.w #$1fe,(a1)
        tst.w d5
        beq.s .modnext
        move.w #$108,(a1)
        moveq #-40,d1
        btst #0,d2
        beq.s .modwrite
        moveq #0,d1
.modwrite:
        move.w d1,2(a1)
.modnext:
        addq.l #4,a1
        addq.w #1,d2
        cmp.w #4,d2
        beq.s .next
        add.w #$100,d0
        move.w d0,(a1)
        addq.l #4,a1
        bra.s .modrow
.next:
        addq.w #1,d7
        cmp.w #52,d7
        blo.s .band
        move.l ROENTRY(a5),a0
        move.l ROEXIT(a5),a1
        tst.w d5
        bne.s .pointers
        move.w #$1fe,(a0)
        move.w #$1fe,4(a0)
        move.w #$1fe,8(a0)
        move.w #$1fe,(a1)
        move.w #$1fe,4(a1)
        move.w #$1fe,8(a1)
        rts
.pointers:
        move.l ROFRONT(a5),d0
        move.w #$e0,(a0)
        swap d0
        move.w d0,2(a0)
        move.w #$e2,4(a0)
        swap d0
        move.w d0,6(a0)
        move.w #$108,8(a0)
        move.w #-40,10(a0)
        move.w d6,d0
        add.w #192,d0
        mulu #40,d0
        add.l FRONT(a5),d0
        move.w #$e0,(a1)
        swap d0
        move.w d0,2(a1)
        move.w #$e2,4(a1)
        swap d0
        move.w d0,6(a1)
        move.w #$108,8(a1)
        clr.w 10(a1)
.done:  rts

build_copper:
        move.l COP(a5),a0
        move.l #$00e00000,(a0)+
        move.l #$00e20000,(a0)+
        move.l #$00e40000,(a0)+
        move.l #$00e60000,(a0)+
        move.l #$00e80000,(a0)+
        move.l #$00ea0000,(a0)+
        move.l #$00ec0000,(a0)+
        move.l #$00ee0000,(a0)+
        move.l #$00f00000,(a0)+
        move.l #$00f20000,(a0)+
        move.l #$008e2c81,(a0)+
        move.l #$00902cc1,(a0)+
        move.l #$00920038,(a0)+
        move.l #$009400d0,(a0)+
        move.l a0,COPMODE(a5)
        move.l #$01002200,(a0)+
        move.l #$01020000,(a0)+
        ; Both playfields behind every sprite pair. PF2P controls priority
        ; even in single-playfield mode: zero hid fighters behind lights.
        move.l #$01040024,(a0)+
        move.l #$01080000,(a0)+
        move.l #$010a0000,(a0)+
        move.l a0,COPPAL(a5)
        move.l #$01800000,(a0)+
        move.l #$01820acf,(a0)+
        move.l #$0184057b,(a0)+
        move.l #$01860fff,(a0)+
        move.l #$01a20123,(a0)+
        move.l #$01aa0123,(a0)+
        move.l a0,COPSPR(a5)
        move.l BASE(a5),d0
        add.l #dummy_sprite-start,d0
        move.w #$120,d1
        moveq #7,d7
.sp:
        move.w d1,(a0)+
        swap d0
        move.w d0,(a0)+
        swap d0
        addq.w #2,d1
        move.w d1,(a0)+
        move.w d0,(a0)+
        addq.w #2,d1
        dbra d7,.sp
        move.l #$01a40eb9,(a0)+
        move.l #$01a60d82,(a0)+
        move.l #$01ac0eb9,(a0)+
        move.l #$01ae0d82,(a0)+
        move.l #$01b20123,(a0)+
        move.l #$01b40eb9,(a0)+
        move.l #$01b60d82,(a0)+
        move.l #$01880c88,(a0)+
        move.l #$018a0856,(a0)+
        move.l #$018c0fda,(a0)+
        move.l #$018e0ffe,(a0)+
        move.l a0,COPEXTRA(a5)
        move.w #$190,d0
        moveq #23,d7
.overlay_palette:
        move.w d0,(a0)+
        move.w #$fff,(a0)+
        addq.w #2,d0
        dbra d7,.overlay_palette
        move.l a0,COPRASTER(a5)
        move.l COPINDEX(a5),a2
        move.l ROMODINDEX(a5),a3
        moveq #0,d7
.band:
        move.l a0,(a2)+
        clr.l (a3)
        move.w d7,d0
        lsl.w #2,d0
        add.w #44,d0
        lsl.w #8,d0
        or.w #$07,d0
        move.w d0,(a0)+
        move.w #$fffe,(a0)+
        move.l #$01800000,(a0)+
        move.l #$01820acf,(a0)+
        move.l #$0184057b,(a0)+
        move.l #$01860fff,(a0)+
        cmp.w #32,d7
        bne.s .restore_band
        move.l a0,HICOP(a5)
        moveq #4,d6
.hi_slots:
        move.l #$01fe0000,(a0)+
        dbra d6,.hi_slots
.restore_band:
        cmp.w #46,d7
        bne.s .next_band
        move.l a0,LOCOP(a5)
        moveq #6,d6
.lo_slots:
        move.l #$01fe0000,(a0)+
        dbra d6,.lo_slots
.next_band:
        cmp.w #10,d7
        bne.s .text_end_band
        move.l a0,TEXTCOP(a5)
        moveq #4,d6
.text_slots:
        move.l #$01fe0000,(a0)+
        dbra d6,.text_slots
.text_end_band:
        cmp.w #46,d7
        bne.s .text_ready
        move.l a0,TEXTEND(a5)
        moveq #7,d6
.text_end_slots:
        move.l #$01fe0000,(a0)+
        dbra d6,.text_end_slots
.text_ready:
        cmp.w #8,d7
        beq.s .ro_entry
        cmp.w #48,d7
        bne.s .ro_mod
        move.l a0,ROEXIT(a5)
        bra.s .ro_ptrs
.ro_entry:
        move.l a0,ROENTRY(a5)
.ro_ptrs:
        move.l #$01fe0000,(a0)+
        move.l #$01fe0000,(a0)+
        move.l #$01fe0000,(a0)+
.ro_mod:
        cmp.w #8,d7
        blo.s .ro_next
        cmp.w #48,d7
        bhs.s .ro_next
        move.l a0,(a3)
        move.l #$01fe0000,(a0)+
        move.w d7,d0
        lsl.w #2,d0
        add.w #44,d0
        lsl.w #8,d0
        or.w #7,d0
        moveq #2,d6
.ro_subrow:
        add.w #$100,d0
        move.w d0,(a0)+
        move.w #$fffe,(a0)+
        move.l #$01fe0000,(a0)+
        dbra d6,.ro_subrow
.ro_next:
        addq.l #4,a3
        addq.w #1,d7
        cmp.w #52,d7
        blo .band
        move.l #$fc07fffe,(a0)+
        move.l #$01800000,(a0)+
        move.l #$ffdffffe,(a0)+
        move.l #$0007fffe,(a0)+
        move.l #$01a20af8,(a0)+
        move.l #$01aa0f8d,(a0)+
        move.l SPRITES(a5),d0
        move.w #$120,d1
        moveq #3,d7
.meters:
        move.w d1,(a0)+
        swap d0
        move.w d0,(a0)+
        swap d0
        addq.w #2,d1
        move.w d1,(a0)+
        move.w d0,(a0)+
        addq.w #2,d1
        add.l #104,d0
        dbra d7,.meters
        move.l #$fffffffe,(a0)+
        rts

text_modulos:
        moveq #0,d5
        cmp.w #4,SCENE(a5)
        bne.s .mode
        moveq #1,d5
.mode:
        move.w TEXTMODE(a5),d0
        move.w d5,TEXTMODE(a5)
        or.w d5,d0
        beq.s .done
        tst.w ROMODE(a5)
        bne.s .done
        move.l ROMODINDEX(a5),a0
        lea 40(a0),a0
        moveq #35,d7
.band:
        move.l (a0)+,a1
        moveq #3,d6
.row:
        move.w #$1fe,(a1)
        tst.w d5
        beq.s .next
        move.w #$108,(a1)
        moveq #-80,d0
        btst #0,d6
        bne.s .write
        moveq #0,d0
.write:
        move.w d0,2(a1)
.next:
        lea 8(a1),a1
        dbra d6,.row
        dbra d7,.band
.done:  rts

animate_colours:
        move.l COPINDEX(a5),a0
        lea hud_bands(pc),a3
        moveq #3,d7
.hud:
        moveq #0,d0
        move.b (a3)+,d0
        move.w FRAME(a5),d1
        lsr.w #3,d1
        add.w d0,d1
        and.w #63,d1
        add.w d1,d1
        move.l a4,a2
        add.l #HUD_COLOURS,a2
        lsl.w #2,d0
        move.l (a0,d0.w),a1
        move.w (a2,d1.w),10(a1)
        dbra d7,.hud
        cmp.w #3,SCENE(a5)
        beq.s .dance
        cmp.w #4,SCENE(a5)
        bne.s .done
        move.w FRAME(a5),d0
        lsr.w #1,d0
        and.w #63,d0
        mulu #36,d0
        move.l a4,a2
        add.l #HI_CHROME,a2
        add.l d0,a2
        lea 40(a0),a0
        moveq #35,d7
.chrome:
        move.l (a0)+,a1
        move.w (a2),10(a1)
        btst #0,d7
        bne.s .same_colour
        addq.l #2,a2
.same_colour:
        dbra d7,.chrome
.done:  rts
.dance:
        lea 64(a0),a0
        move.l a4,a2
        add.l #HUD_COLOURS,a2
        moveq #31,d7
.dance_band:
        move.l (a0)+,a1
        move.w FRAME(a5),d0
        lsr.w #2,d0
        move.w d7,d1
        mulu #3,d1
        add.w d1,d0
        and.w #63,d0
        add.w d0,d0
        move.w (a2,d0.w),18(a1)
        dbra d7,.dance_band
        rts
hud_bands: dc.b 2,3,50,51
        even

palette:
        move.l COPEXTRA(a5),a0
        lea default_extra(pc),a1
        moveq #0,d7
.extra:
        move.w (a1)+,d0
        cmp.w #7,SCENE(a5)
        bne.s .runner_extra
        cmp.w #8,d7
        blo .extra_set
        cmp.w #16,d7
        bhs.s .extra_set
        move.w d7,d1
        and.w #3,d1
        move.w #$36a,d0
        cmp.w #2,d1
        bne.s .fly_white
        move.w #$9df,d0
.fly_white:
        cmp.w #3,d1
        bne.s .extra_set
        move.w #$fff,d0
        bra.s .extra_set
.runner_extra:
        cmp.w #9,SCENE(a5)
        bne.s .runner_palette
        tst.w TRAINART(a5)
        beq.s .extra_set
        cmp.w #16,d7
        blo .extra_set
        move.w d7,d1
        and.w #3,d1
        cmp.w #1,d1
        bne.s .jones_clothes
        move.w #$324,d0
        bra.s .extra_set
.jones_clothes:
        cmp.w #3,d1
        bne.s .extra_set
        move.w #$674,d0
        bra.s .extra_set
.runner_palette:
        cmp.w #6,SCENE(a5)
        bne.s .extra_set
        tst.w BODIES(a5)
        beq.s .extra_set
        move.w #$39c,d0
        cmp.w #8,d7
        blo .extra_set
        move.w #$246,d0
        cmp.w #16,d7
        blo .extra_set
        move.w #$fd9,d0
.extra_set:
        move.w d0,2(a0)
        addq.l #4,a0
        addq.w #1,d7
        cmp.w #24,d7
        blo .extra
        move.l COPINDEX(a5),a2
        moveq #0,d7
.band:
        move.l (a2)+,a0
        moveq #0,d0
        move.w #$acf,d1
        move.w #$57b,d2
        move.w #$fff,d3
        cmp.w #6,SCENE(a5)
        bne.s .train
        move.w d7,d0
        add.w d0,d0
        move.l a4,a1
        add.l #SUNSET_RAMP,a1
        move.w (a1,d0.w),d0
        move.w #$647,d1
        move.w #$324,d2
        move.w #$112,d3
        cmp.w #32,d7
        blo .set
        cmp.w #46,d7
        bhs .set
        move.w #$112,d1
        bra .set
.train:
        cmp.w #7,SCENE(a5)
        bne.s .train_colour
        move.w #$012,d0
        move.w #$325,d1
        move.w #$85a,d2
        move.w #$fc9,d3
        bra .set
.train_colour:
        cmp.w #9,SCENE(a5)
        bne.s .colour
        move.w #$012,d0
        move.w #$345,d1
        move.w #$fb8,d2
        move.w #$bce,d3
        tst.w TRAINART(a5)
        beq.s .old_train_palette
        move.w #$759,d1
        move.w #$e9a,d2
        move.w #$ffe,d3
        cmp.w #36,d7
        blo .set
        bra.s .train_car
.old_train_palette:
        cmp.w #32,d7
        blo .set
.train_car:
        move.w #$567,d1
        move.w #$89a,d2
        move.w #$bdf,d3
        bra .set
.colour:
        cmp.w #5,SCENE(a5)
        bne.s .chrome
        ; A face keeps its material colour across every raster band.
        move.w #$5df,d1
        move.w #$b5f,d2
        move.w #$fd7,d3
        bra .set
.chrome:

.ordinary:
        cmp.w #8,d7
        blo.s .set
        cmp.w #48,d7
        bhs.s .set
        move.w d7,d4
        lsr.w #3,d4
        and.w #3,d4
        add.w d4,d4
        lea raster_ramp(pc),a1
        move.w (a1,d4.w),d1
        move.w d1,d3
.set:
        cmp.w #4,d7
        blo.s .hud_colour
        cmp.w #50,d7
        blo.s .write_colour
.hud_colour:
        move.w FRAME(a5),d4
        lsr.w #3,d4
        add.w d7,d4
        and.w #63,d4
        add.w d4,d4
        move.l a4,a1
        add.l #HUD_COLOURS,a1
        move.w (a1,d4.w),d1
.write_colour:
        move.w d0,6(a0)
        move.w d1,10(a0)
        move.w d2,14(a0)
        move.w d3,18(a0)
        addq.w #1,d7
        cmp.w #52,d7
        blo .band
        rts
raster_ramp: dc.w $5cf,$8ef,$fb8,$f8c
default_extra:
        dc.w $fff,$fff,$fff,$fff,$fff,$fff,$fff,$fff
        dc.w 0,$123,$eb9,$d82,0,$123,$eb9,$d82
        dc.w 0,$123,$eb9,$d82,0,$123,$eb9,$d82

        even
stats_magic: dc.b 'AURA500!'
state:
        dc.b 'AURA'           ; boot initialization clears these pointer fields
        dcb.b 252,0
        even
assets:
        incbin "build/assets.bin"
        even
screen_a: dcb.b SCREEN,0
screen_b: dcb.b SCREEN,0
frozen: dcb.b SCREEN,0
copper: dcb.b 3072,0
sprite_data: dcb.b 416,0
dummy_sprite: dc.l 0,0
graph_data: dcb.b 5120,0
horizon_data: dcb.b 320,0
mask_data: dcb.b PLANE,0
right_fighter_data: dcb.b FIGHTER_POSE*2,0
perf_data: dcb.b 80,0
roto_a: dcb.b 3200,0
roto_b: dcb.b 3200,0
hires_a: dcb.b 5760,0
hires_b: dcb.b 5760,0
hires_work: dcb.b 5760,0
copper_index: dcb.b 208,0
roto_mod_index: dcb.b 208,0
parallax_data: dcb.b 42*104,0
program_end:
