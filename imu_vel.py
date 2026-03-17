import smbus
import time

# MPU6050 Registers and Addresses
MPU6050_ADDR = 0x68
ACCEL_XOUT_H = 0x3B
PWR_MGMT_1 = 0x6B

# Sensitivity for +/- 2g range
ACCEL_SENSITIVITY = 16384.0
GRAVITY = 9.81

# Initialize I2C (Bus 1 is standard for Raspberry Pi)
bus = smbus.SMBus(1)

# Wake up the MPU6050 (it starts in sleep mode)
bus.write_byte_data(MPU6050_ADDR, PWR_MGMT_1, 0)

def read_raw_accel_x():
    """Reads the 16-bit raw X-axis acceleration data."""
    high = bus.read_byte_data(MPU6050_ADDR, ACCEL_XOUT_H)
    low = bus.read_byte_data(MPU6050_ADDR, ACCEL_XOUT_H + 1)
    val = (high << 8) | low
    return val - 65536 if val > 32768 else val

def calibrate_imu(samples=1000):
    """Calculates the static resting error (bias) of the sensor."""
    print("Calibrating... Keep the sensor perfectly still.")
    offset = 0
    for _ in range(samples):
        offset += read_raw_accel_x()
        time.sleep(0.002) # 2ms delay between samples
    return offset / samples

def main():
    # 1. Find the zero-error bias
    accel_offset = calibrate_imu()
    print(f"Calibration complete. Offset: {accel_offset:.2f}\n")

    # 2. Initialize state variables
    v0 = 0.0  # Initial velocity in m/s
    last_time = time.time()
    last_print_time = last_time

    print("Starting integration. Press Ctrl+C to stop.")

    try:
        while True:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time

            # 3. Read raw data and remove the static offset
            raw_accel = read_raw_accel_x()
            clean_accel_raw = raw_accel - accel_offset

            # 4. Convert raw units to m/s^2
            accel_ms2 = (clean_accel_raw / ACCEL_SENSITIVITY) * GRAVITY

            if abs(accel_ms2) < 0.15: 
                accel_ms2 = 0.0
                
            # 5. Integrate: v(t) = v0 + a*dt
            v_t = v0 + (accel_ms2 * dt)

            # 6. Pass v_t forward to the next loop iteration (t = n+1)
            v0 = v_t

            # 7. Output the speed every 1 second
            if current_time - last_print_time >= 1.0:
                print(f"Current Speed: {v_t:.4f} m/s")
                last_print_time = current_time

            # Small delay to set a stable sampling rate (~100Hz)
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\nIntegration stopped by user.")

if __name__ == "__main__":
    main()