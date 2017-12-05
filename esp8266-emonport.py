import machine
import utime
import math
import ujson

ADC_COUNTS = 1024   # in emon this is 1<<ADCbits (left-shift 10bits in the esp8266), ie 2^10
adc = machine.ADC(0)
filteredV = ADC_COUNTS/2

crossCount = 0          # Used to measure number of times threshold is crossed.
numberOfSamples = 0     # This is now incremented


def calc_vi(crossings, timeout):

    supply_voltage = 3300

    cross_count = 0             # Used to measure number of times threshold is crossed.
    number_of_samples = 0       # This is now incremented
    
    # 1) Waits for the waveform to be close to 'zero' (mid-scale adc) part in sin curve.
    st = False                  # an indicator to exit the while loop

    start = utime.ticks_ms()     # ticks_ms()-start makes sure it doesnt get stuck in the loop if there is an error.

    while not st:
        start_i = adc.read()                    # using the voltage waveform
        if (start_i < (ADC_COUNTS*0.55)) and (start_i > (ADC_COUNTS*0.45)):
            st = True  # check its within range
        if utime.ticks_diff(utime.ticks_ms(), start) > 500:
            st = True

    # 2) Main measurement loop
    # -----------------------------------------------------------------------------------------------------
    start = utime.ticks_ms()
    sum_i = 0

    while (cross_count < crossings) and (utime.ticks_diff(utime.ticks_ms(), start) < timeout):

        number_of_samples += 1                      # Count number of times looped.
        last_filtered_v = filteredV                 # Used for delay/phase compensation

        # A) Read in raw voltage and current samples
        # sampleV = analogRead(inPinV)                # Read in raw voltage signal
        sample_i = adc.read()                # Read in raw current signal

        # B) Apply digital low pass filters to extract the 2.5 V or 1.65 V dc offset,
        #     then subtract this - signal is now centred on 0 counts.
        # offsetV = offsetV + ((sampleV-offsetV)/1024)
        # filteredV = sampleV - offsetV
        offset_i = offset_i + ((sample_i-offset_i)/1024)
        filtered_i = sample_i - offset_i

        # C) Root-mean-square method voltage
        # sqV= filteredV * filteredV                    # 1) square voltage values
        # sumV += sqV                                   # 2) sum

        # D) Root-mean-square method current
        sq_i = filtered_i * filtered_i                  # 1) square current values
        sum_i += sq_i                                   # 2) sum

        # E) Phase calibration
        # phaseShiftedV = last_filtered_v + PHASECAL * (filteredV - last_filtered_v)

        # F) Instantaneous power calc
        # instP = phaseShiftedV * filtered_i            # Instantaneous Power
        # sumP +=instP                                  # Sum

        # G) Find the number of times the voltage has crossed the initial voltage
        #    - every 2 crosses we will have sampled 1 wavelength
        #    - so this method allows us to sample an integer number of half wavelengths which increases accuracy
        last_v_cross = check_v_cross
        if sample_i > start_i:
            check_v_cross = True
        else:
            check_v_cross = False

        if number_of_samples == 1:
            last_v_cross = check_v_cross

        if last_v_cross != check_v_cross:
            cross_count += 1

    # 3) Post loop calculations
    # -------------------------------------------------------------------------------------------------------------------------
    # Calculation of the root of the mean of the voltage and current squared (rms)
    # Calibration coefficients applied.

    # V_RATIO = VCAL * ((supply_voltage/1000.0) / ADC_COUNTS)
    # Vrms = V_RATIO * sqrt(sumV / number_of_samples)

    ICAL = 1
    I_RATIO = ICAL * ((supply_voltage/1000.0) / ADC_COUNTS)
    i_rms = I_RATIO * math.sqrt(sum_i / number_of_samples)

    # Calculation power values
    # realPower = V_RATIO * I_RATIO * sum_p / number_of_samples
    # apparentPower = Vrms * Irms
    # powerFactor = realPower / apparentPower

    # Reset accumulators
    # sumV = 0
    sum_i = 0
    # sumP = 0


# --------------------------------------------------------------------------------------
def calc_irms(number_of_samples):

    # if defined emonTxV3
    supply_voltage = 3300
    sum_i = 0
    debug_sinewave = []
    offset_i = ADC_COUNTS/2

    # 1) Waits for the waveform to be close to 'zero' (mid-scale adc) part in sin curve.
    st = False                  # an indicator to exit the while loop

    start = utime.ticks_ms()     # ticks_ms()-start makes sure it doesnt get stuck in the loop if there is an error.

    while not st:
        start_i = adc.read()                    # using the voltage waveform
        if (start_i < (ADC_COUNTS*0.55)) and (start_i > (ADC_COUNTS*0.45)):
            st = True  # check its within range
        if utime.ticks_diff(utime.ticks_ms(), start) > 500:
            st = True

    for n in range(number_of_samples):
        sample_i = adc.read()
        debug_sinewave.append(sample_i)

        # Digital low pass filter extracts the 2.5 V or 1.65 V dc offset,
        # then subtract this - signal is now centered on 0 counts.
        offset_i = (offset_i + (sample_i - offset_i) / 1024)
        filtered_i = sample_i - offset_i

        # Root-mean-square method current
        sq_i = filtered_i * filtered_i
        sum_i += sq_i

    ICAL = 1    # no idea what to set this to? Need to find an example from emonlib repo
    I_RATIO = ICAL * ((supply_voltage / 1000.0) / ADC_COUNTS)
    i_rms = I_RATIO * math.sqrt(sum_i / number_of_samples)

    return i_rms, debug_sinewave


i_rms, sine_wave = calc_irms(20000)
print(ujson.dumps(sine_wave))
