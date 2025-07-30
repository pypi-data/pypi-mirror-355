import utime
import machine


def get_sys_info() -> tuple:
    """
    Get system information including core frequency and temperature.
    
    :return: tuple of (frequency, temperature)
    """

def get_mem_info() -> tuple:
    """
    Get memory usage information of TiCLE.
    
    :return: tuple of (free, used, total) memory in bytes
    """

def get_fs_info(path='/') -> tuple:
    """
    Get filesystem information for the given path.
    
    :param path: Path to check filesystem info for.
    :return: tuple of (total, used, free, usage percentage)
    """


class WifiManager:
    def __init__(self, *, iface=None):
        """
        A class to manage WiFi connections on the TiCLE.
        This class provides methods to scan for available networks, connect to a network, disconnect, and get the IP address.
        It uses the `network` module to handle WiFi operations.

        :param iface: Optional network interface to use. If not provided, it defaults to the STA_IF interface.
        """
           
    def scan(self) -> list[tuple[str,int,int,int]]:
        """
        Scan for available WiFi networks.
        
        :return: List of tuples containing (SSID, RSSI, channel, security).
        """

    def available_ssids(self) -> list[str]:
        """
        Get a list of available SSIDs from the scanned access points.
        
        :return: List of unique SSIDs found in the scanned access points.
        """

    def connect(self, ssid: str, password: str, timeout: float = 20.0) -> bool:
        """
        Connect to a WiFi network with the given SSID and password.
        
        :param ssid: SSID of the WiFi network to connect to.
        :param password: Password for the WiFi network.
        :param timeout: Timeout in seconds for the connection attempt (default is 20 seconds).
        :return: True if connected successfully, False otherwise.
        """

    def disconnect(self) -> None:
        """
        Disconnect from the currently connected WiFi network.
        This method will disconnect the WiFi interface if it is currently connected.
        """
        if self.iface.isconnected():
            self.iface.disconnect()
            utime.sleep_ms(100)
    
    def ifconfig(self) -> tuple | None:
        """
        Get the IP address of the connected WiFi network.     
        
        :return: Tuple containing (ip, netmask, gateway, dns) if connected, None otherwise.
        """

    @property
    def is_connected(self) -> bool:
        """
        Check if the WiFi interface is currently connected to a network.
        
        :return: True if connected, False otherwise.
        """

    @property
    def ip(self) -> str | None:
        """
        Get the IP address of the connected WiFi network.
        
        :return: IP address as a string if connected, None otherwise.
        """


def pLed():
    def __init__(self):
        """
        Basic Led control class built into Pico2W.
        
        :return: Pin object for the built-in LED("WL_GPIO0").
        """

    def on(self):
        """
        Turn on the built-in LED.
        This method sets the built-in LED pin to HIGH, turning on the LED.
        """

    def off(self):
        """
        Turn off the built-in LED.
        This method sets the built-in LED pin to LOW, turning off the LED.
        """

    def toggle(self):
        """
        Toggle the state of the built-in LED.
        This method switches the built-in LED pin between HIGH and LOW, effectively toggling the LED state.
        """

    def value(self) -> int:
        """
        Get the current state of the built-in LED.
        
        :return: The current value of the built-in LED pin (0 for OFF, 1 for ON).
        """

    def value(self, v:int) -> None:
        """
        Set the state of the built-in LED.
        
        :param v: The value to set for the built-in LED pin (0 for OFF, 1 for ON).
        :raises ValueError: If the value is not 0 or 1.
        """

