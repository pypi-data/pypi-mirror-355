import gc
import re
import usys
import utime
import uos
import uselect

import network
import machine
import micropython

import utools
from utools import ANSIEC


micropython.alloc_emergency_exception_buf(256) 

def get_sys_info() -> tuple:
    """
    Get system information including core frequency and temperature.
    
    :return: tuple of (frequency, temperature)
    """
    freq = machine.freq()

    try:
        machine.Pin(43, machine.Pin.IN)
        TEMP_ADC  = 8
    except ValueError: # rp2350a (pico2w)
        TEMP_ADC  = 4
                         
    raw = machine.ADC(TEMP_ADC).read_u16()
    temp = 27 - ((raw * 3.3 / 65535) - 0.706) / 0.001721
    
    return freq, temp


def get_mem_info() -> tuple:
    """
    Get memory usage information of TiCLE.
    
    :return: tuple of (free, used, total) memory in bytes
    """
    gc.collect()
    
    free = gc.mem_free()
    used = gc.mem_alloc()
    total = free + used
    
    return free, used, total

def get_fs_info(path='/') -> tuple:
    """
    Get filesystem information for the given path.
    
    :param path: Path to check filesystem info for.
    :return: tuple of (total, used, free, usage percentage)
    """
    stats = uos.statvfs(path)
    block_size = stats[0]
    total_blocks = stats[2]
    free_blocks = stats[3]

    total = block_size * total_blocks
    free = block_size * free_blocks
    used = total - free
    usage_pct = round(used / total * 100, 2)

    return total, used, free, usage_pct


class WifiManager:
    def __init__(self, *, iface=None):
        """
        A class to manage WiFi connections on the TiCLE.
        This class provides methods to scan for available networks, connect to a network, disconnect, and get the IP address.
        It uses the `network` module to handle WiFi operations.

        :param iface: Optional network interface to use. If not provided, it defaults to the STA_IF interface.
        """
        self.iface = iface or network.WLAN(network.STA_IF)
        if not self.iface.active():
            self.iface.active(True)
           
    def scan(self) -> list[tuple[str,int,int,int]]:
        """
        Scan for available WiFi networks.
        
        :return: List of tuples containing (SSID, RSSI, channel, security).
        """
        return self.iface.scan()

    def available_ssids(self) -> list[str]:
        """
        Get a list of available SSIDs from the scanned access points.
        
        :return: List of unique SSIDs found in the scanned access points.
        """
        aps = self.scan()
        ssids = set()
        for ap in aps:
            ssid = ap[0].decode('utf-8', 'ignore')
            if ssid:
                ssids.add(ssid)
        return list(ssids)

    def connect(self, ssid: str, password: str, timeout: float = 20.0) -> bool:
        """
        Connect to a WiFi network with the given SSID and password.
        
        :param ssid: SSID of the WiFi network to connect to.
        :param password: Password for the WiFi network.
        :param timeout: Timeout in seconds for the connection attempt (default is 20 seconds).
        :return: True if connected successfully, False otherwise.
        """
        if self.iface.isconnected():
            return True

        self.iface.connect(ssid, password)
        start = utime.ticks_ms()
        while not self.iface.isconnected():
            if utime.ticks_diff(utime.ticks_ms(), start) > int(timeout * 1000):
                return False
            utime.sleep_ms(200)
        return True

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
        if not self.is_connected:
            return None
        return self.iface.ifconfig()

    @property
    def is_connected(self) -> bool:
        """
        Check if the WiFi interface is currently connected to a network.
        
        :return: True if connected, False otherwise.
        """
        return self.iface.isconnected()

    @property
    def ip(self) -> str | None:
        """
        Get the IP address of the connected WiFi network.
        
        :return: IP address as a string if connected, None otherwise.
        """
        if not self.is_connected:
            return None
        return self.iface.ifconfig()[0]


