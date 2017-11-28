import machine
import time


ADC_COUNTS = 1024   # in emon this is 1<<ADCbits (10bits in the esp8266), ie 2^10


def calc_vi(crossings, timeout):

    supply_voltage = 3300

    cross_count = 0             # Used to measure number of times threshold is crossed.
    number_of_samples = 0       # This is now incremented
    
    # 1) Waits for the waveform to be close to 'zero' (mid-scale adc) part in sin curve.
    st = False                  # an indicator to exit the while loop

    start = time.ticks_ms()     # ticks_ms()-start makes sure it doesnt get stuck in the loop if there is an error.

    while not st:
        startV = analogRead(inPinV)                    # using the voltage waveform
        if (startV < (ADC_COUNTS*0.55)) and (startV > (ADC_COUNTS*0.45)):
            st = True  # check its within range
        if time.ticks_diff(time.ticks_ms(), start) > 500:
            st = True

    # 2) Main measurement loop
    # -------------------------------------------------------------------------------------------------------------------------
    start = time.ticks_ms()
    
    while (cross_count < crossings) and (time.ticks_diff(time.ticks_ms(), start)):

        number_of_samples += 1                      # Count number of times looped.
        last_filtered_v = filteredV                 # Used for delay/phase compensation

        # A) Read in raw voltage and current samples
        sampleV = analogRead(inPinV)                # Read in raw voltage signal
        sampleI = analogRead(inPinI)                # Read in raw current signal

        # B) Apply digital low pass filters to extract the 2.5 V or 1.65 V dc offset,
        #     then subtract this - signal is now centred on 0 counts.
        offsetV = offsetV + ((sampleV-offsetV)/1024)
        filteredV = sampleV - offsetV
        offsetI = offsetI + ((sampleI-offsetI)/1024)
        filteredI = sampleI - offsetI

        # C) Root-mean-square method voltage
        sqV= filteredV * filteredV                 # 1) square voltage values
        sumV += sqV                                # 2) sum

        # D) Root-mean-square method current
        sqI = filteredI * filteredI                # 1) square current values
        sumI += sqI                                # 2) sum

        # E) Phase calibration
        phaseShiftedV = last_filtered_v + PHASECAL * (filteredV - last_filtered_v)

        # F) Instantaneous power calc
        instP = phaseShiftedV * filteredI          # Instantaneous Power
        sumP +=instP                               # Sum

        # G) Find the number of times the voltage has crossed the initial voltage
        #    - every 2 crosses we will have sampled 1 wavelength
        #    - so this method allows us to sample an integer number of half wavelengths which increases accuracy
        lastVCross = checkVCross
        if (sampleV > startV):
            checkVCross = true
        else:
            checkVCross = false

        if (number_of_samples==1):
            lastVCross = checkVCross

        if (lastVCross != checkVCross):
            cross_count+=1

    # 3) Post loop calculations
    # -------------------------------------------------------------------------------------------------------------------------
    # Calculation of the root of the mean of the voltage and current squared (rms)
    # Calibration coefficients applied.

    V_RATIO = VCAL * ((supply_voltage/1000.0) / ADC_COUNTS)
    Vrms = V_RATIO * sqrt(sumV / number_of_samples)

    I_RATIO = ICAL * ((supply_voltage/1000.0) / ADC_COUNTS)
    Irms = I_RATIO * sqrt(sumI / number_of_samples)

    # Calculation power values
    realPower = V_RATIO * I_RATIO * sumP / number_of_samples
    apparentPower = Vrms * Irms
    powerFactor = realPower / apparentPower

    # Reset accumulators
    sumV = 0
    sumI = 0
    sumP = 0


adc = machine.ADC(0)
sleep_ms(750)

while True:
    #Then read its value with:
    sleep_ms(500)
    adc.read()