class Din:
    LOW         = 0
    HIGH        = 1
    
    PULL_DOWN   = machine.Pin.PULL_DOWN
    PULL_UP     = machine.Pin.PULL_UP
    CB_FALLING  = machine.Pin.IRQ_FALLING
    CB_RISING   = machine.Pin.IRQ_RISING
    
    
    class _ReadOnly:
        def __init__(self, pin:int, pull:int|None, trigger:int|None, callback:callable|None):
            """
            A class to read a digital input pin.

            :param pin: GPIO pin number
            :param pull: Pull-up or pull-down configuration
            :param trigger: Interrupt trigger type.
            :param handler: Callback function for the interrupt
            """

        def get(self) -> int:
            """
            Get the value of the pin.
            
            :return: Pin value (0 or 1).
            """

    def __init__(self, pins:tuple, pull:int|None=None, trigger:int|None=0, callback:function|None=None):
        """
        A class to read digital input pins.
        This class allows reading the state of multiple GPIO pins as digital inputs.
        It provides a convenient way to read the state of multiple input pins simultaneously.
        The class supports pull-up and pull-down configurations, as well as callback triggers for pin state changes.
        
        if trigger and callback are provided, the callback function will be called when the pin state changes.
        callback function signature is `def on_user(pin:int)`:  
          pin is the GPIO pin number that triggered the callback.

        :param pins: Tuple of GPIO pin numbers to be used as digital inputs.
        :param pull: Pull-up or pull-down configuration (default is None).
        :param trigger: Callback trigger type (default is None).
        :param callback: Callback function for the trigger (default is None).
        """
    
    def __getitem__(self, idx:int) -> int:
        """
        Get the value of a specific pin.
        
        param idx: Index of the pin (0 to len(pins)-1).
        :return: Pin value (0 or 1).
        """

    def __len__(self) -> int:
        """
        Get the number of digital input pins.
        
        :return: Number of pins.
        """        


class Dout:
    LOW         = 0
    HIGH        = 1
    PULL_DOWN   = machine.Pin.PULL_DOWN
    PULL_UP     = machine.Pin.PULL_UP
    
    class _WriteOnly:
        def __init__(self, pin:int, pull:int|None=None):
            """
            A class to control a single digital output pin.
            This class allows setting the state of a GPIO pin to either LOW or HIGH.
            It is used internally by the Dout class to manage individual output pins.
            
            :param pin: GPIO pin number to be used as a digital output.
            :param pull: Pull-up or pull-down configuration (default is None).
            """
            
        def get(self) -> int:
            """
            Get the current value of the pin.
            
            :return: Pin value (0 or 1).
            """
        
        def set(self, value:int) -> None:
            """
            Set the value of the pin to LOW or HIGH.
            
            :param value: Pin value to set (0 for LOW, 1 for HIGH).
            :raises ValueError: If the value is not 0 or 1.
            """

    class _Group:
        def __init__(self, pins:list):
            """
            A class to manage a group of digital output pins.
            This class allows setting the state of multiple GPIO pins simultaneously.
            It provides a convenient way to control multiple output pins with a single value.
            
            :param pins: List of Dout._WriteOnly objects to be managed as a group.
            """
            
        @property
        def value(self) -> int:
            """
            Get the value of the group of pins.
            If all pins have the same value, it returns that value.
            If the values are mixed, it returns None.
            
            :return: Pin value (0 or 1) if all pins have the same value, None otherwise.
            """
        
        @value.setter
        def value(self, v:int) -> None:
            """
            Set the value of all pins in the group to the specified value.
            
            :param v: Pin value to set (0 for LOW, 1 for HIGH).
            :raises ValueError: If the value is not 0 or 1.
            """
                
        def map(self, fn) -> None:
            """
            Apply a function to all pins in the group.
            This method allows you to apply a function to each pin in the group.
            
            :param fn: Function to apply to each pin.
            :raises TypeError: If the provided function is not callable.
            """

    def __init__(self, pins:tuple[int, ...], pull:int|None=None):
        """
        A class to control digital output pins.
        This class allows setting the state of multiple GPIO pins to either LOW or HIGH.
        It provides a convenient way to control multiple output pins simultaneously.
        
        :param pins: Tuple of GPIO pin numbers to be used as digital outputs.
        :param pull: Pull-up or pull-down configuration (default is None).
        :raises ValueError: If the provided pins are not valid GPIO pin numbers.
        """
        self.__pins = [Dout._WriteOnly(pin, pull) for pin in pins]
        self.all = Dout._Group(self.__pins)
        
    def __getitem__(self, idx:int) -> int:
        """
        Get the value of a specific pin.
        
        :param idx: Index of the pin (0 to len(pins)-1).
        :return: Pin value (0 or 1).
        """

    def __setitem__(self, idx:int, value:int) -> None:
        """
        Set the value of a specific pin to LOW or HIGH.
        
        :param idx: Index of the pin (0 to len(pins)-1).
        :param value: Pin value to set (0 for LOW, 1 for HIGH).
        :raises ValueError: If the value is not 0 or 1.
        """

    def __len__(self) -> int:
        """
        Get the number of digital output pins.    
        
        :return: Number of pins.
        """


