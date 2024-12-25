import krpc
import time
import math

# Connect to the kRPC server
conn = krpc.connect(name="Align Planets")
vessel = conn.space_center.active_vessel

# Stream for the current universal time (UT) in KSP
current_ut = conn.add_stream(getattr, conn.space_center, "ut")

# Function to calculate the magnitude (length) of a vector
def calculate_vector_length(vector):
    """
    Calculate the magnitude of a vector.

    :param vector: A 3-element tuple representing the vector.
    :return: The magnitude of the vector.
    """
    return math.sqrt(sum(component ** 2 for component in vector))

# Function to calculate the angle between two vectors
def calculate_angle_between_vectors(vector1, vector2):
    """
    Calculate the angle between two vectors.

    :param vector1: The first vector as a 3-element tuple.
    :param vector2: The second vector as a 3-element tuple.
    :return: The angle in radians between the two vectors.
    """
    magnitude1 = calculate_vector_length(vector1)
    magnitude2 = calculate_vector_length(vector2)
    dot_product = sum(vector1[i] * vector2[i] for i in range(3))
    return math.acos(dot_product / (magnitude1 * magnitude2))

# Function to subtract two vectors
def subtract_vectors(vector1, vector2):
    """
    Subtract one vector from another.

    :param vector1: The first vector as a 3-element tuple.
    :param vector2: The second vector as a 3-element tuple.
    :return: The resulting vector as a tuple.
    """
    return tuple(vector1[i] - vector2[i] for i in range(3))

# Define celestial bodies and their parameters
sun = vessel.orbit.body.orbit.body  # The Sun (parent body of Kerbin and Duna)
sun_reference_frame = sun.reference_frame
kerbin = sun.satellites[2]  # Kerbin (3rd satellite of the Sun)
duna = sun.satellites[3]  # Duna (4th satellite of the Sun)

# Functions to retrieve the positions of Kerbin and Duna in the Sun's reference frame
def get_kerbin_position():
    """
    Get the position of Kerbin in the Sun's reference frame.
    """
    return kerbin.position(sun_reference_frame)

def get_duna_position():
    """
    Get the position of Duna in the Sun's reference frame.
    """
    return duna.position(sun_reference_frame)

# Calculate the required phase angle for the transfer
kerbin_semi_major_axis = kerbin.orbit.semi_major_axis
duna_semi_major_axis = duna.orbit.semi_major_axis
transfer_time_ratio = 0.5 * kerbin_semi_major_axis / duna_semi_major_axis + 0.5
required_phase_angle = math.pi * (1 - transfer_time_ratio ** (3 / 2))  # In radians

print(f"Required phase angle: {math.degrees(required_phase_angle):.2f}°")

# Main loop to monitor and control warp to align the planets
while True:
    # Current phase angle between Duna and Kerbin
    current_phase_angle = calculate_angle_between_vectors(get_kerbin_position(), get_duna_position())

    # Measure the change in phase angle over a short time interval
    previous_angle = calculate_angle_between_vectors(get_kerbin_position(), get_duna_position())
    time.sleep(0.2)  # Short delay for angle update
    current_angle = calculate_angle_between_vectors(get_kerbin_position(), get_duna_position())

    # Determine warp speed adjustments based on phase angle
    if previous_angle > current_angle:
        current_phase_angle_deg = math.degrees(current_phase_angle)
        required_phase_angle_deg = math.degrees(required_phase_angle)

        # Adjust warp factor if close to alignment
        if required_phase_angle_deg < current_phase_angle_deg < 46 and conn.space_center.rails_warp_factor != 5:
            conn.space_center.rails_warp_factor = 5
            print(f"Adjusting warp to factor 5. Current phase angle: {current_phase_angle_deg:.2f}°")
            time.sleep(5)
        elif f"{current_phase_angle_deg:.2f}" == f"{required_phase_angle_deg:.2f}":
            conn.space_center.rails_warp_factor = 0
            print("Phase angle alignment achieved. Stopping warp.")
            break
        elif not (required_phase_angle_deg < current_phase_angle_deg < 46) and conn.space_center.rails_warp_factor != 7:
            conn.space_center.rails_warp_factor = 7
            print(f"Adjusting warp to factor 7. Current phase angle: {current_phase_angle_deg:.2f}°")
            time.sleep(5)
    else:
        if conn.space_center.rails_warp_factor != 7:
            conn.space_center.rails_warp_factor = 7
            print("Current phase angle is decreasing. Increasing warp to factor 7.")
            time.sleep(5)

    # Short delay before the next iteration
    time.sleep(0.05)

print("Planetary alignment complete. Ready for transfer!")