def pLed():
    """
    Basic Led control class built into Pico2W.
    
    :return: Pin object for the built-in LED("WL_GPIO0").
    """
    return machine.Pin("WL_GPIO0", machine.Pin.OUT)


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
            self.__pin = machine.Pin(pin, machine.Pin.IN, pull=pull)
            if trigger != 0 and callback is not None:
                self.__user_callback = callback
                self.__pin.irq(trigger=trigger, handler=self.__callback)

        def __callback(self, pin:machine.Pin):
            """
            Callback function for pin state change.
            This function is called when the pin state changes.
            It extracts the GPIO pin number from the pin object and calls the user-defined callback function.
            :param pin: Pin object that triggered the callback.
            """
            match = re.search(r'GPIO(\d+)', str(pin))
            self.__user_callback(int(match.group(1)))            

        def get(self) -> int: 
            """
            Get the value of the pin.
            
            :return: Pin value (0 or 1).
            """
            return self.__pin.value()

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
        self.__din =[Din._ReadOnly(pin, pull, trigger, callback) for pin in pins]
    
    def __getitem__(self, idx:int) -> int:
        """
        Get the value of a specific pin.
        
        :param idx: Index of the pin (0 to len(pins)-1).
        :return: Pin value (0 or 1).
        """
        return self.__din[idx].get()

    def __len__(self) -> int:
        """
        Get the number of digital input pins.
        
        :return: Number of pins.
        """        
        return len(self.__din)


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
            self.__pin = machine.Pin(pin, machine.Pin.OUT, pull=pull)
            
        def get(self) -> int:
            """
            Get the current value of the pin.
            
            :return: Pin value (0 or 1).
            """
            return self.__pin.value()
        
        def set(self, value:int) -> None:
            """
            Set the value of the pin to LOW or HIGH.
            
            :param value: Pin value to set (0 for LOW, 1 for HIGH).
            :raises ValueError: If the value is not 0 or 1.
            """
            self.__pin.value(value)

    class _Group:
        def __init__(self, pins:list):
            """
            A class to manage a group of digital output pins.
            This class allows setting the state of multiple GPIO pins simultaneously.
            It provides a convenient way to control multiple output pins with a single value.

            :param pins: List of Dout._WriteOnly objects to be managed as a group.
            """
            self.__pins = pins
            
        @property
        def value(self) -> int:
            """
            Get the value of the group of pins.
            If all pins have the same value, it returns that value.
            If the values are mixed, it returns None.

            :return: Pin value (0 or 1) if all pins have the same value, None otherwise.
            """
            vals = {p.get() for p in self.__pins}
            return vals.pop() if len(vals) == 1 else None
        
        @value.setter
        def value(self, v:int) -> None:
            """
            Set the value of all pins in the group to the specified value.

            :param v: Pin value to set (0 for LOW, 1 for HIGH).
            :raises ValueError: If the value is not 0 or 1.
            """
            for p in self.__pins:
                p.set(v)
                
        def map(self, fn) -> None:
            """
            Apply a function to all pins in the group.
            This method allows you to apply a function to each pin in the group.
            
            :param fn: Function to apply to each pin.
            :raises TypeError: If the provided function is not callable.
            """
            for p in self.__pins:
                fn(p)

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
        return self.__pins[idx].get()

    def __setitem__(self, idx:int, value:int) -> None:
        """
        Set the value of a specific pin to LOW or HIGH.
        
        :param idx: Index of the pin (0 to len(pins)-1).
        :param value: Pin value to set (0 for LOW, 1 for HIGH).
        :raises ValueError: If the value is not 0 or 1.
        """
        self.__pins[idx].set(value)

    def __len__(self) -> int:
        """
        Get the number of digital output pins.    
        
        :return: Number of pins.
        """
        return len(self.__pins)


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
        self.__pins = pins
        self.__adc = [machine.ADC(machine.Pin(pin)) for pin in self.__pins]
        if period > 0 and callback:
            self.__callback = callback
            machine.Timer(mode=machine.Timer.PERIODIC, period=period, callback=self.__timer_callback)
    
    def __timer_callback(self, timer):
        """
        Timer callback function to call the user-defined callback function.

        :param timer: Timer object.
        """
        for i in range(len(self.__adc)):
            self.__callback(self.__pins[i], *self[i])
            
    def __getitem__(self, idx:int) -> tuple:
        """
        Read the analog value from the ADC pin.
        resolution = 3.3V/4096 = 0.0008056640625V/bit. (0.806mV/bit)
        Therefore, the voltage can be accurately represented up to three decimal places.
        
        :param idx: Index of the pin (0 to len(pins)-1).
        :return: Tuple of (voltage, raw_value).
        """
        raw = self.__adc[idx].read_u16()
        return round(raw * (3.3 / 65535), 3), raw 

    def __len__(self) -> int:
        """
        Get the number of ADC pins.
        
        :return: Number of pins.
        """
        return len(self.__adc)