class Adc():
    def __init__(self, pins:tuple, period:int=0, callback:function=None):
        """
        A class to read analog values from ADC pins.
 
        If period and callback are provided, the callback function will be called repeatedly at the specified interval.
        The callback function signature is `def on_user(pin:int, voltage:float, raw_value:int)`: 
            pin is the GPIO pin number.
            voltage is the raw ADC value converted to voltage.
            raw_value is the raw ADC value (0-65535).

        :param pins: Tuple of GPIO pin numbers (26, 27, or 28).
        :param period: Interval in milliseconds to call the callback function.
        :param callback: Callback function to be called at the specified interval.
        """
            
    def __getitem__(self, idx:int) -> tuple:
        """
        Read the analog value from the ADC pin.
        resolution = 3.3V/4096 = 0.0008056640625V/bit. (0.806mV/bit)
        Therefore, the voltage can be accurately represented up to three decimal places.

        :param idx: Index of the pin (0 to len(pins)-1).
        :return: Tuple of (voltage, raw_value).
        """

    def __len__(self) -> int:
        """
        Get the number of ADC pins.
        
        :return: Number of pins.
        """


class Pwm:
    class _Pin:
        def __init__(self, pin:int):
            """
            A class to control a single PWM pin.
            This class allows setting the frequency, period, and duty cycle of a PWM signal on a specific pin.
            It is used internally by the Pwm class to manage individual PWM pins.

            :param pin: GPIO pin number for PWM output.
            """

        @property
        def freq(self) -> int:
            """
            Frequency [Hz].
            This property gets or sets the frequency of the PWM signal.            

            :return: Frequency in Hz."""

        @freq.setter
        def freq(self, value_hz:int):
            """
            Set the frequency of the PWM pin.
            This method sets the frequency of the PWM signal on the pin.
            It calculates the period in microseconds based on the frequency and updates the PWM pin accordingly.

            :param value_hz: Frequency in Hz.
            :raises ValueError: If the frequency is less than or equal to 0.
            """

        @property
        def period(self) -> int:
            """
            Period [us].
            This property gets or sets the period of the PWM signal in microseconds.

            :return: Period in microseconds.
            """

        @period.setter
        def period(self, us:int):
            """
            Set the period of the PWM signal in microseconds.

            :param us: Period in microseconds.
            :raises ValueError: If the period is less than or equal to 0.
            """

        @property
        def duty(self) -> int:
            """
            Duty cycle [%].
            This property gets or sets the duty cycle of the PWM signal as a percentage (0-100).

            :return: Duty cycle percentage.
            """

        @duty.setter
        def duty(self, pct:int):
            """
            Set the duty cycle of the PWM signal as a percentage (0-100).

            :param pct: Duty cycle percentage (0-100).
            :raises ValueError: If the percentage is less than 0 or greater than 100.
            """

        @property
        def duty_raw(self) -> int:
            """
            Duty cycle in raw value [0-65535].
            This property gets or sets the duty cycle of the PWM signal in raw value (0-65535).

            :return: Duty cycle in raw value.
            """

        @duty_raw.setter
        def duty_raw(self, raw:int):
            """
            Set the duty cycle of the PWM signal in raw value (0-65535).

            :param raw: Duty cycle in raw value (0-65535).
            :raises ValueError: If the raw value is less than 0 or greater than 65535.
            """

        @property
        def duty_us(self) -> int:
            """
            Duty cycle in microseconds [0-period_us].
            This property gets or sets the duty cycle of the PWM signal in microseconds (0 to period_us).

            :return: Duty cycle in microseconds.
            """

        @duty_us.setter
        def duty_us(self, us:int):
            """
            Set the duty cycle of the PWM signal in microseconds (0 to period_us).

            :param us: Duty cycle in microseconds (0 to period_us).
            :raises ValueError: If the microseconds value is less than 0 or greater than period_us.
            """

        @property
        def enable(self) -> bool:
            """
            Enable or disable the PWM signal.
            This property gets or sets whether the PWM signal is enabled or disabled.

            :return: True if enabled, False if disabled.
            """

        @enable.setter
        def enable(self, flag:bool):
            """
            Enable or disable the PWM signal.

            :param flag: True to enable the PWM signal, False to disable it.
            """
        
        def deinit(self) -> None:
            """
            Deinitialize the PWM pin.
            This method stops the PWM signal and releases the resources associated with the pin.
            """
  

    class _Group:
        def __init__(self, pins:tuple):
            """
            A class to manage a group of PWM pins.
            This class allows setting the frequency, period, and duty cycle for multiple PWM pins simultaneously.
            It provides a convenient way to control multiple PWM outputs with the same settings.

            :param pins: Tuple of PwmPin objects to be managed as a group.
            """

        @property
        def freq(self) -> int:
            """
            Frequency [Hz].
            This property gets or sets the frequency of the PWM signal for all pins in the group.
            
            :return: Frequency in Hz.
            """

        @freq.setter
        def freq(self, hz:int):
            """
            Set the frequency of the PWM signal for all pins in the group.

            :param hz: Frequency in Hz.
            :raises ValueError: If the frequency is less than or equal to 0.
            """

        @property
        def period(self) -> int:
            """
            Period [us].
            This property gets or sets the period of the PWM signal for all pins in the group.

            :return: Period in microseconds.
            """

        @period.setter
        def period(self, us: int):
            """
            Set the period of the PWM signal for all pins in the group.

            :param us: Period in microseconds.
            :raises ValueError: If the period is less than or equal to 0.
            """

        @property
        def duty(self) -> int:
            """
            Duty cycle [%].
            This property gets or sets the duty cycle of the PWM signal for all pins in the group.

            :return: Duty cycle percentage.
            """

        @duty.setter
        def duty(self, pct:int):
            """
            Set the duty cycle of the PWM signal for all pins in the group.

            :param pct: Duty cycle percentage (0-100).
            :raises ValueError: If the percentage is less than 0 or greater than 100.
            """

        @property
        def enable(self) -> bool:
            """
            Enable or disable the PWM signal for all pins in the group.
            This property gets or sets whether the PWM signal is enabled or disabled for all pins in the group.

            :return: True if enabled, False if disabled.
            """

        @enable.setter
        def enable(self, flag:bool):
            """
            Enable or disable the PWM signal for all pins in the group.

            :param flag: True to enable the PWM signal, False to disable it.
            """

        def map(self, fn:callable) -> None:
            """
            Apply a function to all PWM pins in the group.
            This method allows you to apply a function to each PWM pin in the group.

            :param fn: Function to apply to each PWM pin.
            :raises TypeError: If the provided function is not callable.
            """
        
        def deinit(self) -> None:
            """
            Deinitialize all PWM pins in the group.
            This method stops the PWM signal and releases the resources associated with all pins in the group.
            """

    def __init__(self, pins:tuple):
        """
        A class to control PWM (Pulse Width Modulation) on TiCLE.
        This class allows setting the frequency, period, and duty cycle of PWM signals.
        It can be used to control devices like motors, LEDs, and other peripherals that require PWM signals.
        The class supports multiple pins for PWM output, allowing simultaneous control of multiple devices.
        
        :param pins: Tuple of GPIO pin numbers to be used for PWM output.
        :raises ValueError: If the frequency is less than or equal to 0.
        """
        self.__pins = [Pwm._Pin(pin) for pin in pins]
        self.all = Pwm._Group(self.__pins)
        
    def __getitem__(self, idx: int) -> _Pin:
        """
        Get a specific PWM pin by index.
        :param idx: Index of the pin (0 to len(pins)-1).
        :return: PwmPin object for the specified pin.
        """

    def __len__(self):
        """
        Get the number of PWM pins.
        :return: Number of PWM pins.
        """

    def __iter__(self):
        """
        Iterate over the PWM pins.
        :return: An iterator over the PwmPin objects.
        """


