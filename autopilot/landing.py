import krpc
import time


def update_focus():
    """
    Update references to the active vessel and its key components after stage changes.
    """
    global vessel, control, antenna
    vessel = conn.space_center.active_vessel
    control = vessel.control
    antenna = vessel.parts.with_tag("radio")


# Connect to the kRPC server and set up initial references
conn = krpc.connect(name="Landing on Duna")
update_focus()

# Create streams for altitude data
altitude = conn.add_stream(getattr, vessel.flight(), "mean_altitude")
surface_altitude = conn.add_stream(getattr, vessel.flight(), "surface_altitude")

# Separate the cruise stage
control.activate_next_stage()
print("Cruise stage separated")

# Update vessel references after stage separation
update_focus()

# Stabilize the capsule before atmospheric entry
while altitude() > 50_000:
    pass
control.sas = True
print("SAS engaged")
time.sleep(1)
control.sas_mode = conn.space_center.SASMode.retrograde
print("SAS set to retrograde")
control.rcs = True
print("RCS engaged")

# Detach the heat shield after atmospheric entry
while altitude() > 40_000:
    pass
control.activate_next_stage()
print("Heat shield detached")
time.sleep(0.1)

# Update vessel references after heat shield separation
update_focus()

# Disable RCS and set SAS to stability assist for controlled descent
control.rcs = False
print("RCS disengaged")
control.sas_mode = conn.space_center.SASMode.stability_assist
print("SAS set to stability assist")

# Deploy parachutes at a safe altitude (RealChute workaround)
while surface_altitude() > 20_000:
    pass
control.activate_next_stage()
print("Parachutes partially deployed")

# Fully deploy parachutes closer to the surface
while surface_altitude() > 1_000:
    pass
control.activate_next_stage()
print("Parachutes fully deployed")

# Prepare for final descent
while surface_altitude() > 200:
    pass
control.activate_next_stage()
print("Preparing for final descent")

# Final landing maneuvers
update_focus()

print("Braking engines activated")
control.activate_next_stage()  # Separate the last stage
vessel.auto_pilot.disengage()  # Disengage autopilot
control.rcs = True
control.sas = True
control.sas_mode = conn.space_center.SASMode.retrograde
control.throttle = 0.0725

# Final landing phase
while surface_altitude() > 2:
    pass
control.throttle = 0
control.activate_next_stage()
time.sleep(1)
print("Perseverance detached")
time.sleep(1)
control.throttle = 0.2
control.rcs = True
control.sas = True
time.sleep(5)

# Final message upon successful landing
print("Landing successful! Welcome to Duna!")
