import glob,sys,numpy as np
from PIL import Image
tag=sys.argv[1]
fs=sorted(glob.glob('logs/shots/%s_travel_a_b*.png'%tag))
im=[np.asarray(Image.open(f).convert('RGB')).astype(np.int16) for f in fs]
h=min(i.shape[0] for i in im); w=min(i.shape[1] for i in im); im=[i[:h,:w] for i in im]
med=np.median(np.stack(im[::2]),axis=0); bad=[]
for k,i in enumerate(im):
    dark=(i.max(axis=2)<14)&(med.max(axis=2)>=40); dark[:100]=False
    if dark.sum()>400: bad.append((k+1,int(dark.sum())))
print('%s: frames=%d flagged=%d %s'%(tag,len(im),len(bad),bad))
