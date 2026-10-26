import re,sys,struct
def dst(w):
    return ''.join(c for b,c in zip((24,23,22,21),'xyzw') if (w>>b)&1)
def up(w):
    if w & 0x80000000 and False: pass
    d=dst(w); ft=(w>>16)&31; fs=(w>>11)&31; fd=(w>>6)&31; op=w&0x3F
    bc='xyzw'
    names={0x00:'addx',1:'addy',2:'addz',3:'addw',4:'subx',5:'suby',6:'subz',7:'subw',8:'maddx',9:'maddy',10:'maddz',11:'maddw',12:'msubx',13:'msuby',14:'msubz',15:'msubw',16:'maxx',17:'maxy',18:'maxz',19:'maxw',20:'minix',21:'miniy',22:'miniz',23:'miniw',24:'mulx',25:'muly',26:'mulz',27:'mulw',0x1C:'mulq',0x1D:'maxi',0x1E:'muli',0x1F:'minii',0x20:'addq',0x21:'maddq',0x22:'addi',0x23:'maddi',0x24:'subq',0x25:'msubq',0x26:'subi',0x27:'msubi',0x28:'add',0x29:'madd',0x2A:'mul',0x2B:'max',0x2C:'sub',0x2D:'msub',0x2E:'opmsub',0x2F:'mini'}
    if op<0x3C:
        n=names.get(op,f'op{op:02X}')
        if n=='opmsub': return f'opmsub.xyz vf{fd},vf{fs},vf{ft}'
        return f'{n}.{d} vf{fd},vf{fs},vf{ft}'
    g=op&3; k=(w>>6)&31
    t={0:['addax','subax','maddax','msubax','itof0','ftoi0','mulax','mulaq','addaq','subaq','adda','suba'],
       1:['adday','subay','madday','msubay','itof4','ftoi4','mulay','abs','maddaq','msubaq','madda','msuba'],
       2:['addaz','subaz','maddaz','msubaz','itof12','ftoi12','mulaz','mulai','addai','subai','mula','opmula'],
       3:['addaw','subaw','maddaw','msubaw','itof15','ftoi15','mulaw','clip','maddai','msubai','nop']}[g]
    n=t[k] if k<len(t) else f'sp{g}_{k}'
    if n in('itof0','itof4','itof12','itof15','ftoi0','ftoi4','ftoi12','ftoi15','abs'): return f'{n}.{d} vf{ft},vf{fs}'
    if n=='clip': return f'clipw.xyz vf{fs},vf{ft}'
    if n=='nop': return 'nop'
    return f'{n}.{d} ACC,vf{fs},vf{ft}'
def imm11(w):
    v=w&0x7FF
    return v-0x800 if v&0x400 else v
