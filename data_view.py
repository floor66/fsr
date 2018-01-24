import matplotlib.pyplot as plt

f = open("sensordata/data_1516706033_1.txt")
lines = f.readlines()

ts = []
vs = []
for l in lines:
    if l[0] != ";":
        tmp = l.rstrip().split(",")

        if len(tmp) == 3:
            t = int(tmp[0])
            v = int(tmp[2])

            if v > 0:
                voltage = (v * (5.06 / 1023))
                r = 10000 * ((5.06 / voltage) - 1)
                
                ts.append(t)
                vs.append(v)
            else:
                ts.append(t)
                vs.append(0)

plt.plot(ts, vs)
plt.xlim(0, ts[-1])
#plt.ylim(0, 40000)
plt.grid()
plt.show()
