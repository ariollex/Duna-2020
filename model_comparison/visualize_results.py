from math import inf
import matplotlib.pyplot as plt
import numpy as np
import json
import os

# Load data from JSON files
with open("records/flight_data.json", "r") as f:
    ksp_data = json.load(f)  # Data from Kerbal Space Program
with open("records/model_data.json", "r") as f:
    model_data = json.load(f)  # Data from the mathematical model

# Extract data from JSON
speed_ksp = ksp_data["speed"]
altitude_ksp = ksp_data["altitude"]
angle_ksp = ksp_data["angle"]
mass_ksp = ksp_data["mass"]
time_ksp = ksp_data["time"]

speed = model_data["speed"]
altitude = model_data["altitude"]
angle = model_data["angle"]
mass = model_data["mass"]
time = model_data["time"]

# Interpolate KSP data onto the time grid of the mathematical model
speed_ksp_interp = np.interp(time, time_ksp, speed_ksp)
altitude_ksp_interp = np.interp(time, time_ksp, altitude_ksp)
angle_ksp_interp = np.interp(time, time_ksp, angle_ksp)
mass_ksp_interp = np.interp(time, time_ksp, mass_ksp)

# Calculate absolute errors
speed_error = [abs(s1 - s2) for s1, s2 in zip(speed, speed_ksp_interp)]
altitude_error = [abs(a1 - a2) for a1, a2 in zip(altitude, altitude_ksp_interp)]
angle_error = [abs(ang1 - ang2) for ang1, ang2 in zip(angle, angle_ksp_interp)]
mass_error = [abs(m1 - m2) for m1, m2 in zip(mass, mass_ksp_interp)]

# Function to calculate percentage errors
def calculate_percent_error(model, interpolated):
    """
    Calculate percentage error between model and interpolated data.
    """
    return [(abs(m - i) / m * 100) if m != 0 else 0 for m, i in zip(model, interpolated)]

# Calculate percentage errors
speed_error_percent = calculate_percent_error(speed, speed_ksp_interp)
altitude_error_percent = calculate_percent_error(altitude, altitude_ksp_interp)
angle_error_percent = calculate_percent_error(angle, angle_ksp_interp)
mass_error_percent = calculate_percent_error(mass, mass_ksp_interp)

def max_percent_error(time, model, interpolated, graph_name):
    """
    Calculate maximum percentage error between model and interpolated data.
    """
    maximum = -inf
    result = (0, 0)
    for t, m, i in zip(time, model, interpolated):
        if abs(m - i) >= maximum:
            maximum = abs(m - i)
            result = (t, abs(m - i) / m * 100 if m != 0 else 0)
    print(f"The maximum error for {graph_name} is {result[1]}% at time t={result[0]} s.")

max_percent_error(time, speed, speed_ksp_interp, "V(t)")
max_percent_error(time, altitude, altitude_ksp_interp, "H(t)")
max_percent_error(time, angle, angle_ksp_interp, "α(t)")
max_percent_error(time, mass, mass_ksp_interp, "M(t)")

# Generate plots
# Ensure output directory exists
os.makedirs("output", exist_ok=True)

# Plotting functions
def plot_speed_time():
    plt.title("Зависимость скорости от времени")
    plt.plot(time, speed, label="Мат. модель")
    plt.plot(time, speed_ksp_interp, label="Kerbal Space Program")
    plt.plot(time, speed_error, label="Погрешность", linestyle="--", color="#7edb5c")
    plt.legend()
    plt.grid()
    plt.xlabel("Время, с")
    plt.ylabel("Скорость, м/с")

def plot_altitude_time():
    plt.title("Зависимость высоты от времени")
    plt.plot(time, altitude, label="Мат. модель")
    plt.plot(time, altitude_ksp_interp, label="Kerbal Space Program")
    plt.plot(time, altitude_error, label="Погрешность", linestyle="--", color="#db5c9a")
    plt.legend()
    plt.grid()
    plt.xlabel("Время, с")
    plt.ylabel("Высота, м")

def plot_angle_time():
    plt.title("Зависимость угла наклона от времени")
    plt.plot(time, angle, label="Мат. модель")
    plt.plot(time, angle_ksp_interp, label="Kerbal Space Program")
    plt.plot(time, angle_error, label="Погрешность", linestyle="--", color="#F5D033")
    plt.legend()
    plt.grid()
    plt.xlabel("Время, с")
    plt.ylabel("Угол, °")

def plot_mass_time():
    plt.title("Зависимость массы от времени")
    plt.plot(time, mass, label="Мат. модель")
    plt.plot(time, mass_ksp_interp, label="Kerbal Space Program")
    plt.plot(time, mass_error, label="Погрешность", linestyle="--", color="#33f5f5")
    plt.legend()
    plt.grid()
    plt.xlabel("Время, с")
    plt.ylabel("Масса, кг")

def plot_relative_error():
    plt.title("Относительная погрешность")
    plt.ylim(top=150)
    plt.plot(time, speed_error_percent, label="Скорость", color="#7edb5c")
    plt.plot(time, altitude_error_percent, label="Высота", color="#db5c9a")
    plt.plot(time, angle_error_percent, label="Угол", color="#F5D033")
    plt.plot(time, mass_error_percent, label="Масса", color="#33f5f5")
    plt.legend()
    plt.grid()
    plt.xlabel("Время, с")
    plt.ylabel("Погрешность, %")

# Save individual plots
plt.figure(figsize=(8, 6))
plot_speed_time()
plt.savefig("output/speed_time.png", dpi=300)
plt.close()
plt.figure(figsize=(8, 6))
plot_altitude_time()
plt.savefig("output/altitude_time.png", dpi=300)
plt.close()
plt.figure(figsize=(8, 6))
plot_angle_time()
plt.savefig("output/angle_time.png", dpi=300)
plt.close()
plt.figure(figsize=(8, 6))
plot_mass_time()
plt.savefig("output/mass_time.png", dpi=300)
plt.close()
plt.figure(figsize=(8, 6))
plot_relative_error()
plt.savefig("output/relative_error.png", dpi=300)
plt.close()

# Combined overview plot
plt.figure(figsize=(16, 9))
plt.subplot(2, 3, 1)
plot_speed_time()
plt.subplot(2, 3, 2)
plot_altitude_time()
plt.subplot(2, 3, 3)
plot_angle_time()
plt.subplot(2, 3, 4)
plot_mass_time()
plt.subplot(2, 3, 5)
plot_relative_error()
plt.tight_layout()
plt.savefig("output/comparison_flight_parameters.png", dpi=300)
plt.show()
