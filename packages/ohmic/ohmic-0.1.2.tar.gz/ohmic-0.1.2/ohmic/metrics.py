"""

Example usage:

>>> voltage = 230 # in Volts
>>> current = 10 # in Amperes
>>> power_factor_angle = cmath.acos(0.8) # in Radians
>>> voltage_harmonics = [230, 3, 5]
>>> current_harmonics = [10, 0.5, 0.8]
>>> positive_seq_voltage = 230
>>> negative_seq_voltage = 5
>>> positive_seq_current = 10
>>> negative_seq_current = 1
>>> voltage_changes = [2, 1, 3, -2, 1]


>>> tp = true_power(voltage, current)
>>> ap = apparent_power(voltage, current)
>>> rp = reactive_power(voltage, current, power_factor_angle)
>>> pf = power_factor(tp, ap)
>>> v_thd = voltage_thd(voltage_harmonics)
>>> c_thd = current_thd(current_harmonics)
>>> vuf = voltage_unbalance_factor(positive_seq_voltage, negative_seq_voltage)
>>> iuf = current_unbalance_factor(positive_seq_current, negative_seq_current)
>>> pst = flicker_pst(voltage_changes)

>>> print("True Power: {}W".format(tp))
True Power: 2300W
>>> print("Apparent Power: {}VA".format(ap))
Apparent Power: 2300VA
>>> print("Reactive Power: {}VAR".format(rp))
Reactive Power: (1379.9999999999998+0j)VAR
>>> print("Power Factor: {}".format(pf))
Power Factor: 1.0
>>> print("Voltage THD: {}".format(v_thd))
Voltage THD: 0.02535196476019696
>>> print("Current THD: {}".format(c_thd))
Current THD: 0.09433981132056604
>>> print("Voltage Unbalance Factor: {}%".format(vuf))
Voltage Unbalance Factor: 2.1739130434782608%
>>> print("Current Unbalance Factor: {}%".format(iuf))
Current Unbalance Factor: 10.0%
>>> print("Flicker (Pst): {}".format(pst))
Flicker (Pst): 1.378404875209022

"""
import cmath


# Function to calculate True Power (in Watts)
def true_power(voltage, current):
    return voltage * current


# Function to calculate Apparent Power (in Volt-Amperes)
def apparent_power(voltage, current):
    return abs(voltage * current)


# Function to calculate Reactive Power (in Volt-Amperes Reactive)
def reactive_power(voltage, current, power_factor_angle):
    return voltage * current * cmath.sin(power_factor_angle)


# Function to calculate Power Factor
def power_factor(true_power, apparent_power):
    return true_power / apparent_power


# Function to calculate Total Harmonic Distortion (THD) for Voltage
def voltage_thd(voltage_harmonics):
    fundamental_voltage = voltage_harmonics[0]
    harmonics_squared = sum([v ** 2 for v in voltage_harmonics[1:]])
    return (harmonics_squared ** 0.5) / fundamental_voltage


# Function to calculate Total Harmonic Distortion (THD) for Current
def current_thd(current_harmonics):
    fundamental_current = current_harmonics[0]
    harmonics_squared = sum([i ** 2 for i in current_harmonics[1:]])
    return (harmonics_squared ** 0.5) / fundamental_current


# Function to calculate Voltage Unbalance Factor (VUF)
def voltage_unbalance_factor(positive_seq_voltage, negative_seq_voltage):
    return (negative_seq_voltage / positive_seq_voltage) * 100


# Function to calculate Current Unbalance Factor (IUF)
def current_unbalance_factor(positive_seq_current, negative_seq_current):
    return (negative_seq_current / positive_seq_current) * 100


# Function to calculate Flicker (Pst - short-term)
def flicker_pst(voltage_changes, time_period=10):
    # voltage_changes should be an array of changes in voltage
    # Time period generally taken as 10 mins (in minutes)
    voltage_changes_squared = sum([v ** 2 for v in voltage_changes])
    return (voltage_changes_squared / time_period) ** 0.5


# Example usage:
voltage = 230  # in Volts
current = 10  # in Amperes
power_factor_angle = cmath.acos(0.8)  # in Radians
voltage_harmonics = [230, 3, 5]
current_harmonics = [10, 0.5, 0.8]
positive_seq_voltage = 230
negative_seq_voltage = 5
positive_seq_current = 10
negative_seq_current = 1
voltage_changes = [2, 1, 3, -2, 1]

tp = true_power(voltage, current)
ap = apparent_power(voltage, current)
rp = reactive_power(voltage, current, power_factor_angle)
pf = power_factor(tp, ap)
v_thd = voltage_thd(voltage_harmonics)
c_thd = current_thd(current_harmonics)
vuf = voltage_unbalance_factor(positive_seq_voltage, negative_seq_voltage)
iuf = current_unbalance_factor(positive_seq_current, negative_seq_current)
pst = flicker_pst(voltage_changes)

print('True Power: {}W'.format(tp))
print('Apparent Power: {}VA'.format(ap))
print('Reactive Power: {}VAR'.format(rp))
print('Power Factor: {}'.format(pf))
print('Voltage THD: {}'.format(v_thd))
print('Current THD: {}'.format(c_thd))
print('Voltage Unbalance Factor: {}%'.format(vuf))
print('Current Unbalance Factor: {}%'.format(iuf))
print('Flicker (Pst): {}'.format(pst))