class Button:
    def __init__(self, double_click_ms:int=260, long_press_ms:int=800, debounce_ms:int=20):
        """
        A simple button class to handle single click, double click and long press events.
    
        :param double_click_ms: Time in milliseconds to consider a double click.
        :param long_press_ms: Time in milliseconds to consider a long press.
        :param debounce_ms: Time in milliseconds to debounce the button press.
        """

    @property
    def on_clicked(self) -> callable:
        """
        Callback function for single click event.
        
        :return: The callback function.
        """

    @on_clicked.setter
    def on_clicked(self, fn:callable):
        """
        Set the callback function for single click event.
        
        :param fn: The callback function to be called on single click.
        
        It should be defined as:
        def on_my_clicked():
            # Handle single click event
             pass
        """

    @property
    def on_double_clicked(self) -> callable:
        """
        Callback function for double click event.
        
        :return: The callback function.
        """

    @on_double_clicked.setter
    def on_double_clicked(self, fn:callable):
        """
        Set the callback function for double click event.
        
        :param fn: The callback function to be called on double click.
        """

    @property
    def on_long_pressed(self) -> callable:
        """
        Callback function for long press event.
        
        :return: The callback function.
        """

    @on_long_pressed.setter
    def on_long_pressed(self, fn:callable):
        """
        Set the callback function for long press event.
        
        :param fn: The callback function to be called on long press.
        """