def imm15(w): return ((w>>10)&0x7800)|(w&0x7FF)
def low(pc,w):
    if w==0x8000033C: return 'nop'
    op=w>>25; d=dst(w); ft=(w>>16)&31; fs=(w>>11)&31; fd=(w>>6)&31
    if op==0x00: return f'lq.{d} vf{ft},{imm11(w)}(vi{fs})'
    if op==0x01: return f'sq.{d} vf{fs},{imm11(w)}(vi{ft})'
    if op==0x04: return f'ilw.{d} vi{ft},{imm11(w)}(vi{fs})'
    if op==0x05: return f'isw.{d} vi{ft},{imm11(w)}(vi{fs})'
    if op==0x08: return f'iaddiu vi{ft},vi{fs},{imm15(w)}'
    if op==0x09: return f'isubiu vi{ft},vi{fs},{imm15(w)}'
    m={0x10:'fceq',0x11:'fcset',0x12:'fcand',0x13:'fcor',0x14:'fseq',0x15:'fsset',0x16:'fsand',0x17:'fsor',0x18:'fmeq',0x1A:'fmand',0x1B:'fmor',0x1C:'fcget'}
    if op in m: return f'{m[op]} vi{ft} imm=0x{((w>>10)&0x1000)|(w&0xFFF):X}' if op not in (0x11,) else f'fcset 0x{w&0xFFFFFF:X}'
    br={0x20:'b',0x21:'bal',0x28:'ibeq',0x29:'ibne',0x2C:'ibltz',0x2D:'ibgtz',0x2E:'iblez',0x2F:'ibgez',0x24:'jr',0x25:'jalr'}
    if op in br:
        if op in (0x24,0x25): return f'{br[op]} vi{fs}'
        return f'{br[op]} vi{ft},vi{fs} ->0x{pc+8+imm11(w)*8:X}'
    if op==0x40:
        f=w&0x3F
        if f in (0x30,0x31,0x34,0x35): return f'{ {0x30:"iadd",0x31:"isub",0x34:"iand",0x35:"ior"}[f]} vi{fd},vi{fs},vi{ft}'
        if f==0x32: return f'iaddi vi{ft},vi{fs},{(fd if fd<16 else fd-32)}'
        o=w&0x7FF; fsf=(w>>21)&3; ftf=(w>>23)&3
        S={0x33C:'move',0x33D:'mr32',0x37C:'lqi',0x37D:'sqi',0x37E:'lqd',0x37F:'sqd',0x3BC:'div',0x3BD:'sqrt',0x3BE:'rsqrt',0x3BF:'waitq',0x3FC:'mtir',0x3FD:'mfir',0x3FE:'ilwr',0x3FF:'iswr',0x43C:'rnext',0x43D:'rget',0x43E:'rinit',0x43F:'rxor',0x67C:'mfp',0x6BC:'xtop',0x6BD:'xitop',0x6FC:'xgkick',0x73C:'esadd',0x73D:'ersadd',0x73E:'eleng',0x73F:'erleng',0x77C:'eatanxy',0x77D:'eatanxz',0x77E:'esum',0x7BC:'esqrt',0x7BD:'ersqrt',0x7BE:'ercpr',0x7BF:'waitp',0x7FC:'esin',0x7FD:'eatan',0x7FE:'eexp'}
        n=S.get(o,f'sp{o:03X}')
        if n in('div','sqrt','rsqrt'): return f'{n} Q,vf{fs}.{"xyzw"[fsf]},vf{ft}.{"xyzw"[ftf]}'
        if n=='lqi': return f'lqi.{d} vf{ft},(vi{fs}++)'
        if n=='sqi': return f'sqi.{d} vf{fs},(vi{ft}++)'
        if n=='lqd': return f'lqd.{d} vf{ft},(--vi{fs})'
        if n=='sqd': return f'sqd.{d} vf{fs},(--vi{ft})'
        if n=='move': return f'move.{d} vf{ft},vf{fs}'
        if n=='mtir': return f'mtir vi{ft},vf{fs}.{"xyzw"[fsf]}'
        if n=='mfir': return f'mfir.{d} vf{ft},vi{fs}'
        if n in('xtop','xitop'): return f'{n} vi{ft}'
        if n=='xgkick': return f'xgkick vi{fs}'
        if n=='ilwr': return f'ilwr.{d} vi{ft},(vi{fs})'
        if n=='iswr': return f'iswr.{d} vi{ft},(vi{fs})'
        return n+f' ft={ft} fs={fs} dst={d}'
    return f'lop{op:02X} raw={w:08X}'
if __name__=='__main__':
    rows=[]
    for l in open(sys.argv[1],errors='replace'):
        m=re.search(r'eg pc=0x(\w+) up=0x(\w+) lo=0x(\w+)(.*)',l)
        if m: rows.append((int(m[1],16),int(m[2],16),int(m[3],16),m[4]))
    a=int(sys.argv[2]); b=int(sys.argv[3])
    for i,(pc,u,lw,rest) in enumerate(rows[a:b],a):
        flag=('I' if u>>31&1 else '')+('E' if u>>30&1 else '')+('M' if u>>29&1 else '')
        iword = ' I=%08X'%lw if (u>>31)&1 else ''
        ud=up(u) if u&0x3F!=0x3F or True else ''
        ld='(imm)'+iword if (u>>31)&1 else low(pc,lw)
        vfw=re.findall(r'(vfw=\S+ \S+ \S+ \S+(?:;vf\d+:\S+ \S+ \S+ \S+)*)',rest)
        short=re.sub(r' q=.*','',rest).strip()
        print(f'{i:3d} {pc:04X} {flag:2s} {ud:30s} | {ld:34s} {short}')
