#!/usr/bin/env python3
"""
Si7021 Temperature and Humidity Sensor Driver
for Raspberry Pi Zero W

This driver implements I2C communication MANUALLY using GPIO bit-banging
(no I2C libraries or hardware I2C interface required)
"""

import time
from typing import Tuple, Optional

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("Error: RPi.GPIO not installed")
    print("Install with: sudo apt-get install python3-rpi.gpio")
    exit(1)


class ManualI2C:
    """
    Manual I2C implementation using GPIO bit-banging
    Based on I2C protocol specification
    """
    
    def __init__(self, scl_pin: int, sda_pin: int, frequency: int = 100000):
        """
        Initialize manual I2C interface
        
        Args:
            scl_pin: GPIO pin number for SCL (clock)
            sda_pin: GPIO pin number for SDA (data)
            frequency: I2C clock frequency in Hz (default: 100kHz)
        """
        self.scl_pin = scl_pin
        self.sda_pin = sda_pin
        
        # Calculate delay for clock timing (half period)
        self.delay = 1.0 / (2.0 * frequency)
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Initialize pins as outputs, both HIGH (idle state)
        GPIO.setup(self.scl_pin, GPIO.OUT)
        GPIO.setup(self.sda_pin, GPIO.OUT)
        GPIO.output(self.scl_pin, GPIO.HIGH)
        GPIO.output(self.sda_pin, GPIO.HIGH)
        
        time.sleep(0.001)
    
    def _scl_low(self):
        """Set SCL pin LOW"""
        GPIO.output(self.scl_pin, GPIO.LOW)
        time.sleep(self.delay)
    
    def _scl_high(self):
        """Set SCL pin HIGH"""
        GPIO.output(self.scl_pin, GPIO.HIGH)
        time.sleep(self.delay)
    
    def _sda_low(self):
        """Set SDA pin LOW"""
        GPIO.setup(self.sda_pin, GPIO.OUT)
        GPIO.output(self.sda_pin, GPIO.LOW)
        time.sleep(self.delay)
    
    def _sda_high(self):
        """Set SDA pin HIGH (release)"""
        GPIO.setup(self.sda_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        time.sleep(self.delay)
    
    def _read_sda(self) -> bool:
        """Read SDA pin state"""
        GPIO.setup(self.sda_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        time.sleep(self.delay / 2)
        return GPIO.input(self.sda_pin)
    
    def start_condition(self):
        """
        Generate I2C START condition
        START: SDA goes LOW while SCL is HIGH
        """
        self._sda_high()
        self._scl_high()
        self._sda_low()
        self._scl_low()
    
    def stop_condition(self):
        """
        Generate I2C STOP condition
        STOP: SDA goes HIGH while SCL is HIGH
        """
        self._sda_low()
        self._scl_high()
        self._sda_high()
    
    def write_bit(self, bit: bool):
        """
        Write a single bit to I2C bus
        
        Args:
            bit: Bit value to write (True/False or 1/0)
        """
        if bit:
            self._sda_high()
        else:
            self._sda_low()
        
        self._scl_high()
        self._scl_low()
    
    def read_bit(self) -> bool:
        """
        Read a single bit from I2C bus
        
        Returns:
            Bit value read (True/False)
        """
        self._sda_high()  # Release SDA
        self._scl_high()
        bit = self._read_sda()
        self._scl_low()
        return bit
    
    def write_byte(self, byte: int) -> bool:
        """
        Write a byte to I2C bus
        
        Args:
            byte: Byte value to write (0-255)
            
        Returns:
            True if ACK received, False if NACK
        """
        # Write 8 bits, MSB first
        for i in range(8):
            bit = (byte >> (7 - i)) & 0x01
            self.write_bit(bit)
        
        # Read ACK/NACK bit
        ack = not self.read_bit()  # ACK is LOW
        return ack
    
    def read_byte(self, ack: bool = True) -> int:
        """
        Read a byte from I2C bus
        
        Args:
            ack: Send ACK after reading (True) or NACK (False)
            
        Returns:
            Byte value read (0-255)
        """
        byte = 0
        
        # Read 8 bits, MSB first
        for i in range(8):
            bit = self.read_bit()
            byte = (byte << 1) | (1 if bit else 0)
        
        # Send ACK or NACK
        self.write_bit(not ack)  # ACK is LOW, NACK is HIGH
        
        return byte
    
    def write(self, address: int, data: bytes) -> bool:
        """
        Write data to I2C device
        
        Args:
            address: 7-bit I2C device address
            data: Bytes to write
            
        Returns:
            True if successful, False otherwise
        """
        self.start_condition()
        
        # Write address with WRITE bit (0)
        if not self.write_byte((address << 1) | 0):
            self.stop_condition()
            return False
        
        # Write data bytes
        for byte in data:
            if not self.write_byte(byte):
                self.stop_condition()
                return False
        
        self.stop_condition()
        return True
    
    def read(self, address: int, length: int) -> bytes:
        """
        Read data from I2C device
        
        Args:
            address: 7-bit I2C device address
            length: Number of bytes to read
            
        Returns:
            Bytes read from device
        """
        self.start_condition()
        
        # Write address with READ bit (1)
        if not self.write_byte((address << 1) | 1):
            self.stop_condition()
            raise IOError("Failed to address device for reading")
        
        # Read data bytes
        data = []
        for i in range(length):
            # Send ACK for all bytes except last (send NACK for last byte)
            ack = (i < length - 1)
            byte = self.read_byte(ack)
            data.append(byte)
        
        self.stop_condition()
        return bytes(data)
    
    def write_read(self, address: int, write_data: bytes, read_length: int) -> bytes:
        """
        Write then read from I2C device (repeated start)
        
        Args:
            address: 7-bit I2C device address
            write_data: Bytes to write
            read_length: Number of bytes to read
            
        Returns:
            Bytes read from device
        """
        # Write phase
        self.start_condition()
        
        if not self.write_byte((address << 1) | 0):
            self.stop_condition()
            raise IOError("Failed to address device for writing")
        
        for byte in write_data:
            if not self.write_byte(byte):
                self.stop_condition()
                raise IOError("Failed to write data")
        
        # Read phase (repeated start)
        self.start_condition()
        
        if not self.write_byte((address << 1) | 1):
            self.stop_condition()
            raise IOError("Failed to address device for reading")
        
        data = []
        for i in range(read_length):
            ack = (i < read_length - 1)
            byte = self.read_byte(ack)
            data.append(byte)
        
        self.stop_condition()
        return bytes(data)
    
    def cleanup(self):
        """Cleanup GPIO"""
        GPIO.cleanup([self.scl_pin, self.sda_pin])


class Si7021:
    """
    Driver for Si7021 Temperature and Humidity Sensor
    Uses manual I2C bit-banging implementation
    """
    
    # I2C Address (fixed)
    SI7021_ADDRESS = 0x40
    
    # Command Codes (from Si7021 datasheet)
    CMD_MEASURE_RH_HOLD = 0xE5
    CMD_MEASURE_RH_NO_HOLD = 0xF5
    CMD_MEASURE_TEMP_HOLD = 0xE3
    CMD_MEASURE_TEMP_NO_HOLD = 0xF3
    CMD_READ_TEMP_FROM_RH = 0xE0
    CMD_RESET = 0xFE
    CMD_WRITE_USER_REG = 0xE6
    CMD_READ_USER_REG = 0xE7
    CMD_WRITE_HEATER_REG = 0x51
    CMD_READ_HEATER_REG = 0x11
    
    # Measurement delays (in seconds)
    DELAY_MEASURE_RH_12BIT = 0.030
    DELAY_MEASURE_TEMP_14BIT = 0.015
    DELAY_RESET = 0.020
    
    # User Register bits
    USER_REG_RESOLUTION_MASK = 0x81
    USER_REG_VDDS = 0x40
    USER_REG_HTRE = 0x04
    
    # Resolution settings
    RESOLUTION_RH12_TEMP14 = 0x00
    RESOLUTION_RH8_TEMP12 = 0x01
    RESOLUTION_RH10_TEMP13 = 0x80
    RESOLUTION_RH11_TEMP11 = 0x81
    
    def __init__(self, scl_pin: int = 3, sda_pin: int = 2):
        """
        Initialize the Si7021 sensor with manual I2C
        
        Args:
            scl_pin: GPIO pin for SCL (default: GPIO 3)
            sda_pin: GPIO pin for SDA (default: GPIO 2)
        """
        self.i2c = ManualI2C(scl_pin, sda_pin)
        self.address = self.SI7021_ADDRESS
        
        # Verify sensor is present
        if not self._check_device():
            raise RuntimeError(f"Si7021 sensor not found at address 0x{self.address:02X}")
        
        # Reset sensor
        self.reset()
    
    def _check_device(self) -> bool:
        """Check if device is present"""
        try:
            self.i2c.write(self.address, bytes([self.CMD_READ_USER_REG]))
            time.sleep(0.001)
            data = self.i2c.read(self.address, 1)
            return True
        except:
            return False
    
    def _crc8(self, data: bytes) -> int:
        """
        Calculate CRC-8 checksum
        Polynomial: x^8 + x^5 + x^4 + 1 (0x131)
        """
        crc = 0x00
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x131
                else:
                    crc = crc << 1
            crc &= 0xFF
        return crc
    
    def _measure_no_hold(self, command: int, delay: float) -> int:
        """Perform measurement using No Hold Master Mode"""
        # Send measurement command
        self.i2c.write(self.address, bytes([command]))
        
        # Wait for measurement
        time.sleep(delay)
        
        # Read measurement data (2 bytes + CRC)
        max_retries = 20
        for attempt in range(max_retries):
            try:
                data = self.i2c.read(self.address, 3)
                break
            except:
                time.sleep(0.005)
        else:
            raise RuntimeError("Failed to read measurement data")
        
        # Verify CRC
        if self._crc8(data[:2]) != data[2]:
            raise RuntimeError("CRC check failed")
        
        # Convert to 16-bit value
        raw_value = (data[0] << 8) | data[1]
        return raw_value
    
    def reset(self):
        """Perform soft reset"""
        self.i2c.write(self.address, bytes([self.CMD_RESET]))
        time.sleep(self.DELAY_RESET)
    
    def read_humidity(self) -> float:
        """
        Read relative humidity
        
        Returns:
            Relative humidity in percent (0-100%)
        """
        raw_humidity = self._measure_no_hold(
            self.CMD_MEASURE_RH_NO_HOLD,
            self.DELAY_MEASURE_RH_12BIT
        )
        
        # Convert using datasheet formula: RH = ((125 * raw) / 65536) - 6
        humidity = ((125.0 * raw_humidity) / 65536.0) - 6.0
        humidity = max(0.0, min(100.0, humidity))
        
        return humidity
    
    def read_temperature(self) -> float:
        """
        Read temperature
        
        Returns:
            Temperature in degrees Celsius
        """
        raw_temp = self._measure_no_hold(
            self.CMD_MEASURE_TEMP_NO_HOLD,
            self.DELAY_MEASURE_TEMP_14BIT
        )
        
        # Convert using datasheet formula: Temp = ((175.72 * raw) / 65536) - 46.85
        temperature = ((175.72 * raw_temp) / 65536.0) - 46.85
        
        return temperature
    
    def read_temperature_from_humidity(self) -> float:
        """Read temperature from previous humidity measurement"""
        self.i2c.write(self.address, bytes([self.CMD_READ_TEMP_FROM_RH]))
        time.sleep(0.002)
        
        data = self.i2c.read(self.address, 2)
        raw_temp = (data[0] << 8) | data[1]
        
        temperature = ((175.72 * raw_temp) / 65536.0) - 46.85
        return temperature
    
    def read_both(self) -> Tuple[float, float]:
        """
        Read both humidity and temperature efficiently
        
        Returns:
            Tuple of (humidity, temperature)
        """
        humidity = self.read_humidity()
        temperature = self.read_temperature_from_humidity()
        return humidity, temperature
    
    def read_user_register(self) -> int:
        """Read user register"""
        self.i2c.write(self.address, bytes([self.CMD_READ_USER_REG]))
        time.sleep(0.001)
        data = self.i2c.read(self.address, 1)
        return data[0]
    
    def write_user_register(self, value: int):
        """Write user register"""
        self.i2c.write(self.address, bytes([self.CMD_WRITE_USER_REG, value & 0xFF]))
        time.sleep(0.001)
    
    def set_resolution(self, resolution: int):
        """Set measurement resolution"""
        user_reg = self.read_user_register()
        user_reg &= ~self.USER_REG_RESOLUTION_MASK
        user_reg |= (resolution & self.USER_REG_RESOLUTION_MASK)
        self.write_user_register(user_reg)
    
    def get_resolution(self) -> int:
        """Get current resolution"""
        user_reg = self.read_user_register()
        return user_reg & self.USER_REG_RESOLUTION_MASK
    
    def enable_heater(self, enable: bool = True):
        """Enable or disable on-chip heater"""
        user_reg = self.read_user_register()
        if enable:
            user_reg |= self.USER_REG_HTRE
        else:
            user_reg &= ~self.USER_REG_HTRE
        self.write_user_register(user_reg)
    
    def is_heater_enabled(self) -> bool:
        """Check if heater is enabled"""
        user_reg = self.read_user_register()
        return bool(user_reg & self.USER_REG_HTRE)
    
    def set_heater_level(self, level: int):
        """Set heater current level (0-15)"""
        level = max(0, min(15, level))
        self.i2c.write(self.address, bytes([self.CMD_WRITE_HEATER_REG, level & 0x0F]))
        time.sleep(0.001)
    
    def get_heater_level(self) -> int:
        """Get current heater level"""
        self.i2c.write(self.address, bytes([self.CMD_READ_HEATER_REG]))
        time.sleep(0.001)
        data = self.i2c.read(self.address, 1)
        return data[0] & 0x0F
    
    def read_serial_number(self) -> Tuple[int, int]:
        """
        Read 64-bit serial number
        
        Returns:
            Tuple of (serial_a, serial_b) - two 32-bit values
        """
        # Read first part
        data1 = self.i2c.write_read(self.address, bytes([0xFA, 0x0F]), 8)
        
        # Read second part
        data2 = self.i2c.write_read(self.address, bytes([0xFC, 0xC9]), 6)
        
        # Combine into two 32-bit values
        serial_a = (data1[0] << 24) | (data1[2] << 16) | (data1[4] << 8) | data1[6]
        serial_b = (data2[0] << 24) | (data2[1] << 16) | (data2[3] << 8) | data2[4]
        
        return serial_a, serial_b
    
    def read_firmware_revision(self) -> int:
        """
        Read firmware revision
        
        Returns:
            Firmware revision (0xFF = v1.0, 0x20 = v2.0)
        """
        data = self.i2c.write_read(self.address, bytes([0x84, 0xB8]), 1)
        return data[0]
    
    def cleanup(self):
        """Cleanup GPIO"""
        self.i2c.cleanup()
    
    def __del__(self):
        """Cleanup on deletion"""
        try:
            self.cleanup()
        except:
            pass


def main():
    """
    Example usage of the Si7021 driver with manual I2C
    """
    print("Si7021 Temperature + Humidity Sensor Test")
    print("Manual I2C Bit-Banging Implementation")
    print("=" * 55)
    
    try:
        # Initialize sensor
        # Using GPIO 3 for SCL and GPIO 2 for SDA (default I2C pins)
        print("Initializing Si7021 sensor...")
        sensor = Si7021(scl_pin=3, sda_pin=2)
        print("✓ Si7021 sensor initialized successfully!")
        print()
        
        # Read sensor information
        print("Sensor Information:")
        print("-" * 55)
        
        # Read serial number
        try:
            serial_a, serial_b = sensor.read_serial_number()
            print(f"Serial Number: 0x{serial_a:08X}{serial_b:08X}")
        except Exception as e:
            print(f"Serial Number: Could not read ({e})")
        
        # Read firmware revision
        try:
            firmware = sensor.read_firmware_revision()
            fw_version = "1.0" if firmware == 0xFF else "2.0"
            print(f"Firmware Version: {fw_version} (0x{firmware:02X})")
        except Exception as e:
            print(f"Firmware Version: Could not read ({e})")
        
        # Read user register
        user_reg = sensor.read_user_register()
        print(f"User Register: 0x{user_reg:02X}")
        
        # Get resolution
        resolution = sensor.get_resolution()
        res_map = {
            0x00: "RH: 12-bit, Temp: 14-bit",
            0x01: "RH: 8-bit, Temp: 12-bit",
            0x80: "RH: 10-bit, Temp: 13-bit",
            0x81: "RH: 11-bit, Temp: 11-bit"
        }
        print(f"Resolution: {res_map.get(resolution, 'Unknown')}")
        
        # Check heater status
        heater_enabled = sensor.is_heater_enabled()
        print(f"Heater: {'Enabled' if heater_enabled else 'Disabled'}")
        
        print()
        print("=" * 55)
        print()
        
        # Continuous measurement
        print("Starting continuous measurements (Ctrl+C to stop)...")
        print()
        print("Time      | Temp (°C) | Temp (°F) | Humidity (%)")
        print("-" * 55)
        
        measurement_count = 0
        
        while True:
            try:
                # Read both values
                humidity, temperature = sensor.read_both()
                
                # Convert to Fahrenheit
                temp_f = (temperature * 1.8) + 32.0
                
                # Get current time
                current_time = time.strftime("%H:%M:%S")
                
                # Display
                print(f"{current_time} | {temperature:7.2f}  | {temp_f:7.2f}  | {humidity:7.2f}")
                
                measurement_count += 1
                
                # Show count every 10 measurements
                if measurement_count % 10 == 0:
                    print(f"  [{measurement_count} measurements taken]")
                
                # Wait before next measurement
                time.sleep(2)
                
            except Exception as e:
                print(f"  Error reading sensor: {e}")
                time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n")
        print("=" * 55)
        print("Measurement stopped by user")
        print(f"Total measurements: {measurement_count}")
        print("=" * 55)
    
    except RuntimeError as e:
        print(f"\n✗ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check wiring connections:")
        print("   - VIN  → Pi Pin 1 (3.3V)")
        print("   - GND  → Pi Pin 6 (GND)")
        print("   - SCL  → Pi Pin 5 (GPIO 3)")
        print("   - SDA  → Pi Pin 3 (GPIO 2)")
        print("2. Verify sensor is powered")
        print("3. Check for loose connections")
        print("4. Try different GPIO pins if needed")
    
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\nCleaning up GPIO...")
        try:
            sensor.cleanup()
        except:
            GPIO.cleanup()
        print("Done!")


if __name__ == "__main__":
    main()