def i2cdetect(bus:int, show:bool=False) -> list | None:
    """
    Detect I2C devices on the specified bus.

    :param bus: The I2C bus number. 0 or 1.
    :param show: If True, it prints the entire status, if False, it returns only the recognized device addresses in a list.
    :return: A list of detected I2C devices.
    """


class I2c:
    def __init__(self, scl:int, sda:int, addr:int, freq:int=400_000):
        """
        I2C class for TiCLE.
        This class is a wrapper around the machine.I2C class to provide a more user-friendly interface.
        It automatically detects the I2C bus based on the provided SDA and SCL pins.

        :param scl: The SCL pin number.
        :param sda: The SDA pin number.
        :param freq: The frequency of the I2C bus (default is 400kHz).
        """

    def read_u8(self, reg:int) -> int:
        """
        Read an unsigned 8-bit value from the specified register.

        :param reg: The register address to read from.
        :return: The value read from the register.
        """

    def read_u16(self, reg:int, *, little_endian:bool=True) -> int:
        """
        Read an unsigned 16-bit value from the specified register.

        :param reg: The register address to read from.
        :param little_endian: If True, read the value in little-endian format, otherwise in big-endian format.
        :return: The value read from the register.
        """

    def write_u8(self, reg:int, val:int) -> None:
        """
        Write an unsigned 8-bit value to the specified register.

        :param reg: The register address to write to.
        :param val: The value to write to the register (0-255).
        """

    def write_u16(self, reg:int, val:int, *, little_endian:bool=True) -> None:
        """
        Write an unsigned 16-bit value to the specified register.

        :param reg: The register address to write to.
        :param val: The value to write to the register (0-65535).
        :param little_endian: If True, write the value in little-endian format, otherwise in big-endian format.
        """

    def readfrom(self, nbytes:int, *, stop:bool=True) -> bytes:
        """
        Read a specified number of bytes from the I2C device.

        :param nbytes: The number of bytes to read.
        :param stop: If True, send a stop condition after reading.
        :return: The bytes read from the I2C device.
        """

    def readinto(self, buf:bytearray, *, stop:bool=True) -> int:
        """
        Read bytes into a buffer from the I2C device.

        :param buf: The buffer to read the bytes into.
        :param stop: If True, send a stop condition after reading.
        :return: The number of bytes read into the buffer.
        """

    def readfrom_mem(self, reg:int, nbytes:int, *, addrsize:int=8) -> bytes:
        """
        Read a specified number of bytes from a specific register in the I2C device.

        :param reg: The register address to read from.
        :param nbytes: The number of bytes to read.
        :param addrsize: The address size in bits (default is 8 bits).
        :return: The bytes read from the specified register.
        """

    def readfrom_mem_into(self, reg:int, buf:bytearray, *, addrsize:int=8) -> int:
        """
        Read bytes from a specific register in the I2C device into a buffer.

        :param reg: The register address to read from.
        :param buf: The buffer to read the bytes into.
        :param addrsize: The address size in bits (default is 8 bits).
        :return: The number of bytes read into the buffer.
        """

    def writeto(self, buf:bytes, *, stop:bool=True) -> int:
        """
        Write bytes to the I2C device.

        :param buf: The bytes to write to the I2C device.
        :param stop: If True, send a stop condition after writing.
        :return: The number of bytes written to the I2C device.
        """

    def writeto_mem(self, reg:int, buf:bytes, *, addrsize:int=8) -> int:
        """
        Write bytes to a specific register in the I2C device.

        :param reg: The register address to write to.
        :param buf: The bytes to write to the specified register.
        :param addrsize: The address size in bits (default is 8 bits).
        :return: The number of bytes written to the specified register.
        """


