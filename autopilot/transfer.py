import krpc
import time
import math

# Connect to the kRPC server and get the active vessel
conn = krpc.connect(name="Interplanetary Transfer")
vessel = conn.space_center.active_vessel

# Stream for the current universal time (UT) in KSP
current_ut = conn.add_stream(getattr, conn.space_center, "ut")

# Function to calculate the magnitude (length) of a vector
def calculate_vector_length(vector):
    return math.sqrt(sum(component ** 2 for component in vector))

# Function to calculate the angle between two vectors
def calculate_angle_between_vectors(vector1, vector2):
    magnitude1 = calculate_vector_length(vector1)
    magnitude2 = calculate_vector_length(vector2)
    dot_product = sum(vector1[i] * vector2[i] for i in range(3))
    return math.acos(dot_product / (magnitude1 * magnitude2))

# Function to subtract two vectors
def subtract_vectors(vector1, vector2):
    return tuple(vector1[i] - vector2[i] for i in range(3))

# Define celestial bodies and reference frames
sun = vessel.orbit.body.orbit.body  # The Sun (parent body of the vessel's orbit)
sun_reference_frame = sun.reference_frame
kerbin = sun.satellites[2]  # Kerbin is the 3rd satellite of the Sun
duna = sun.satellites[3]  # Duna is the 4th satellite of the Sun

# Function to calculate a Hohmann transfer delta-v
def calculate_hohmann_transfer(mu, r1, r2):
    """
    Calculate the required delta-v for a Hohmann transfer.

    :param mu: Gravitational parameter of the central body
    :param r1: Semi-major axis of the initial orbit
    :param r2: Semi-major axis of the target orbit
    :return: Tuple of (delta_v1, delta_v2)
    """
    semi_major_axis = (r1 + r2) / 2
    delta_v1 = math.sqrt(mu / r1) * (math.sqrt(r2 / semi_major_axis) - 1)
    delta_v2 = math.sqrt(mu / r2) * (1 - math.sqrt(r1 / semi_major_axis))
    return delta_v1, delta_v2

# Calculate the required velocities for the transfer
v_exit_kerbin, v_arrival_duna = calculate_hohmann_transfer(
    sun.gravitational_parameter,
    kerbin.orbit.semi_major_axis,
    duna.orbit.semi_major_axis
)

# Calculate Kerbin escape velocity and required delta-v
v_escape_velocity = math.sqrt(
    v_exit_kerbin ** 2 + 2 * kerbin.gravitational_parameter *
    (1 / vessel.orbit.semi_major_axis - 1 / kerbin.sphere_of_influence)
)
v_orbital_velocity = math.sqrt(kerbin.gravitational_parameter / vessel.orbit.semi_major_axis)
delta_v = v_escape_velocity - v_orbital_velocity
print(f"Delta V for the maneuver: {delta_v:.2f} m/s")

# Calculate burn time for the maneuver
thrust = vessel.available_thrust
isp = vessel.specific_impulse * 9.82  # Effective exhaust velocity
initial_mass = vessel.mass
final_mass = initial_mass / math.exp(delta_v / isp)
flow_rate = thrust / isp
burn_time = (initial_mass - final_mass) / flow_rate
print(f"Engine burn time: {burn_time:.2f} seconds")

# Calculate required exit angle from Kerbin's sphere of influence (SOI)
eccentricity = 1 + vessel.orbit.semi_major_axis * v_exit_kerbin ** 2 / kerbin.gravitational_parameter
required_exit_angle = math.acos(-1 / eccentricity)
print(f"Required exit angle: {math.degrees(required_exit_angle):.2f}°")

# Calculate angular velocity of the vessel's orbit
angular_velocity = math.sqrt(kerbin.gravitational_parameter / (vessel.orbit.semi_major_axis ** 3))

# Calculate the current angle and time until the maneuver
theta0 = math.pi - calculate_angle_between_vectors(
    kerbin.velocity(sun_reference_frame),
    subtract_vectors(vessel.position(sun_reference_frame), kerbin.position(sun_reference_frame))
)
time.sleep(0.1)  # Pause briefly to get updated data
theta1 = math.pi - calculate_angle_between_vectors(
    kerbin.velocity(sun_reference_frame),
    subtract_vectors(vessel.position(sun_reference_frame), kerbin.position(sun_reference_frame))
)
print(f"Current angle: {math.degrees(theta1):.2f}°")

# Determine the time to the required exit angle
if theta0 > theta1:
    if math.pi >= theta1 >= required_exit_angle:
        delta_angle = theta1 - required_exit_angle
        time_to_angle = delta_angle / angular_velocity
        if time_to_angle - burn_time / 2 <= 0:
            delta_angle += 2 * math.pi
    else:
        delta_angle = 2 * math.pi + theta1 - required_exit_angle
else:
    delta_angle = 2 * math.pi - (theta1 + required_exit_angle)

phase_angle = math.degrees(calculate_angle_between_vectors(
    kerbin.position(sun_reference_frame), duna.position(sun_reference_frame))
)
print(f"Current phase angle: {phase_angle:.2f}°")

delta_angle_deg = math.degrees(delta_angle)
print(f"Required angle to travel: {delta_angle_deg:.2f}°")

time_to_angle = delta_angle / angular_velocity
minutes_to_angle = int(time_to_angle // 60)
seconds_to_angle = time_to_angle % 60
print(f"Time until maneuver: {minutes_to_angle} minutes and {seconds_to_angle:.2f} seconds")

# Create a maneuver node for the transfer
maneuver_node = vessel.control.add_node(current_ut() + time_to_angle, prograde=delta_v)
print("Maneuver node created.")

# Set Duna as the target
conn.space_center.target_body = duna
print("Target set to Duna.")

# Prepare for the maneuver
vessel.auto_pilot.disengage()
vessel.control.sas = True
time.sleep(1)
vessel.control.sas_mode = conn.space_center.SASMode.maneuver
print("SAS set to maneuver mode.")

# Warp to the maneuver start
warp_start_time = current_ut() + time_to_angle - burn_time / 2
print("Maneuver executed and ready for fine-tuning.")