class Pwm:
    __FULL_RANGE = 65_535
    __MICROS_PER_SEC = 1_000_000

    class _Pin:
        def __init__(self, pin:int):
            """
            A class to control a single PWM pin.
            This class allows setting the frequency, period, and duty cycle of a PWM signal on a specific pin.
            It is used internally by the Pwm class to manage individual PWM pins.

            :param pin: GPIO pin number for PWM output.
            """
            self.__pin = pin
            self.__pwm = machine.PWM(machine.Pin(self.__pin))
            self.__freq = 0
            self.__enabled = True
            self.__period_us = 0
            self.duty = 0

        def __apply_duty(self):
            """
            Apply the duty cycle to the PWM pin.
            This method sets the duty cycle of the PWM signal on the pin.
            It calculates the raw duty cycle value based on the percentage and updates the PWM pin accordingly.
            """
            raw = int(self.__duty_pct * Pwm.__FULL_RANGE / 100)
            self.__pwm.duty_u16(raw if self.__enabled else 0)

        @property
        def freq(self) -> int:
            """
            Frequency [Hz].
            This property gets or sets the frequency of the PWM signal.
            
            :return: Frequency in Hz."""
            return self.__freq

        @freq.setter
        def freq(self, value_hz:int):
            """
            Set the frequency of the PWM pin.
            This method sets the frequency of the PWM signal on the pin.
            It calculates the period in microseconds based on the frequency and updates the PWM pin accordingly.
            
            :param value_hz: Frequency in Hz.
            :raises ValueError: If the frequency is less than or equal to 0.
            """
            if value_hz <= 0:
                raise ValueError("Frequency must be positive")
            self.__freq = value_hz
            self.__pwm.freq(self.__freq)
            self.__period_us = Pwm.__MICROS_PER_SEC // self.__freq

            self.__apply_duty()

        @property
        def period(self) -> int:
            """
            Period [us].
            This property gets or sets the period of the PWM signal in microseconds.
            
            :return: Period in microseconds.
            """
            return self.__period_us

        @period.setter
        def period(self, us:int):
            """
            Set the period of the PWM signal in microseconds.
            
            :param us: Period in microseconds.
            :raises ValueError: If the period is less than or equal to 0.
            """
            self.freq = Pwm.__MICROS_PER_SEC // us            # re-uses freq setter

        @property
        def duty(self) -> int:
            """
            Duty cycle [%].
            This property gets or sets the duty cycle of the PWM signal as a percentage (0-100).
            :return: Duty cycle percentage.
            """
            return self.__duty_pct

        @duty.setter
        def duty(self, pct:int):
            """
            Set the duty cycle of the PWM signal as a percentage (0-100).
            
            :param pct: Duty cycle percentage (0-100).
            :raises ValueError: If the percentage is less than 0 or greater than 100.
            """
            pct = utools.clamp(pct, 0, 100)
            self.__duty_pct = pct
            self.__apply_duty()

        @property
        def duty_raw(self) -> int:
            """
            Duty cycle in raw value [0-65535].
            This property gets or sets the duty cycle of the PWM signal in raw value (0-65535).
            
            :return: Duty cycle in raw value.
            """
            return self.__pwm.duty_u16()

        @duty_raw.setter
        def duty_raw(self, raw:int):
            """
            Set the duty cycle of the PWM signal in raw value (0-65535).
            
            :param raw: Duty cycle in raw value (0-65535).
            :raises ValueError: If the raw value is less than 0 or greater than 65535.
            """
            raw = utools.clamp(raw, 0, Pwm.__FULL_RANGE)
            self.__duty_pct = round(raw * 100 / Pwm.__FULL_RANGE)
            self.__pwm.duty_u16(raw if self.__enabled else 0)

        @property
        def duty_us(self) -> int:
            """
            Duty cycle in microseconds [0-period_us].
            This property gets or sets the duty cycle of the PWM signal in microseconds (0 to period_us).
            
            :return: Duty cycle in microseconds.
            """
            return int(self.__duty_pct * self.__period_us / 100)

        @duty_us.setter
        def duty_us(self, us:int):
            """
            Set the duty cycle of the PWM signal in microseconds (0 to period_us).
            
            :param us: Duty cycle in microseconds (0 to period_us).
            :raises ValueError: If the microseconds value is less than 0 or greater than period_us.
            """
            us = utools.clamp(us, 0, self.__period_us)
            self.duty = int(us * 100 / self.__period_us)

        @property
        def enable(self) -> bool:
            """
            Enable or disable the PWM signal.
            This property gets or sets whether the PWM signal is enabled or disabled.
            
            :return: True if enabled, False if disabled.
            """
            return self.__enabled

        @enable.setter
        def enable(self, flag:bool):
            """
            Enable or disable the PWM signal.
            
            :param flag: True to enable the PWM signal, False to disable it.
            """
            self.__enabled = bool(flag)
            self.__apply_duty()
        
        def deinit(self) -> None:
            """
            Deinitialize the PWM pin.
            This method stops the PWM signal and releases the resources associated with the pin.
            """
            self.freq = 0
            self.enable = False
            self.__pwm.deinit()
            self.__pwm = None
  

    class _Group:
        def __init__(self, pins:tuple):
            """
            A class to manage a group of PWM pins.
            This class allows setting the frequency, period, and duty cycle for multiple PWM pins simultaneously.
            It provides a convenient way to control multiple PWM outputs with the same settings.

            :param pins: Tuple of PwmPin objects to be managed as a group.
            """
            self.__pins = pins

        @property
        def freq(self) -> int:
            """
            Frequency [Hz].
            This property gets or sets the frequency of the PWM signal for all pins in the group.
            
            :return: Frequency in Hz.
            """
            vals = {p.freq for p in self.__pins}
            return vals.pop() if len(vals) == 1 else None

        @freq.setter
        def freq(self, hz:int):
            """
            Set the frequency of the PWM signal for all pins in the group.
            
            :param hz: Frequency in Hz.
            :raises ValueError: If the frequency is less than or equal to 0.
            """
            for p in self.__pins:
                p.freq = hz

        @property
        def period(self) -> int:
            """
            Period [us].
            This property gets or sets the period of the PWM signal for all pins in the group.
            
            :return: Period in microseconds.
            """
            vals = {p.period for p in self.__pins}
            return vals.pop() if len(vals) == 1 else None

        @period.setter
        def period(self, us:int):
            """
            Set the period of the PWM signal for all pins in the group.
            
            :param us: Period in microseconds.
            :raises ValueError: If the period is less than or equal to 0.
            """
            for p in self.__pins:
                p.period = us

        @property
        def duty(self) -> int:
            """
            Duty cycle [%].
            This property gets or sets the duty cycle of the PWM signal for all pins in the group.
            
            :return: Duty cycle percentage.
            """
            vals = {p.duty for p in self.__pins}
            return vals.pop() if len(vals) == 1 else None

        @duty.setter
        def duty(self, pct:int):
            """
            Set the duty cycle of the PWM signal for all pins in the group.
            
            :param pct: Duty cycle percentage (0-100).
            :raises ValueError: If the percentage is less than 0 or greater than 100.
            """
            for p in self.__pins:
                p.duty = pct

        @property
        def enable(self) -> bool:
            """
            Enable or disable the PWM signal for all pins in the group.
            This property gets or sets whether the PWM signal is enabled or disabled for all pins in the group.
            
            :return: True if enabled, False if disabled.
            """
            vals = {p.enable for p in self.__pins}
            return vals.pop() if len(vals) == 1 else None

        @enable.setter
        def enable(self, flag:bool):
            """
            Enable or disable the PWM signal for all pins in the group.
            :param flag: True to enable the PWM signal, False to disable it.
            """
            for p in self.__pins:
                p.enable = flag

        def map(self, fn:callable) -> None:
            """
            Apply a function to all PWM pins in the group.
            This method allows you to apply a function to each PWM pin in the group.
            
            :param fn: Function to apply to each PWM pin.
            :raises TypeError: If the provided function is not callable.
            """
            for p in self.__pins:
                fn(p)
        
        def deinit(self) -> None:
            """
            Deinitialize all PWM pins in the group.
            This method stops the PWM signal and releases the resources associated with all pins in the group.
            """
            for p in self.__pins:
                p.deinit()
            self.__pins = None


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
        return self.__pins[idx]

    def __len__(self):
        """
        Get the number of PWM pins.
        
        :return: Number of PWM pins.
        """
        return len(self.__pins)

    def __iter__(self):
        """
        Iterate over the PWM pins.
        
        :return: An iterator over the PwmPin objects.
        """
        return iter(self.__pins)


