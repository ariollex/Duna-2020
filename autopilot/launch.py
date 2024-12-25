import krpc
import time
import math
import json
import os

# Time for recording flight data (seconds)
RECORD_TIME = 140

# Lists for recording flight data
speed_records = []
altitude_records = []
angle_records = []
mass_records = []
time_records = []

def save_flight_data():
    """
    Save recorded flight data to a JSON file.
    """
    os.makedirs("records", exist_ok=True)
    flight_data = {
        "speed": speed_records,
        "altitude": altitude_records,
        "angle": angle_records,
        "mass": mass_records,
        "time": time_records,
    }
    with open("records/flight_data.json", "w") as file:
        json.dump(flight_data, file, indent=4)

# Flight parameters
TURN_START_ALTITUDE = 1000  # Altitude to start gravity turn (m)
TURN_END_ALTITUDE = 45000  # Altitude to complete gravity turn (m)
TARGET_APOAPSIS = 100000   # Target apoapsis altitude (m)

# Connect to Kerbal Space Program (KSP)
conn = krpc.connect(name="Launch to Orbit")
vessel = conn.space_center.active_vessel

# Setting up data streams
ut = conn.add_stream(getattr, conn.space_center, "ut")
altitude = conn.add_stream(getattr, vessel.flight(), "mean_altitude")
apoapsis = conn.add_stream(getattr, vessel.orbit, "apoapsis_altitude")
periapsis = conn.add_stream(getattr, vessel.orbit, "periapsis_altitude")
speed = conn.add_stream(getattr, vessel.flight(vessel.orbit.body.reference_frame), "speed")
angle = conn.add_stream(getattr, vessel.flight(vessel.surface_reference_frame), "pitch")
mass = conn.add_stream(getattr, vessel, "mass")
srb_fuel = conn.add_stream(vessel.resources_in_decouple_stage(9, cumulative=False).amount, "SolidFuel")

# Countdown before launch
for i in range(3, 0, -1):
    print(f"Launch in {i}...")
    time.sleep(1)
print("Liftoff!")

# Launch sequence
vessel.auto_pilot.engage()
vessel.control.activate_next_stage()  # Activate first stage
for i in range(40, 0, -1):
    time.sleep(0.05)
    vessel.control.throttle = 1.0 / i
time.sleep(1)
vessel.auto_pilot.target_pitch_and_heading(90, 90)
vessel.control.activate_next_stage()  # Ignite main engines

# Track time since launch
start_time = ut()
srb_separated = False
current_time = ut() - start_time

is_data_saved = False  # Flag to ensure data is saved only once

# Main ascent loop
while apoapsis() < TARGET_APOAPSIS:
    # Record data during the ascent phase
    if current_time <= RECORD_TIME:
        current_time = ut() - start_time
        speed_records.append(speed())
        altitude_records.append(altitude())
        angle_records.append(90 - angle())
        mass_records.append(mass())
        time_records.append(current_time)
    else:
        if not is_data_saved:
            save_flight_data()
            is_data_saved = True
            print("Flight data has been saved.")

    # Gravity turn logic
    if TURN_START_ALTITUDE < altitude() < TURN_END_ALTITUDE:
        frac = (altitude() - TURN_START_ALTITUDE) / (TURN_END_ALTITUDE - TURN_START_ALTITUDE)
        vessel.auto_pilot.target_pitch_and_heading(90 - frac * 90, 90)

    # Separate SRBs when fuel is depleted
    if not srb_separated and srb_fuel() <= 0:
        print("Separating SRBs.")
        vessel.control.activate_next_stage()
        srb_separated = True

    time.sleep(0.1)

# Cut off engines and prepare for orbit circularization
vessel.control.activate_next_stage()
vessel.control.throttle = 0
print("Reached target apoapsis. Preparing for circularization maneuver.")

# Planning the circularization maneuver
mu = vessel.orbit.body.gravitational_parameter
r = vessel.orbit.apoapsis
a1 = vessel.orbit.semi_major_axis
a2 = r
v1 = math.sqrt(mu * ((2 / r) - (1 / a1)))
v2 = math.sqrt(mu * ((2 / r) - (1 / a2)))
delta_v = v2 - v1
node = vessel.control.add_node(ut() + vessel.orbit.time_to_apoapsis, prograde=delta_v)

# Orienting for the maneuver
vessel.auto_pilot.disengage()
vessel.control.sas = True
vessel.control.sas_mode = conn.space_center.SASMode.maneuver
print("SAS set to maneuver mode.")

# Calculate burn time
thrust = vessel.available_thrust
isp = vessel.specific_impulse * 9.82
m0 = vessel.mass
m1 = m0 / math.exp(delta_v / isp)
flow_rate = thrust / isp
burn_time = (m0 - m1) / flow_rate

# Wait for the maneuver burn
print("Waiting for circularization burn...")
burn_start_time = ut() + vessel.orbit.time_to_apoapsis - (burn_time / 2)
while burn_start_time - ut() > 0:
    if altitude() >= 70000 and not srb_separated:
        vessel.control.activate_next_stage()
        srb_separated = True
    time.sleep(0.1)

# Execute the circularization burn
print("Executing circularization burn.")
vessel.control.throttle = 1.0
time.sleep(burn_time)
vessel.control.throttle = 0
vessel.control.remove_nodes()
vessel.control.activate_next_stage()
print("Circularization complete. Stable orbit achieved.")
