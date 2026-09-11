"""Shade the pinned motion-capture skeleton without altering its animation."""
import importlib.util, math, struct
from PIL import Image, ImageDraw

def generate(reference, output):
    spec=importlib.util.spec_from_file_location('mocap',reference/'tools/mocap_runner.py')
    mocap=importlib.util.module_from_spec(spec);spec.loader.exec_module(mocap)
    poses,scale,top,_,_=mocap.cycle()
    data=bytearray();offsets=[];preview=[]
    for half,origin,count in [(1,(108,40),12),(2,(36,116),8),(2,(240,112),8)]:
        for phase in range(count):
            f=phase/count*len(poses);i=int(f);t=f-i
            p={name: (origin[0]+(52+(v[0]*(1-t)+poses[(i+1)%len(poses)][name][0]*t)*scale)/half,
                      origin[1]+(8+(top-v[1]*(1-t)-poses[(i+1)%len(poses)][name][1]*t)*scale)/half)
               for name,v in poses[i].items()}
            im=Image.new('P',(320,256));draw=ImageDraw.Draw(im)
            def limb(a,b,width,colour):
                a=p[a];b=p[b];w=max(1,round(width/half));r=w/2
                draw.line([a,b],fill=colour,width=w)
                for x,y in [a,b]:draw.ellipse((x-r,y-r,x+r,y+r),fill=colour)
            # Far limbs first; the near side carries the sunset highlights.
            for side,colour in [('Left',2),('Right',1)]:
                limb(side+'UpLeg',side+'Leg',7,colour)
                limb(side+'Leg',side+'Foot',5,colour)
                limb(side+'Foot',side+'ToeBase',4,3 if side=='Right' else 2)
                limb(side+'Arm',side+'ForeArm',5,colour)
                limb(side+'ForeArm',side+'Hand',4,colour)
            limb('Neck1','Hips',12,1)
            limb('Neck1','Hips',4,3)
            x,y=[sum(v)/2 for v in zip(p['Head'],p['HeadEnd'])]
            draw.ellipse((x-5/half,y-6/half,x+5/half,y+6/half),fill=1)
            draw.arc((x-5/half,y-6/half,x+5/half,y+6/half),240,70,fill=3,width=max(1,round(2/half)))
            # Sparse word runs: absolute byte offset, literal word count, words.
            # This writes only the occupied parts of the cleared overlay planes.
            offsets.append(len(data))
            for plane in range(2):
                for y in range(24,200):
                    row=[sum(bool(im.getpixel((x+b,y))&(1<<plane))<<(15-b) for b in range(16)) for x in range(0,320,16)]
                    x=0
                    while x<20:
                        if not row[x]:x+=1;continue
                        start=x
                        while x<20 and row[x]:x+=1
                        data+=struct.pack('>HH',plane*10240+y*40+start*2,x-start)
                        data+=struct.pack('>'+'H'*(x-start),*row[start:x])
            data+=b'\xff\xff'
            if half==1:
                im.putpalette([0,0,0,53,154,204,39,62,99,255,217,153]+[0]*756)
                preview.append(im.convert('RGB').crop((108,40,210,180)))
    sheet=Image.new('RGB',(102*6,140*2))
    for i,im in enumerate(preview):sheet.paste(im,((i%6)*102,(i//6)*140))
    sheet.save(output/'runner-bodies.png')
    return offsets,data
