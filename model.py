import matplotlib.pyplot as plt
from math import log

PLOT_COUNT = 0

class calcModel:
    def __init__(self, Vcc, pulldown):
        self.Vcc = Vcc
        self.pulldown = pulldown

        # Pre-append 0, because self.analogs[0] will give 0 for all calculations
        self.analogs = range(0, 1024) # 2^10, gives an array of 0-1023 (= 1024 different values)
        self.volts = [0] # Volt
        self.resists = [0] # Ohm
        self.conds = [0] # Siemen
        self.forces = [0] # Newton

        for i in self.analogs:
            if i > 0:
                self.volts.append(self.val_to_volt(i))

                if self.volts[i] > 0:
                    self.resists.append(self.volt_to_Rfsr(self.volts[i]))

                    if self.resists[i] > 0:
                        self.conds.append(1 / self.resists[i])

                        if self.conds[i] > 0:
                            self.forces.append(self.sensor_val_to_N(i))
                        else:
                            self.forces.append(0)
                    else:
                        self.conds.append(0)
                        self.forces.append(0)

    def val_to_volt(self, val):
        return val * (self.Vcc / (2**10 - 1)) if val > 0 else 0

    """
    FSR spec sheet says:
      VOUT = (V+) / [1 + RFSR/RM]
      
    Where:
      VOUT is measured by Arduino on the analog pin
        the pin gives a value of 0-1023, corresponding to (Vcc / 2^10) different "steps" of voltage
      V+ = Vcc (power source to Arduino)
      RFSR = the "unknown" we want to know (!)
      RM = pulldown resistance

    So, in our words and some algebra:
      res_volt = Vcc / (1 + (Rfsr / Rp))
      
      (1 + (Rfsr / Rp)) * res_volt = Vcc   | Div both sides by (1 + (Rfsr / Rp))
      (1 + (Rfsr / Rp)) = (Vcc / res_volt) | Div both sides by res_volt
      (Rfsr / Rp) = ((Vcc / res_volt) - 1) | Subtract both by 1
      Rfsr = Rp * ((Vcc / res_volt) - 1)   | Multiply both by Rp
    """
    def volt_to_Rfsr(self, volt):
        # return ((self.Vcc * self.pulldown) / volt) - self.pulldown (old formula, works the same but less evidence)
        return self.pulldown * ((self.Vcc / volt) - 1)

    def sensor_val_to_N(self, val):
        if(val > 0):
            res_volt = self.val_to_volt(val)
            Rfsr = self.volt_to_Rfsr(res_volt)
            cond = 1 / Rfsr # Conductance = 1 / Resistance and vice-versa
            
            # y = 96892x-1,292
            force = 96892 * (Rfsr**-1.292)
            # Not really correct, reference website rounded too much

            return force

            """
            #print("Vfsr = %.10f V" % res_volt)
            #print("Rfsr = %.10f Ohm" % Rfsr)
            #print("Cfsr = %.10f S" % cond)

            # Speculative:
            #   for a voltage of <3 V, the correlation is quite linear to conductance
            if res_volt <= 3:
                # This is what we can calibrate! If we apply 100g (or rather a series) of weight and get the voltage difference,
                #  we can calculate the Rfsr and thus the conductance!

                # Between 0 and 100g == 0 and 0.981 N == 0 and 0.0000015 S -> read from Datasheet, bad approximation
                slope_NS = (0.1 * 9.81) / 0.0000015 # Slope in N/S

                # N = N/S * S
                # This only counts for 0-3V
                force = slope_NS * cond

                return force
            else:
                #print("V > 3V")
                return 0
            """
        else:
            return 0

    def plot(self, x, y, xlabel, ylabel, xlim=None, ylim=None):
        global PLOT_COUNT
        PLOT_COUNT += 1
        
        fig = plt.figure(PLOT_COUNT)
        ax1 = fig.add_subplot(111)
        ax1.set_title("%s vs. %s\nVcc = %.02f V, Pulldown = %i kOhm" % (ylabel, xlabel, self.Vcc, self.pulldown/1000))

        ax1.set_xlabel(xlabel)
        ax1.set_ylabel(ylabel)

        if xlim is not None:
            ax1.set_xlim(xlim)

        if ylim is not None:
            ax1.set_ylim(ylim)

        ax1.plot(x, y)

m = calcModel(5.06, 10000)
m.plot(m.volts, m.resists, "Voltage (V)", "Resistance (Ohm)")
m.plot(m.volts, m.conds, "Voltage (V)", "Conductance (S)", ylim=(0, 2*10**-3))
m.plot([v*1000 for v in m.volts], m.forces, "Voltage (mV)", "Force (N)", ylim=(0, 100))
print(m.forces[-10:])

#m = calcModel(5.06, 3000)
#m.plot(m.volts, m.conds, "Voltage (V)", "Conductance (S)", ylim=(0, 2*10**-3))

#m = calcModel(5.06, 100000)
#m.plot(m.volts, m.conds, "Voltage (V)", "Conductance (S)", ylim=(0, 2*10**-4))

plt.show()

