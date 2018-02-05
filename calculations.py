class FSRCalculations:
    def __init__(self, Vcc, pulldown):
        self.Vcc = Vcc
        self.pulldown = pulldown

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
        return self.pulldown * ((self.Vcc / volt) - 1) if volt > 0 else 0

    def val_to_N(self, val):
        if(val > 0):
            res_volt = self.val_to_volt(val)
            Rfsr = self.volt_to_Rfsr(res_volt)

            if Rfsr > 0:
                cond = 1 / Rfsr # Conductance = 1 / Resistance and vice-versa
            else:
                return 0
            
            #   y = 96892x-1,292 (in grams), so * g for newton
            force = (96892 * (Rfsr**-1.292)) * 9.8066500286389
            # Not really correct, reference website rounded too much

            return force

            """
            #print("Vfsr = %.10f V" % res_volt)
            #print("Rfsr = %.10f Ohm" % Rfsr)
            #print("Cfsr = %.10f S" % cond)
            """
        else:
            return 0

