import matplotlib.pyplot as plt

PLOT_COUNT = 0

class calcModel:
    def __init__(self, Vcc, pulldown):
        self.Vcc = Vcc
        self.pulldown = pulldown

        self.analogs = range(0, 1024) # 2^10
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

    def volt_to_Rfsr(self, volt):
        return ((self.Vcc * self.pulldown) / volt) - self.pulldown

    def sensor_val_to_N(self, val):
        if(val > 0):
            res_volt = self.val_to_volt(val)
            Rfsr = self.volt_to_Rfsr(res_volt)
            cond = 1 / Rfsr # Conductance = 1 / Resistance | G = 1/R | R = 1/G

            #print("Vfsr = %.10f V" % res_volt)
            #print("Rfsr = %.10f Ohm" % Rfsr)
            #print("Cfsr = %.10f S" % cond)

            # For a voltage of <3 V, the correlation is quite linear to conductance
            if res_volt <= 3:
                # This is what we can calibrate! If we apply exactly 100g of weight and get the voltage difference,
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
        else:
            return 0

    def plot(self, x, y, xlabel, ylabel, xlim=None, ylim=None):
        global PLOT_COUNT
        PLOT_COUNT += 1
        
        fig = plt.figure(PLOT_COUNT)
        ax1 = fig.add_subplot(111)
        ax1.set_title("%s vs. %s\nVcc = %.02f V, Pulldown = %i Ohm" % (ylabel, xlabel, self.Vcc, self.pulldown))

        ax1.set_xlabel(xlabel)
        ax1.set_ylabel(ylabel)

        if xlim is not None:
            ax1.set_xlim(xlim)

        if ylim is not None:
            ax1.set_ylim(ylim)

        ax1.plot(x, y)

m = calcModel(5.06, 10000)
m.plot(m.volts, m.conds, "Voltage (V)", "Conductance (S)", ylim=(0, 2*10**-3))

m = calcModel(5.06, 3000)
m.plot(m.volts, m.conds, "Voltage (V)", "Conductance (S)", ylim=(0, 2*10**-3))

m = calcModel(5.06, 100000)
m.plot(m.volts, m.conds, "Voltage (V)", "Conductance (S)", ylim=(0, 2*10**-4))

plt.show()
"""
  Convert the 0...1023 (= 1024 different values!) value to Newtons
  
  We start with:
   res_volt = sensor_readout * (Vcc / (2^10 - 1))
  Where sensor_readout comes directly from Arduino
  Vcc = power supply voltage (e.g. with USB, it's aprox. 5.06V)
  And 2^10 (=1024) because arduino has 10-bit readout capability
  We exclude a readout of 0, so we use 1023 in the calculation, not 1024

  Then we want to calculate the resistance over the FSR:
   res_volt = (Vcc * Rp) / (Rp + Rfsr)
  We know res_volt, Vcc, Rp (= pulldown resistance)
  We want to know Rfsr

  Some algebra:
   res_volt = (Vcc * Rp) / (Rp + Rfsr) | start out with this
   (Rp + Rfsr) * res_volt = Vcc * Rp   | both side times (R + FSR)
   (Rp + Rfsr) = (Vcc * Rp) / res_volt | both sides divided by res_volt
   Rfsr = ((Vcc * Rp) / res_volt) - Rp | both sides subtracted by R
"""
