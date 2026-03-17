import smbus
import time

# MPU6050 Registers and I2C Address
MPU6050_ADDR = 0x68
PWR_MGMT_1   = 0x6B
ACCEL_XOUT_H = 0x3B

# Initialize the I2C bus
bus = smbus.SMBus(1)

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

print("Initializing MPU6050...")
init_mpu()
time.sleep(1)
print("Streaming Acceleration Data... Press Ctrl+C to stop.")

try:
    while True:
        # 1. Read Raw Accelerometer Data from the 6 sequential registers
        acc_x = read_raw_data(ACCEL_XOUT_H)
        acc_y = read_raw_data(ACCEL_XOUT_H + 2)
        acc_z = read_raw_data(ACCEL_XOUT_H + 4)
        
        # 2. Scale the Raw Data
        # Accelerometer default sensitivity is +/- 2g. We divide by 16384.0 to get standard g-forces.
        ax_g = acc_x / 16384.0
        ay_g = acc_y / 16384.0
        az_g = acc_z / 16384.0
        
        # Print the acceleration vectors, formatted to 3 decimal places
        print(f"Accel X: {ax_g:6.3f} g | Accel Y: {ay_g:6.3f} g | Accel Z: {az_g:6.3f} g")
        
        # Run at approximately 20Hz for easy reading in the terminal
        time.sleep(0.05)

except KeyboardInterrupt:
    print("\nData stream stopped.")