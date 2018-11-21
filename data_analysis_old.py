import numpy as np

fn = "data_1541493946_2"
wire = "Mesh"

baseline_t_start = 0
baseline_t_end = 1

comp_t_start = 1
comp_t_end = 31

with open("sensordata/%s.txt" % fn) as f:
    baseline_t_start *= 60000
    baseline_t_end *= 60000
    comp_t_start *= 60000
    comp_t_end *= 60000

    # Load data
    data_lines = f.readlines()
    ts = []
    vals = []
    for l in data_lines:
        if l[0] != ";":
            tmp = l.rstrip().split(",")

            if len(tmp) == 3:
                t = int(tmp[0])
                v = int(tmp[2])

                ts.append(t)
                vals.append(v)

    ts = np.array(ts)
    vals = np.array(vals)
    volts = (vals * (5.06 / 1023))
    resists = 10000 * ((5.06 / volts) - 1)

    baseline_t_start = 0
    baseline_t_end = np.where(ts == baseline_t_end)[0][0]
    comp_t_start = np.where(ts == comp_t_start)[0][0]
    comp_t_end = np.where(ts == comp_t_end)[0][0]

    baseline = np.mean(
        vals[baseline_t_start:baseline_t_end]
        )
    comp = np.mean(
        vals[comp_t_start:comp_t_end]
        )
    
    print(wire)
    print("Baseline value = %.4f" % baseline)
    print("End value      = %.4f" % comp)
    print("Factor         = %.4f" % (comp / baseline))
    print("1/Factor       = %.4f" % (baseline / comp))
    print("Difference     = %.4f" % (comp - baseline))
