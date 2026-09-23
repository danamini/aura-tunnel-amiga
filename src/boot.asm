        include "build/size.i"
        dc.b 'DOS',0
        dc.l 0,880
        move.l a1,a5
        move.l 4.w,a6
        move.l #ALLOCATION,d0
        move.l #$10002,d1
        jsr -198(a6)            ; AllocMem: cleared CHIP, DMA-visible
        tst.l d0
        beq.s failure
        move.l d0,a4
        move.l a5,a1
        move.w #2,28(a1)        ; CMD_READ
        move.l #PAYLOAD,36(a1)
        move.l a4,40(a1)
        move.l #1024,44(a1)
        jsr -456(a6)            ; DoIO; still under the boot ROM
        tst.b 31(a5)
        bne.s failure
        ; The score is CPU-only data; reserve it in the A500's 512 KiB slow RAM.
        move.l #MUSIC_ALLOCATION,d0
        move.l #$10004,d1      ; MEMF_CLEAR | MEMF_FAST (includes A500 slow RAM)
        jsr -198(a6)
        tst.l d0
        beq.s failure
        move.l d0,a3
        move.l a5,a1
        move.w #2,28(a1)
        move.l #MUSIC_ALLOCATION,36(a1)
        move.l a3,40(a1)
        move.l #1024+PAYLOAD,44(a1)
        jsr -456(a6)
        tst.b 31(a5)
        bne.s failure
        move.l a5,a1
        move.w #9,28(a1)        ; TD_MOTOR off
        clr.l 36(a1)
        jsr -456(a6)
        jmp (a4)
failure:
        move.w #$f00,$dff180
        bra.s failure