class Button:
    def __init__(self, double_click_ms:int=260, long_press_ms:int=800, debounce_ms:int=20):
        """
        A simple button class to handle single click, double click and long press events.
        
        :param double_click_ms: Time in milliseconds to consider a double click.
        :param long_press_ms: Time in milliseconds to consider a long press.
        :param debounce_ms: Time in milliseconds to debounce the button press.
        """
        self.__DBL = double_click_ms
        self.__LNG = long_press_ms
        self.__DEB = debounce_ms

        self.__click_waiting = False
        self.__long_fired = False
        self.__last_edge = 0

        self.__tm_click = machine.Timer(-1)
        self.__tm_long = machine.Timer(-1)

        self.__on_clicked = None
        self.__on_double_clicked = None
        self.__on_long_pressed = None

        self.__sw = Din((2,), Din.PULL_DOWN, Din.CB_RISING|Din.CB_FALLING, self.__callback)

    @property
    def on_clicked(self) -> callable:
        """
        Callback function for single click event.
        
        :return: The callback function.
        """
        return self.__on_clicked

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
        self.__on_clicked = fn

    @property
    def on_double_clicked(self) -> callable:
        """
        Callback function for double click event.
        
        :return: The callback function.
        """
        return self.__on_double_clicked

    @on_double_clicked.setter
    def on_double_clicked(self, fn:callable):
        """
        Set the callback function for double click event.
        
        :param fn: The callback function to be called on double click.
        """
        self.__on_double_clicked = fn

    @property
    def on_long_pressed(self) -> callable:
        """
        Callback function for long press event.
        
        :return: The callback function.
        """
        return self.__on_long_pressed

    @on_long_pressed.setter
    def on_long_pressed(self, fn:callable):
        """
        Set the callback function for long press event.
        
        :param fn: The callback function to be called on long press.
        """
        self.__on_long_pressed = fn

    def __safe_call(self, fn):
        """
        Safely calls the provided function if it is not None.
        
        :param fn: Function to call.
        """
        if fn:
            micropython.schedule(lambda _: fn(), 0)
    
    def __cb_single_click(self, _t):
        """
        Callback for single click event.
        
        :param _t: Timer object (not used).
        """
        self.__click_waiting = False
        self.__safe_call(self.__on_clicked)

    def __cb_long_press(self, _t):
        """
        Callback for long press event.
        
        :param _t: Timer object (not used).
        """
        if self.__sw[0]:
            self.__long_fired = True
            self.__safe_call(self.__on_long_pressed)
                                    
    def __callback(self, _):
        """
        Callback for button state change.
        
        :param _: Unused parameter.
        """
        now = utime.ticks_ms()

        if utime.ticks_diff(now, self.__last_edge) < self.__DEB:
            return
        self.__last_edge = now

        if self.__sw[0]:
            self.__long_fired = False
            self.__tm_long.init(period=self.__LNG, mode=machine.Timer.ONE_SHOT, callback=self.__cb_long_press)
            return

        self.__tm_long.deinit()

        if self.__long_fired:
            return

        if self.__click_waiting:
            self.__tm_click.deinit()
            self.__click_waiting = False
            self.__safe_call(self.__on_double_clicked)
        else:
            self.__click_waiting = True
            self.__tm_click.init(period=self.__DBL, mode=machine.Timer.ONE_SHOT, callback=self.__cb_single_click)


