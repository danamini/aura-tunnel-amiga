"""Inspect a FS-UAE save state against the immutable build actually launched."""
from pathlib import Path
import argparse, hashlib, json, re, struct, zlib

ROOT=Path(__file__).resolve().parents[1]

def chunks(path):
    data=Path(path).read_bytes();offset=0;out={}
    while offset+12<=len(data):
        name=data[offset:offset+4].decode('ascii')
        size,flags=struct.unpack_from('>II',data,offset+4)
        if size<12:break
        block=data[offset+12:offset+size]
        if flags&1:block=zlib.decompress(block[4:])
        out[name]=block
        offset+=size+4-((size-12-(4 if flags&1 else 0))&3)
    return out

def inspect(path):
    release=Path((ROOT/'emulator-data/loaded-build.txt').read_text().strip())
    binary=(release/'demo.bin').read_bytes()
    listing=(release/'demo.lst').read_text()
    def symbol(name):return int(re.search(r'^'+name+r'\s+A:([0-9A-Fa-f]+)$',listing,re.M)[1],16)
    saved=chunks(path);memory=saved['CRAM']
    # The floppy staging copy can retain the marker; select the relocated live
    # program by its BASE self-pointer, not the first matching byte string.
    candidates=[]
    for match in re.finditer(re.escape(b'AURA500!'),memory):
        candidate=match.start()-symbol('stats_magic')
        state_address=candidate+symbol('state')
        if 0<=state_address and state_address+256<=len(memory):
            if struct.unpack_from('>I',memory,state_address+68)[0]==candidate:
                candidates.append((candidate,state_address))
    assert len(candidates)==1,'Expected one active native program'
    base,state=candidates[0]
    assert memory[base:base+128]==binary[:128],'Snapshot does not match launched binary'
    u16=lambda a:struct.unpack_from('>H',memory,a)[0]
    u32=lambda a:struct.unpack_from('>I',memory,a)[0]
    result={'sha256':hashlib.sha256(binary).hexdigest(),'base':base,'state':state,
            'pc':struct.unpack_from('>I',saved['CPU '],68)[0],
            'ticks':u32(state+16),'renders':u32(state+32),'scene':u16(state+26),
            'scene_frame':u16(state+24),'muted':bool(u16(state+36)),
            'graph_ticks_upper_bound':u16(state+166), 'graph_x':u16(state+56), 'graph_y':u16(state+58)}
    perf=u32(state+76)
    if perf and perf+80<=len(memory):
        names=json.loads((release/'scenes.json').read_text())
        result['performance']=[{'scene':names[i]['name'],'presented':u32(perf+i*8),
          'vblanks':u32(perf+i*8+4),'fps':round(50*u32(perf+i*8)/u32(perf+i*8+4),2) if u32(perf+i*8+4) else None} for i in range(10)]
    return result,saved

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('snapshot',nargs='?',default=str(ROOT/'emulator-data/states/Saved State 1.uss'))
    p.add_argument('--save',action='store_true');args=p.parse_args()
    result,_=inspect(args.snapshot)
    print(json.dumps(result,indent=2))
    if args.save:(ROOT/'build/runtime-results.json').write_text(json.dumps(result,indent=2)+'\n')
