from scipy import integrate
import numpy as np
import math
import json
import os

SIMULATE_TIME = 140

# Constants
GRAVITY_KERBIN = 9.82  # Gravitational acceleration on Kerbin (m/s^2)

# Mass parameters
INITIAL_MASS = 379_739  # Initial mass of the rocket with fuel (kg)
STAGE1_MASS = 156_859  # Mass of the rocket after booster separation with fuel (kg)

# Solid Rocket Boosters (SRBs)
SRB_THRUST = 678_240  # Thrust of SRB engines (N)
SRB_COUNT = 4  # Number of SRBs
SRB_ISP = 225  # Specific impulse of SRBs (s)
SRB_BURN_TIME = 105.48  # Burn time of SRBs (s)

# Second Stage
STAGE2_THRUST = 1_000_000  # Thrust of second stage engines (N)
STAGE2_ENGINE_COUNT = 2  # Number of engines in the second stage
STAGE2_ISP = 315  # Specific impulse of second stage engines (s)
STAGE2_BURN_TIME = 116.94  # Burn time of the second stage (s)


def write_values():
    """
    Write simulation results to a JSON file for analysis.
    """
    os.makedirs("records", exist_ok=True)
    flight_data = {
        "speed": total_speed.tolist(),
        "altitude": altitude.tolist(),
        "angle": [math.degrees(alpha(h)) for h in altitude],
        "mass": [mass_at_time(t) for t in time],
        "time": time.tolist(),
    }
    with open("records/model_data.json", "w") as file:
        json.dump(flight_data, file, indent=4)


def alpha(altitude):
    """
    Compute the pitch angle of the rocket based on altitude.
    """
    max_turn_angle = math.radians(90)  # Maximum angle (90 degrees)
    turn_start_altitude = 1_000  # Altitude to start gravity turn (m)
    turn_end_altitude = 45_000  # Altitude to complete gravity turn (m)

    if altitude < turn_start_altitude:
        return 0
    elif turn_start_altitude <= altitude <= turn_end_altitude:
        progress = (altitude - turn_start_altitude) / (turn_end_altitude - turn_start_altitude)
        return math.radians(90 * progress)
    else:
        return max_turn_angle


def effective_isp(time):
    """
    Calculate the effective specific impulse of the rocket at a given time.
    """
    if time < SRB_BURN_TIME:
        return (
            (SRB_THRUST * SRB_COUNT + STAGE2_THRUST * STAGE2_ENGINE_COUNT) /
            (SRB_THRUST * SRB_COUNT / SRB_ISP + STAGE2_THRUST * STAGE2_ENGINE_COUNT / STAGE2_ISP) *
            GRAVITY_KERBIN
        )
    else:
        return (
            (STAGE2_THRUST * STAGE2_ENGINE_COUNT) /
            (STAGE2_THRUST * STAGE2_ENGINE_COUNT / STAGE2_ISP) *
            GRAVITY_KERBIN
        )


def mass_at_time(time):
    """
    Calculate the mass of the rocket at a given time.
    """
    if time < SRB_BURN_TIME:
        return INITIAL_MASS - (SRB_THRUST * SRB_COUNT + STAGE2_THRUST * STAGE2_ENGINE_COUNT) / effective_isp(time) * time
    else:
        return STAGE1_MASS - (STAGE2_THRUST * STAGE2_ENGINE_COUNT) / effective_isp(time) * (time - SRB_BURN_TIME)


def thrust_at_time(time):
    """
    Calculate the thrust of the rocket at a given time.
    """
    if time < SRB_BURN_TIME:
        return SRB_THRUST * SRB_COUNT + STAGE2_THRUST * STAGE2_ENGINE_COUNT
    else:
        return STAGE2_THRUST * STAGE2_ENGINE_COUNT


def gravity_at_altitude(altitude):
    """
    Calculate the gravitational acceleration at a given altitude.
    """
    planet_radius = 600_000  # Radius of Kerbin (m)
    return GRAVITY_KERBIN * (planet_radius ** 2) / (planet_radius + altitude) ** 2


def drag_force(velocity, altitude):
    """
    Calculate the aerodynamic drag on the rocket.
    """
    air_density_at_sea_level = 1.225  # Air density at sea level (kg/m^3)
    scale_height = 5600  # Atmospheric scale height (m)
    drag_coefficient = 1.5  # Drag coefficient
    reference_area = 18  # Reference cross-sectional area (m^2)

    air_density = air_density_at_sea_level * np.exp(-altitude / scale_height)
    return 0.5 * drag_coefficient * air_density * velocity ** 2 * reference_area


def system_equations(time, state):
    """
    Define the system of equations for the rocket's motion.
    """
    vertical_velocity, altitude, horizontal_velocity = state

    dv_dt = (
        (thrust_at_time(time) * np.cos(alpha(altitude)) - drag_force(vertical_velocity, altitude)) /
        mass_at_time(time) -
        gravity_at_altitude(altitude)
    )
    dh_dt = vertical_velocity
    du_dt = (
        (thrust_at_time(time) * np.sin(alpha(altitude)) - drag_force(horizontal_velocity, altitude)) /
        mass_at_time(time)
    )

    return [dv_dt, dh_dt, du_dt]


# Initial conditions
initial_vertical_velocity = 0  # Vertical velocity (m/s)
initial_altitude = 0  # Altitude (m)
initial_horizontal_velocity = 0  # Horizontal velocity (m/s)

# Time simulation range
simulation_time = np.linspace(0, SIMULATE_TIME, 1250)

# Solve the system of differential equations
solution = integrate.solve_ivp(
    system_equations,
    t_span=(0, SIMULATE_TIME),
    y0=[initial_vertical_velocity, initial_altitude, initial_horizontal_velocity],
    t_eval=simulation_time,
    method="RK45"
)

# Extract results
time = solution.t
vertical_velocity = solution.y[0]
horizontal_velocity = solution.y[2]
total_speed = np.sqrt(vertical_velocity ** 2 + horizontal_velocity ** 2)
altitude = solution.y[1]

# Save results to a file
write_values()