def i2cdetect(bus:int, show:bool=False) -> list | None:
    """
    Detect I2C devices on the specified bus.
    
    :param bus: The I2C bus number. 0 or 1.
    :param show: If True, it prints the entire status, if False, it returns only the recognized device addresses in a list.
    :return: A list of detected I2C devices.
    """
    i2c = machine.I2C(bus)
    devices = i2c.scan()

    if not show:
        return devices
    else:
        print("     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f")
        for i in range(0, 8):
            print("{:02x}:".format(i*16), end='')
            for j in range(0, 16):
                address = i * 16 + j
                if address in devices:
                    print(ANSIEC.FG.BRIGHT_YELLOW + " {:02x}".format(address) + ANSIEC.OP.RESET, end='')
                else:
                    print(" --", end='')
            print()


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
        I2C_PIN_MAP = {
            0: {'sda': {0,4,8,12,16,20}, 'scl': {1,5,9,13,17,21}},
            1: {'sda': {2,6,10,14,18,26}, 'scl': {3,7,11,15,19,27}},
        }
        bus = None
        for bus_id, pins in I2C_PIN_MAP.items():
            if sda in pins['sda'] and scl in pins['scl']:
                bus = bus_id
                break
        if bus is None:
            raise ValueError(f"Invalid I2C pins: SDA={sda}, SCL={scl}")

        self.__addr = addr
        self.__i2c = machine.I2C(bus, scl=machine.Pin(scl), sda=machine.Pin(sda), freq=freq)

    def read_u8(self, reg:int) -> int:
        """
        Read an unsigned 8-bit value from the specified register.

        :param reg: The register address to read from.
        :return: The value read from the register.
        """
        data = self.__i2c.readfrom_mem(self.__addr, reg, 1)
        return data[0]

    def read_u16(self, reg:int, *, little_endian:bool=True) -> int:
        """
        Read an unsigned 16-bit value from the specified register.

        :param reg: The register address to read from.
        :param little_endian: If True, read the value in little-endian format, otherwise in big-endian format.
        :return: The value read from the register.
        """
        data = self.__i2c.readfrom_mem(self.__addr, reg, 2)
        order = 'little' if little_endian else 'big'
        return int.from_bytes(data, order)

    def write_u8(self, reg:int, val:int) -> None:
        """
        Write an unsigned 8-bit value to the specified register.

        :param reg: The register address to write to.
        :param val: The value to write to the register (0-255).
        """
        self.__i2c.writeto_mem(self.__addr, reg, bytes([val & 0xFF]))

    def write_u16(self, reg:int, val:int, *, little_endian:bool=True) -> None:
        """
        Write an unsigned 16-bit value to the specified register.

        :param reg: The register address to write to.
        :param val: The value to write to the register (0-65535).
        :param little_endian: If True, write the value in little-endian format, otherwise in big-endian format.
        """
        order = 'little' if little_endian else 'big'
        self.__i2c.writeto_mem(self.__addr, reg, val.to_bytes(2, order))

    def readfrom(self, nbytes:int, *, stop:bool=True) -> bytes:
        """
        Read a specified number of bytes from the I2C device.

        :param nbytes: The number of bytes to read.
        :param stop: If True, send a stop condition after reading.
        :return: The bytes read from the I2C device.
        """
        return self.__i2c.readfrom(self.__addr, nbytes, stop)

    def readinto(self, buf:bytearray, *, stop:bool=True) -> int:
        """
        Read bytes into a buffer from the I2C device.

        :param buf: The buffer to read the bytes into.
        :param stop: If True, send a stop condition after reading.
        :return: The number of bytes read into the buffer.
        """
        return self.__i2c.readinto(self.__addr, buf, stop)

    def readfrom_mem(self, reg:int, nbytes:int, *, addrsize:int=8) -> bytes:
        """
        Read a specified number of bytes from a specific register in the I2C device.

        :param reg: The register address to read from.
        :param nbytes: The number of bytes to read.
        :param addrsize: The address size in bits (default is 8 bits).
        :return: The bytes read from the specified register.
        """
        return self.__i2c.readfrom_mem(self.__addr, reg, nbytes, addrsize=addrsize)

    def readfrom_mem_into(self, reg:int, buf:bytearray, *, addrsize:int=8) -> int:
        """
        Read bytes from a specific register in the I2C device into a buffer.

        :param reg: The register address to read from.
        :param buf: The buffer to read the bytes into.
        :param addrsize: The address size in bits (default is 8 bits).
        :return: The number of bytes read into the buffer.
        """
        return self.__i2c.readfrom_mem_into(self.__addr, reg, buf, addrsize=addrsize)

    def writeto(self, buf:bytes, *, stop:bool=True) -> int:
        """
        Write bytes to the I2C device.

        :param buf: The bytes to write to the I2C device.
        :param stop: If True, send a stop condition after writing.
        :return: The number of bytes written to the I2C device.
        """
        return self.__i2c.writeto(self.__addr, buf, stop)

    def writeto_mem(self, reg:int, buf:bytes, *, addrsize:int=8) -> int:
        """
        Write bytes to a specific register in the I2C device.

        :param reg: The register address to write to.
        :param buf: The bytes to write to the specified register.
        :param addrsize: The address size in bits (default is 8 bits).
        :return: The number of bytes written to the specified register.
        """
        return self.__i2c.writeto_mem(self.__addr, reg, buf, addrsize=addrsize)


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
        self._timeout   = timeout
        self._stdin     = usys.stdin.buffer
        self._stdout    = usys.stdout
        self._buf       = utools.RingBuffer(bufsize)
        self._scheduled = False
        self._tmr = machine.Timer(-1)
        self._tmr.init(period=poll_ms, mode=machine.Timer.PERIODIC, callback=self.__tick)

    def __tick(self, t):
        """
        Periodic callback to read data from the REPL stdin.
        This method is called periodically to read data from the REPL stdin and store it in the ring buffer.
        It checks if the buffer is empty and schedules the `__pump` method to read data.
        If the buffer is not empty, it does nothing.

        :param t: Timer object (not used).
        """
        if not self._scheduled:
            self._scheduled = True
            try:
                micropython.schedule(self.__pump, None)
            except RuntimeError:
                self._scheduled = False

    def __pump(self, _):
        """
        Read data from the REPL stdin and put it into the ring buffer.
        This method is called periodically to read data from the REPL stdin and store it in the ring buffer.
        It reads one byte at a time as long as data is available in the stdin buffer.
        If an exception occurs during reading, it is caught and the scheduled flag is reset.
        """
        try:
            # read 1 byte at a time as long as data is ready
            while uselect.select([self._stdin], [], [], 0)[0]:
                b = self._stdin.read(1)
                if not b:
                    break
                self._buf.put(b)
        except Exception:
            pass
        finally:
            self._scheduled = False

    def __wait(self, deadline_ms:int):
        """
        Wait until the REPL buffer has data or the deadline is reached.
        This method blocks until data is available in the buffer or the deadline is reached.
        If `deadline_ms` is None, it will block indefinitely until data is available.
        If `deadline_ms` is specified, it will wait until the specified time in milliseconds.
        If the timeout is set to 0, it will return immediately if data is available, otherwise it will block until data is available.
        
        :param deadline_ms: The deadline in milliseconds to wait for data. If None, it will block indefinitely.
        """
        while not self._buf.avail():
            if deadline_ms is not None and utime.ticks_diff(deadline_ms, utime.ticks_ms()) <= 0:
                return
            dur = None if deadline_ms is None else max(0,
                utime.ticks_diff(deadline_ms, utime.ticks_ms())) / 1000
            uselect.select([self._stdin], [], [], dur)

    @property
    def timeout(self):
        """
        Get the timeout for read operations.
        - timeout=None : blocking read
        - timeout=0    : non-blocking read
        - timeout>0    : wait up to timeout seconds
        """
        return self._timeout
    
    @timeout.setter
    def timeout(self, value:float|None):
        """
        Set the timeout for read operations.
        - timeout=None : blocking read
        - timeout=0    : non-blocking read
        - timeout>0    : wait up to timeout seconds
        :param value: The timeout value in seconds. If None, it will block indefinitely.
        """
        self._timeout = value

    def read(self, size:int=1) -> bytes:
        """
        Read `size` bytes from the REPL buffer.
        If `size` is less than or equal to 0, it returns an empty byte string.
        If `size` is greater than the available data, it waits for data to become available based on the timeout.
        
        :param size: The number of bytes to read (default is 1).
        :return: The read bytes as a byte string.
        """   
        if size <= 0:
            return b''
        dl = None if self._timeout is None else utime.ticks_add(utime.ticks_ms(), int(self._timeout*1000))
        self.__wait(dl)
        return self._buf.get(size)

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
        # Non-blocking shortcut
        if self._timeout == 0:
            if max_size and self._buf.avail() >= max_size:
                return self._buf.get(max_size)
            data = self._buf.get_until(expected, max_size)
            return data or b''

        # Prepare deadline for waiting modes
        deadline = None
        if self._timeout is not None:
            deadline = utime.ticks_add(utime.ticks_ms(), int(self._timeout * 1000))

        # Main loop for blocking/timeout
        while True:
            # max_size first
            if max_size and self._buf.avail() >= max_size:
                return self._buf.get(max_size)

            # pattern next
            data = self._buf.get_until(expected, max_size)
            if data is not None:
                return data

            # timeout check
            if deadline is not None:
                if utime.ticks_diff(deadline, utime.ticks_ms()) <= 0:
                    return b''

            # wait for incoming data
            self.__wait(deadline)

    def write(self, data:bytes) -> int:
        """
        Write `data` to the REPL UART.
        If `data` is not bytes or bytearray, it raises a TypeError.
        
        :param data: The data to write (must be bytes or bytearray).
        :return: The number of bytes written.
        """
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("data must be bytes or bytearray")
        return self._stdout.write(data)

    def close(self):
        """
        Close the REPL serial connection and deinitialize the timer.
        This method stops the periodic timer and releases resources.
        """
        self._tmr.deinit()


