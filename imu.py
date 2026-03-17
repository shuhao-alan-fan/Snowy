import smbus
import math
import time

# MPU6050 Registers and I2C Address
MPU6050_ADDR = 0x68
PWR_MGMT_1   = 0x6B
ACCEL_XOUT_H = 0x3B
GYRO_XOUT_H  = 0x43

# Initialize the I2C bus
bus = smbus.SMBus(1) # 1 indicates /dev/i2c-1

def init_mpu():
    # Write to power management register to wake up the sensor
    bus.write_byte_data(MPU6050_ADDR, PWR_MGMT_1, 0)

def read_raw_data(addr):
    # Read two bytes (high and low) from the given register address
    high = bus.read_byte_data(MPU6050_ADDR, addr)
    low = bus.read_byte_data(MPU6050_ADDR, addr+1)
    
    # Combine the two bytes to get a 16-bit value
    value = ((high << 8) | low)
    
    # Convert to signed 16-bit integer
    if(value > 32768):
        value = value - 65536
    return value

# Setup variables for the Complementary Filter
pitch = 0.0
roll = 0.0
alpha = 0.98 # Filter tuning parameter
last_time = time.time()

print("Initializing MPU6050...")
init_mpu()
time.sleep(1)
print("Reading Data... Press Ctrl+C to stop.")

try:
    while True:
        # 1. Read Raw Accelerometer Data
        acc_x = read_raw_data(ACCEL_XOUT_H)
        acc_y = read_raw_data(ACCEL_XOUT_H + 2)
        acc_z = read_raw_data(ACCEL_XOUT_H + 4)
        
        # 2. Read Raw Gyroscope Data
        gyro_x = read_raw_data(GYRO_XOUT_H)
        gyro_y = read_raw_data(GYRO_XOUT_H + 2)
        gyro_z = read_raw_data(GYRO_XOUT_H + 4)
        
        # 3. Scale the Raw Data
        # Accelerometer default is +/- 2g (divide by 16384.0)
        ax = acc_x / 16384.0
        ay = acc_y / 16384.0
        az = acc_z / 16384.0
        
        # Gyroscope default is +/- 250 degrees/second (divide by 131.0)
        gx = gyro_x / 131.0
        gy = gyro_y / 131.0
        gz = gyro_z / 131.0
        
        # 4. Calculate Time Delta (dt)
        current_time = time.time()
        dt = current_time - last_time
        last_time = current_time
        
        # 5. Calculate Accelerometer Angles (in degrees)
        # Using atan2 to convert the gravity vectors into absolute angles
        pitch_acc = math.atan2(ay, math.sqrt(ax * ax + az * az)) * 180.0 / math.pi
        roll_acc = math.atan2(-ax, math.sqrt(ay * ay + az * az)) * 180.0 / math.pi
        
        # 6. Apply the Complementary Filter
        # Combine the fast gyro integration with the stable accelerometer gravity vector
        pitch = alpha * (pitch + gx * dt) + (1.0 - alpha) * pitch_acc
        roll = alpha * (roll + gy * dt) + (1.0 - alpha) * roll_acc
        
        # Print the smoothed angles, formatted to 2 decimal places
        print(f"Pitch: {pitch:6.2f} | Roll: {roll:6.2f}")
        
        # Run the loop at approximately 50Hz
        time.sleep(0.02)

except KeyboardInterrupt:
    print("\nData reading stopped.")