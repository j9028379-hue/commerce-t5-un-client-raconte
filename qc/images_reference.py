import cv2,numpy as np,sys
v,w=[cv2.VideoCapture(p) for p in sys.argv[1:3]];worst=0
for i in range(900):
 ok,a=v.read();good,b=w.read();assert ok and good and a.shape==b.shape==(1280,720,3);a,b=[cv2.resize(x,(90,160),interpolation=cv2.INTER_AREA).astype(float) for x in [a,b]];worst=max(worst,np.abs(a-b).mean())
assert not v.read()[0] and not w.read()[0] and worst<1.5,worst;print('900 images comparées ; erreur absolue moyenne max / 255 :',worst)