class ReplSerial:
    def __init__(self, timeout:float|None=None, *, bufsize:int=512, poll_ms:int=10):
        """
        This class provides a way to read from and write to the REPL (Read-Eval-Print Loop) using a ring buffer.
        It allows for non-blocking reads, reading until a specific pattern, and writing data to the REPL.   

        :param timeout: The timeout in seconds for read operations. If None, it will block until data is available.
        - timeout=None : blocking read
        - timeout=0    : non-blocking read
        - timeout>0    : wait up to timeout seconds
        :param bufsize: The size of the ring buffer (default is 512 bytes).
        :param poll_ms: The polling interval in milliseconds for reading data from the REPL (default is 10 ms).
        """

    @property
    def timeout(self):
        """
        Get the timeout for read operations.
        - timeout=None : blocking read
        - timeout=0    : non-blocking read
        - timeout>0    : wait up to timeout seconds
        """
    
    @timeout.setter
    def timeout(self, value:float|None):
        """
        Set the timeout for read operations.
        - timeout=None : blocking read
        - timeout=0    : non-blocking read
        - timeout>0    : wait up to timeout seconds

        :param value: The timeout value in seconds. If None, it will block indefinitely.
        """

    def read(self, size:int=1) -> bytes:
        """
        Read `size` bytes from the REPL buffer.
        If `size` is less than or equal to 0, it returns an empty byte string.
        If `size` is greater than the available data, it waits for data to become available based on the timeout.

        :param size: The number of bytes to read (default is 1).
        :return: The read bytes as a byte string.
        """   

    def read_until(self, expected:bytes=b'\n', max_size:int|None=None) -> bytes:
        """
        Read from the REPL buffer until the expected byte sequence is found, the maximum size is reached, or a timeout occurs.
        If `max_size` is specified, it limits the amount of data read.
        If `expected` is not found within the timeout, it returns an empty byte string.
        
        - timeout=0     : non-blocking -> return only when pattern or max_size is satisfied, else b''
        - timeout>0     : wait up to timeout, then same as above or b'' on timeout
        - timeout=None  : blocking until pattern or max_size

        :param expected: The expected byte sequence to look for (default is b'\n').
        :param max_size: The maximum size of data to read (default is None, no limit).
        :return: The data read from the REPL buffer, including the expected sequence if found.
        """


    def write(self, data:bytes) -> int:
        """
        Write `data` to the REPL UART.
        If `data` is not bytes or bytearray, it raises a TypeError.

        :param data: The data to write (must be bytes or bytearray).
        :return: The number of bytes written.
        """

    def close(self):
        """
        Close the REPL serial connection and deinitialize the timer.
        This method stops the periodic timer and releases resources.
        """


def input(prompt:str="") -> str:
    """
    Blocking input() replacement with:
      - UTF-8 decoding (1-4 bytes per char)
      - <-, -> arrow cursor movement
      - Backspace deletes before cursor
      - Deletes at cursor
      - Proper insertion anywhere in the line
      
    :param prompt: The prompt string to display before reading input (default is an empty string).
    :return: The input string entered by the user.
    """