def input(prompt:str="") -> str:
    """
    Blocking input() replacement with:
      - UTF-8 decoding (1-4 bytes per char)
      - <-, -> arrow cursor movement
      - Backspace deletes before cursor
      - Deletes at cursor
      - Proper insertion anywhere in the line
    
    :param prompt: The prompt to display before reading input.
    :return: The input string entered by the user.
    """
    __char_width = lambda ch: 1 if len(ch.encode('utf-8')) == 1 else 2

    repl_in = usys.stdin.buffer
    repl_out = usys.stdout
    
    BACKSPACE = (0x08, 0x7F)
    ENTER = (0x0D, 0x0A)
        
    if prompt:
        repl_out.write(prompt.encode('utf-8'))

    buf = []
    pos = 0
    push = None
    
    while True:
        if push is not None:
            b = push
            push = None
        else:
            while not uselect.select([repl_in], [], [], 0)[0]:
                pass
            b = repl_in.read(1)
            if not b:
                continue
        byte = b[0]

        if byte in ENTER:
            repl_out.write(b"\n")
            while uselect.select([repl_in], [], [], 0)[0]:
                nxt = repl_in.read(1)
                if not nxt:
                    continue
                if nxt[0] in ENTER:
                    continue
                push = nxt
                break
            break

        if byte == 0x1B:
            seq = repl_in.read(2)
            # left key
            if seq == b'[D' and pos > 0:
                w = __char_width(buf[pos-1])
                repl_out.write(f"\x1b[{w}D".encode())
                pos -= 1
            # right key
            elif seq == b'[C' and pos < len(buf):
                w = __char_width(buf[pos])
                repl_out.write(f"\x1b[{w}C".encode())
                pos += 1
            # Delete (ESC [ 3 ~)
            elif seq == b'[3' and repl_in.read(1) == b'~' and pos < len(buf):
                buf.pop(pos)
                repl_out.write(b"\x1b[K")
                tail = ''.join(buf[pos:])
                if tail:
                    repl_out.write(tail.encode('utf-8'))
                    ws = sum(__char_width(c) for c in tail)
                    repl_out.write(f"\x1b[{ws}D".encode())
            continue

        # Backspace
        if byte in BACKSPACE and pos > 0:
            pos -= 1
            removed = buf.pop(pos)
            w = __char_width(removed)
            repl_out.write(f"\x1b[{w}D".encode())
            repl_out.write(b"\x1b[K")
            tail = ''.join(buf[pos:])
            if tail:
                repl_out.write(tail.encode('utf-8'))
                ws = sum(__char_width(c) for c in tail)
                repl_out.write(f"\x1b[{ws}D".encode())
            continue

        first = byte
        if first < 0x80:
            seq = b
        elif (first & 0xE0) == 0xC0:
            seq = b + repl_in.read(1)
        elif (first & 0xF0) == 0xE0:
            seq = b + repl_in.read(2)
        elif (first & 0xF8) == 0xF0:
            seq = b + repl_in.read(3)
        else:
            continue

        try:
            ch = seq.decode('utf-8')
        except UnicodeError:
            continue

        buf.insert(pos, ch)
        w = __char_width(ch)
        tail = ''.join(buf[pos+1:])

        repl_out.write(seq)
        if tail:
            repl_out.write(tail.encode('utf-8'))
            ws = sum(__char_width(c) for c in tail)
            repl_out.write(f"\x1b[{ws}D".encode())
        pos += 1

    return ''.join(buf)
