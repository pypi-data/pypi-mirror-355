import math
import utime
import machine
import ustruct
import rp2
import array
import math

import utools
from . import Dout, Din, Pwm, I2c

class Relay:
    ON = Dout.HIGH
    OFF = Dout.LOW

    class _Channel:
        """
        A class representing a single relay channel.
        This class provides properties to get and set the state of the relay,
        turn the relay on or off, and set the delay in milliseconds.
        """
        def __init__(self, parent, idx):
            """
            Initialize the relay channel with a reference to the parent Relay instance and its index.
            
            :param parent: Reference to the parent Relay instance
            :param idx: Index of the relay channel (0-based)
            """
            self.__parent = parent
            self.__idx = idx

        @property
        def state(self) -> int:
            """
            Get the current state of the relay channel.
            This property returns the state of the relay channel, which can be either Relay.ON or Relay.OFF.
            
            :return: Current state of the relay channel (Dout.HIGH or Dout.LOW)
            """
            return self.__parent.__states[self.__idx]

        @state.setter
        def state(self, val: int) -> None:
            """
            Set the state of the relay channel.
            This property sets the state of the relay channel to either Relay.ON or Relay.OFF.
            
            :param val: State to set (Dout.HIGH or Dout.LOW)
            """
            if val not in (Dout.LOW, Dout.HIGH):
                raise ValueError("state must be Dout.LOW or Dout.HIGH")
            self.__parent.__dout[self.__idx] = val
            self.__parent.__states[self.__idx] = val
            utime.sleep_ms(self.__parent.__min_delay_ms)

        def on(self) -> None:
            """
            Turn the relay channel on.
            This method sets the state of the relay channel to Relay.ON.
            """
            self.state = Relay.ON

        def off(self) -> None:
            """
            Turn the relay channel off.
            This method sets the state of the relay channel to Relay.OFF.
            """
            self.state = Relay.OFF

        @property
        def delay_ms(self) -> int:
            """
            Get the minimum delay in milliseconds for the relay channel.
            This property returns the minimum delay in milliseconds that is applied after changing the state of the relay channel.
            
            :return: Minimum delay in milliseconds
            """
            return self.__parent.__min_delay_ms

        @delay_ms.setter
        def delay_ms(self, ms: int) -> None:
            """
            Set the minimum delay in milliseconds for the relay channel.
            This property sets the minimum delay in milliseconds that is applied after changing the state of the relay channel.
            
            :param ms: Minimum delay in milliseconds
            """
            self.__parent.__min_delay_ms = int(ms)

    class _Group:
        """
        A class representing a group of relay channels.
        This class allows setting attributes for all channels in the group at once.
        """
        def __init__(self, channels):
            """
            Initialize the group of relay channels.
            
            :param channels: List of Relay._Channel objects
            """
            self.__channels = channels

        def __setattr__(self, name, value):
            """
            Set an attribute for all channels in the group.
            If the attribute name starts with an underscore, it is set on the group itself.
            
            :param name: Attribute name
            :param value: Value to set for the attribute
            """
            if name.startswith('_'):
                super().__setattr__(name, value)
            else:
                for ch in self.__channels:
                    setattr(ch, name, value)

        def __getattr__(self, name):
            """
            Get an attribute from the first channel in the group.
            """
            return getattr(self.__channels[0], name)

    def __init__(self, pins:tuple[int, ...], min_delay_ms:int=5):
        """
        Initialize the Relay with specified GPIO pins and minimum delay.
        
        :param pins: Tuple of GPIO pin numbers for the relay channels (e.g., (2, 3, 4))
        :param min_delay_ms: Minimum delay in milliseconds after changing the state of a relay channel (default 5 ms)
        """
        self.__min_delay_ms = int(min_delay_ms)
        self.__dout = Dout(pins)
        self.__states = [Relay.OFF] * len(pins)
        for i in range(len(pins)):
            self.__dout[i] = Relay.OFF
        self.__channels = [Relay.__Channel(self, i) for i in range(len(pins))]
        self.all = Relay._Group(self.__channels)

    def __getitem__(self, idx:int) -> _Channel:
        """
        Get the relay channel at the specified index.
        
        :param idx: Index of the relay channel (0-based)
        :return: Relay._Channel object for the specified index
        """
        return self.__channels[idx]

    def __len__(self) -> int:
        """
        Get the number of relay channels.
        
        :return: Number of relay channels
        """
        return len(self.__channels)

    
class ServoMotor:
    """
    A class to control multiple servo motors using PWM.
    This class allows setting angles, speeds, and non-blocking behavior for each servo channel.
    It supports a range of servo motors and provides methods to control them individually or as a group.
    """
    class _Channel:
        """
        A class representing a single servo channel.
        This class provides properties to get and set the angle, speed, and non-blocking behavior of the servo.
        """
        def __init__(self, pin: int, *, freq: int, min_us: int, max_us: int, init_deg: float):
            """
            Initialize the servo channel with the specified parameters.
            
            :param pin: GPIO pin number for the servo motor
            :param freq: PWM frequency in Hz
            :param min_us: Minimum pulse width in microseconds
            :param max_us: Maximum pulse width in microseconds
            :param init_deg: Initial angle in degrees
            """
            self.__pin = pin
            self.__pwm = Pwm((pin,))
            self.__min_us = min_us
            self.__max_us = max_us
            self.__current_angle = init_deg

        @property
        def angle(self) -> float:
            """
            Get the current angle of the servo channel.
            This property returns the current angle in degrees (0 to 180).
            
            :return: Current angle in degrees
            """
            return self.__parent._current_angles[self.__idx]

        @angle.setter
        def angle(self, deg: float) -> None:
            """
            Set the target angle for the servo channel.
            This property clamps the angle to the range [0, 180] degrees and updates the target angle.
            
            :param deg: Target angle in degrees (0 to 180)
            """
            self.__parent.__set_target(self.__idx, deg)

        @property
        def speed_ms(self) -> int:
            """
            Get the speed in milliseconds for the servo channel.
            This property returns the speed in milliseconds for moving to the target angle.
            
            :return: Speed in milliseconds
            """
            return self.__parent._speed_ms[self.__idx]

        @speed_ms.setter
        def speed_ms(self, ms: int) -> None:
            """
            Set the speed in milliseconds for the servo channel.
            This property sets the speed for moving to the target angle.
            """
            self.__parent._speed_ms[self.__idx] = int(ms)

        @property
        def nonblocking(self) -> bool:
            """
            Get the non-blocking flag for the servo channel.
            This property indicates whether the servo channel operates in non-blocking mode.
            
            :return: True if non-blocking mode is enabled, False otherwise
            """
            return self.__parent._nonblocking[self.__idx]

        @nonblocking.setter
        def nonblocking(self, flag: bool) -> None:
            """
            Set the non-blocking flag for the servo channel.
            This property enables or disables non-blocking mode for the servo channel.
            
            :param flag: True to enable non-blocking mode, False to disable
            """
            self.__parent._nonblocking[self.__idx] = bool(flag)

    class _Group:
        def __init__(self, channels):
            """
            Initialize the group of servo channels.
            
            :param channels: List of ServoMotor._Channel objects
            """
            self._channels = channels

        def __setattr__(self, name, value):
            """
            Set an attribute for all channels in the group.
            If the attribute name starts with an underscore, it is set on the group itself.
            
            :param name: Attribute name
            :param value: Value to set for the attribute
            """
            if name.startswith('_'):
                super().__setattr__(name, value)
                return
            for ch in self._channels:
                setattr(ch, name, value)

        def __getattr__(self, name):
            """
            Get an attribute from the first channel in the group.
            If the attribute does not exist, it raises an AttributeError.
            
            :param name: Attribute name
            :return: Value of the attribute from the first channel
            """
            return getattr(self._channels[0], name)

    def __init__(self, pins:tuple[int, ...], freq:int=50, default_min_us:int=500, default_max_us: int=2500, initial_angle: float=0.0):
        """
        Initialize the ServoMotor with specified GPIO pins and parameters.
        
        :param pins: Tuple of GPIO pin numbers for the servo motors (e.g., (2, 3, 4))
        :param freq: PWM frequency in Hz (default 50 Hz)
        :param default_min_us: Default minimum pulse width in microseconds (default 500 us)
        :param default_max_us: Default maximum pulse width in microseconds (default 2500 us)
        :param initial_angle: Initial angle for all servos in degrees (default 0.0)
        """
        self._pwm = Pwm(pins)
        self._pwm.all.freq = freq
        n = len(pins)
        self._min_us = [default_min_us] * n
        self._max_us = [default_max_us] * n
        init_deg = utools.clamp(initial_angle, 0.0, 180.0)
        self._current_angles = [init_deg] * n
        self._target_angles = [init_deg] * n
        self._speed_ms = [0] * n
        self._nonblocking = [False] * n
        self._timer = machine.Timer()
        self._timer_active = False
        self._channels = [ServoMotor._Channel(self, i) for i in range(n)]
        self.all = ServoMotor._Group(self._channels)
        for ch in self._channels:
            ch.angle = init_deg

    def __compute_us(self, deg: float, idx: int) -> float:
        """
        Compute the pulse width in microseconds for a given angle and servo channel index.
        This method maps the angle (0 to 180 degrees) to the corresponding pulse width
        based on the minimum and maximum pulse widths defined for that channel.
        
        :param deg: Angle in degrees (0 to 180)
        :param idx: Index of the servo channel (0-based)
        :return: Pulse width in microseconds
        """
        span = self._max_us[idx] - self._min_us[idx]
        return self._min_us[idx] + span * deg / 180.0

    def __set_target(self, idx: int, deg: float) -> None:
        """
        Set the target angle for a specific servo channel.
        This method clamps the angle to the range [0, 180] degrees and updates the target angle.
        
        :param idx: Index of the servo channel (0-based)
        :param deg: Target angle in degrees (0 to 180)
        """
        deg = utools.clamp(deg, 0.0, 180.0)
        self._target_angles[idx] = deg
        speed = self._speed_ms[idx]
        nonblk = self._nonblocking[idx]
        if not nonblk or speed <= 0:
            us = self.__compute_us(deg, idx)
            self._pwm[idx].duty_us = int(us)
            self._current_angles[idx] = deg
        else:
            if not self._timer_active:
                self._timer.init(
                    period=speed,
                    mode=machine.Timer.PERIODIC,
                    callback=self.__timer_cb
                )
                self._timer_active = True

    def __timer_cb(self, t) -> None:
        """
        Timer callback function to update servo angles periodically.
        This function is called periodically to move the servos towards their target angles.
        
        :param t: Timer object (not used in this context)
        """
        done = True
        for idx, tgt in enumerate(self._target_angles):
            if self._nonblocking[idx] and self._speed_ms[idx] > 0:
                cur = self._current_angles[idx]
                if cur != tgt:
                    done = False
                    sign = 1 if tgt > cur else -1
                    new = cur + sign
                    self._current_angles[idx] = new
                    us = self.__compute_us(new, idx)
                    self._pwm[idx].duty_us = int(us)
        if done:
            self._timer.deinit()
            self._timer_active = False

    def __getitem__(self, idx: int) -> _Channel:
        """
        Get the servo channel at the specified index.
        
        :param idx: Index of the servo channel (0-based)
        :return: ServoMotor._Channel object for the specified index
        """
        return self._channels[idx]

    def deinit(self) -> None:
        """
        Deinitialize the ServoMotor instance.
        This method stops the timer and disables all PWM channels.
        """
        if self._timer_active:
            self._timer.deinit()
        self._pwm.all.enable = False


class PiezoBuzzer:
    """
    A class to control a piezo buzzer using PWM.
    It can play tones, melodies, and supports effects like staccato, vibrato, and tremolo.
    """
    __NOTE_FREQ = {
        'C':0,'CS':1,'D':2,'DS':3,'E':4,'F':5,
        'FS':6,'G':7,'GS':8,'A':9,'AS':10,'B':11
    }
    __BASE_FREQ = 16.35

    def __init__(self, pin:int, tempo:int=120):
        """
        Initialize the PiezoBuzzer with the specified pin and tempo.
        
        :param pin: GPIO pin number for the buzzer (default 1).
        :param tempo: Tempo in beats per minute (default 120).
        """
        self.__pwm = Pwm((pin,))
        self.__chan = self.__pwm[0]
        self.__chan.duty = 0
        self.__tempo = tempo
        self.__is_playing = False
        self.__timer = machine.Timer()
        self.__seq = []
        self.__idx = -2
        self.__state = 'off'
        self.__ms_remain = 0
        self.__on_ms = 0
        self.__off_ms = 0
        self.__tick = 10
        self.__effect = None

    def __note_to_freq(self, note_oct:str) -> int:
        """
        Convert a musical note with octave to frequency in Hz.
        
        :param note_oct: Musical note with octave (e.g., 'C4', 'A#5').
        :return: Frequency in Hz.
        """
        note = note_oct[:-1].upper()
        octave = int(note_oct[-1])
        n = octave*12 + self.__class__.__NOTE_FREQ[note]
        return int(self.__class__.__BASE_FREQ * (2 ** (n/12)))

    def __timer_cb(self, t):
        """
        Timer callback function to handle the buzzer state changes.
        This function is called periodically to update the buzzer state.
        
        :param t: Timer object (not used in this context).
        """
        if not self.__is_playing:
            return
        self.__ms_remain -= self.__tick
        if self.__ms_remain > 0:
            return
        if self.__state == 'on':
            self.__chan.duty = 0
            self.__state = 'off'
            self.__ms_remain = self.__off_ms
        else:
            self.__idx += 2
            if self.__idx >= len(self.__seq):
                self.stop()
                return
            note = self.__seq[self.__idx]
            length = self.__seq[self.__idx+1]
            dur = (60/self.__tempo)*(4/length)
            self.__on_ms = int(dur*900)
            self.__off_ms = int(dur*100)
            self.__state = 'on'
            if note.upper() in ('R','REST'):
                self.__chan.duty = 0
            else:
                freq = self.__note_to_freq(note)
                self.__chan.freq = freq
                if self.__effect == 'staccato':
                    self.__on_ms = int(self.__on_ms * 0.5)
                self.__chan.duty = 50
            self.__ms_remain = self.__on_ms

    def tone(self, note_oct:str, length:int=4, effect:str=None):
        """
        Play a single tone with the specified note, length, and effect.
       
        :param note_oct: Musical note with octave (e.g., 'C4', 'A#5').
        :param length: Length of the note in beats (default 4).
        :param effect: Effect to apply to the note (e.g., 'staccato', 'vibrato', 'tremolo', 'gliss:C#5').
        """
        dur = (60/self.__tempo)*(4/length)
        if note_oct.upper() in ('R','REST'):
            self.__chan.duty = 0
            utime.sleep(dur)
            return
        base_freq = self.__note_to_freq(note_oct)
        if effect == 'vibrato':
            end = utime.ticks_ms() + int(dur*1000)
            while utime.ticks_ms() < end:
                t = (utime.ticks_ms()%100)/100
                mod = math.sin(2*math.pi*t)*5
                self.__chan.freq = int(base_freq+mod)
                self.__chan.duty = 50
            self.__chan.duty = 0
        elif effect == 'tremolo':
            end = utime.ticks_ms() + int(dur*1000)
            while utime.ticks_ms() < end:
                t = (utime.ticks_ms()%200)/200
                duty = int((math.sin(2*math.pi*t)+1)/2*100)
                self.__chan.freq = base_freq
                self.__chan.duty = duty
            self.__chan.duty = 0
        elif effect and effect.startswith('gliss'):
            parts = effect.split(':')
            if len(parts)==2:
                target = self.__note_to_freq(parts[1])
                steps = 20
                for i in range(steps):
                    f = base_freq + (target-base_freq)*i/(steps-1)
                    self.__chan.freq = int(f)
                    self.__chan.duty = 50
                    utime.sleep(dur/steps)
                self.__chan.duty = 0
        else:
            self.__chan.freq = base_freq
            if effect=='staccato':
                self.__chan.duty = 50
                utime.sleep(dur*0.5)
                self.__chan.duty = 0
                utime.sleep(dur*0.5)
            else:
                self.__chan.duty = 50
                utime.sleep(dur)
                self.__chan.duty = 0

    def play(self, melody, effect:str=None, background:bool=False):
        """
        Play a melody consisting of notes and lengths.
        
        :param melody: List of notes and lengths (e.g., ['C4', 4, 'D4', 2, 'E4', 1]).
        :param effect: Effect to apply to the melody (e.g., 'staccato', 'vibrato', 'tremolo').
        :param background: If True, play the melody in the background (default False).
        """
        if self.__is_playing:
            return
        if not background:
            for i in range(0,len(melody),2):
                note, length = melody[i], melody[i+1]
                self.tone(note, length, effect)
        else:
            self.__seq = melody[:]
            self.__idx = -2
            self.__effect = effect if effect=='staccato' else None
            self.__is_playing = True
            self.__timer.init(mode=machine.Timer.PERIODIC, period=self.__tick, callback=self.__timer_cb)

    def stop(self):
        """
        Stop playing the current melody and reset the buzzer state.
        """
        self.__is_playing = False
        try:
            self.__timer.deinit()
        except:
            pass
        self.__chan.duty = 0

    def set_tempo(self, bpm:int):
        """
        Set the tempo for the buzzer in beats per minute.
        
        :param bpm: Tempo in beats per minute
        """
        self.__tempo = bpm


class SR04:
    """
    This class drives an HC-SR04 ultrasonic sensor by emitting a 40 kHz pulse 
    and measuring its time-of-flight (using the speed of sound ≈343 m/s at 20 °C) 
    to compute distances from 2 cm to 400 cm, then applies a Kalman filter 
    to smooth out measurement noise.
    """    
    
    def __init__(self, trig:int, echo:int, *, temp_c:float=20.0, R:int=25, Q:int=4):
        """
        Initialize the ultrasonic sensor with the specified trigger and echo pins.
        
        :param trig: GPIO pin number for the trigger pin.
        :param echo: GPIO pin number for the echo pin.
        :param temp_c: Temperature in degrees Celsius (default is 20.0).
        :param R: Measurement noise covariance (default is 25).
        :param Q: Process noise covariance (default is 4).
        """
        self.__trig = Dout((trig,)) #machine.Pin(trig, machine.Pin.OUT, value=0)
        self.__echo = Din((echo,))  #machine.Pin(echo, machine.Pin.IN)
        
        self.__x  = 0.0
        self.__v  = 0.0
        self.__P  = [[1.0, 0.0],[0.0, 1.0]]
        self.__R  = R
        self.__Q  = Q
        
        self.__temp_c = temp_c

    def __cm_per_us(self, temp:float) -> float:
        """
        Calculate the speed of sound in cm/us based on the temperature.
        The speed of sound in air increases by approximately 0.606 m/s for each degree Celsius increase in temperature.
        
        :param temp: Temperature in degrees Celsius.
        :return: Speed of sound in cm/us.
        """
        speed = 331.3 + 0.606 * temp       # m/s
        return (speed * 100.0) / 1_000_000 / 2.0
        
    def __trigger(self):
        """
        Send a 10 microsecond pulse to the trigger pin to initiate the ultrasonic measurement.
        The trigger pin is set high for 10 microseconds and then set low.
        """
        self.__trig.on()
        utime.sleep_us(10)
        self.__trig.off()

    def __kalman1d(self, z:float, dt:float=0.06) -> float:
        """
        Kalman filter for 1D data.
        
        :param z: Measurement value.
        :param dt: Time interval (default is 0.06 seconds).
        :return: Filtered value.
        """        
        # predict
        self.__x += self.__v * dt
        self.__P[0][0] += dt * (2 * self.__P[1][0] + dt * self.__P[1][1]) + self.__Q
        self.__P[0][1] += dt * self.__P[1][1]
        self.__P[1][0] += dt * self.__P[1][1]

        # update
        y = z - self.__x
        S = self.__P[0][0] + self.__R
        K0 = self.__P[0][0] / S
        K1 = self.__P[1][0] / S

        self.__x += K0 * y
        self.__v += K1 * y

        self.__P[0][0] -= K0 * self.__P[0][0]
        self.__P[0][1] -= K0 * self.__P[0][1]
        self.__P[1][0] -= K1 * self.__P[0][0]
        self.__P[1][1] -= K1 * self.__P[0][1]

        return self.__x
    
    def read(self, timeout_us:int=30_000, temp_c:float|None=None) -> float|None:
        """
        Read the distance from the ultrasonic sensor.
        
        :param timeout_us: Timeout in microseconds for the echo signal.
        :return: Distance in centimeters or None if timeout occurs.
        """
        t = self.__temp_c if temp_c is None else temp_c
        
        # trigger pulse
        self.__trig.off()  # Ensure trigger is low before sending pulse
        self.__trigger()
        
        dur = machine.time_pulse_us(self.__echo, 1, timeout_us)
        if dur < 0:
            return None               # timeout / invalid
        
        factor = self.__cm_per_us(t)
        measurement = dur * factor
        filtered = self.__kalman1d(measurement)
        
        return filtered

@rp2.asm_pio(
    sideset_init=rp2.PIO.OUT_LOW,
    out_shiftdir=rp2.PIO.SHIFT_LEFT,
    autopull=True,
    pull_thresh=24
)
def __ws2812_pio():
    T1 = 2
    T2 = 5
    T3 = 3
    label("bitloop")
    out(x, 1)           .side(0) [T3 - 1]
    jmp(not_x, "do0")   .side(1) [T1 - 1]
    jmp("bitloop")      .side(1) [T2 - 1]
    label("do0")
    nop()               .side(0) [T2 - 1]

class WS2812Matrix:
    def __init__(self, pin_sm_pairs:list[tuple[int,int]], *, panel_w:int=16, panel_h:int=16, grid_w:int=1,  grid_h:int=1, zigzag:bool=True, origin:str='top_left', brightness:float=0.25):
        """
        WS2812 Matrix controller using PIO for multiple panels.
        
        :param pin_sm_pairs: list of (pin_number, state_machine_id) tuples
        :param panel_w: width of each panel in pixels
        :param panel_h: height of each panel in pixels
        :param grid_w: number of panels in the grid width
        :param grid_h: number of panels in the grid height
        :param zigzag: if True, odd rows are reversed (zigzag wiring)
        :param origin: one of 'top_left', 'top_right', 'bottom_left', 'bottom_right'
        :param brightness: brightness level from 0.0 to 1.0
        """
        if origin not in ('top_left','top_right','bottom_left','bottom_right'):
            raise ValueError("origin must be top_left/top_right/bottom_left/bottom_right")
        
        mapping = pin_sm_pairs
        
        self.__panel_w  = panel_w
        self.__panel_h  = panel_h
        self.__grid_w   = grid_w
  
        self.__display_w   = panel_w * grid_w
        self.__display_h   = panel_h * grid_h

        self.__zigzag   = zigzag
        self.__origin   = origin
        self.brightness  = brightness

        self.__sms = [] 
        self.__bufs = []
        self.__panels_per_sm = math.ceil((grid_w * grid_h) / len(mapping))
        self.__pixels_per_panel = panel_w * panel_h

        for pin_no, sm_id in mapping:
            pin = machine.Pin(pin_no, machine.Pin.OUT, machine.Pin.PULL_DOWN)
            sm  = rp2.StateMachine(sm_id, __ws2812_pio, freq=8_000_000, sideset_base=pin)
            sm.active(1)
            self.__sms.append(sm)
            buf_len = self.__pixels_per_panel * self.__panels_per_sm
            self.__bufs.append(array.array('I', [0]*buf_len))
        
    def __coord_to_index(self, x:int, y:int):
        """
        Convert pixel coordinates (x, y) to the corresponding state machine and buffer index.
        
        :param x: x-coordinate (horizontal position)
        :param y: y-coordinate (vertical position)
        :return: (state_machine_index, buffer_index)
        """
        if not (0 <= x < self.__display_w and 0 <= y < self.__display_h):
            raise IndexError("pixel out of range")

        # calculate panel ID and local coordinates within the panel
        panel_col = x // self.__panel_w
        panel_row = y // self.__panel_h
        panel_id  = panel_row * self.__grid_w + panel_col

        # panel internal local coordinates
        lx = x % self.__panel_w
        ly = y % self.__panel_h

        # convert to panel-local coordinates
        if self.__origin.startswith('bottom'):
            ly = self.__panel_h - 1 - ly
        if self.__origin.endswith('right'):
            lx = self.__panel_w - 1 - lx
        
        # zigzag adjustment
        if self.__zigzag and (ly % 2):  # odd rows are reversed if zigzag is enabled
            lx = self.__panel_w - 1 - lx

        # SM / buffer index
        sm_idx   = panel_id // self.__panels_per_sm
        local_id = panel_id %  self.__panels_per_sm
        buf_idx  = local_id * self.__pixels_per_panel + ly * self.__panel_w + lx
        return sm_idx, buf_idx

    def deinit(self):
        """
        Deinitialize the WS2812 matrix controller.
        This method clears the buffers, stops the state machines, and resets the pins.
        """
        self.clear()
        utime.sleep_us(150)
        
        for sm in self.__sms:
            sm.active(0)
        for sm in self.__sms:
            sm.exec("set(pindirs, 1)")
            sm.exec("set(pins, 0)")

    @property
    def display_w(self) -> int:
        """
        Get the width of the display in pixels.
        
        :return: Width of the display in pixels
        """
        return self.__display_w

    @property
    def display_h(self) -> int:
        """
        Get the height of the display in pixels.
        
        :return: Height of the display in pixels
        """
        return self.__display_h

    @property
    def brightness(self) -> float:
        """
        Get the current brightness level of the matrix.
        The brightness level is a float value between 0.0 (off) and 1.0 (full brightness).
        
        :return: Brightness level (float)
        """
        return self.__bright

    @brightness.setter
    def brightness(self, value:float):
        """
        Set the brightness level of the matrix.
        The brightness level should be a float value between 0.0 (off) and 1.0 (full brightness).
        
        :param value: Brightness level (float)
        :raises ValueError: If the brightness value is not between 0.0 and 1.0.
        """
        self.__bright = max(0.0, min(value,1.0))
        b = self.__bright
        self.__btab = bytes(int(i * b + 0.5) for i in range(256))

    def __setitem__(self, pos:tuple[int,int], color:tuple[int,int,int]):
        """
        Set the color of a pixel at the specified position.
        The color should be a tuple of three integers representing the RGB values (0-255).
        
        :param pos: Tuple of (x, y) coordinates of the pixel
        :param color: Tuple of (R, G, B) color values
        :raises IndexError: If the pixel coordinates are out of range.
        """
        x,y = pos
        r,g,b = color
        sm_idx, buf_idx = self.__coord_to_index(x,y)
        self.__bufs[sm_idx][buf_idx] = (g & 0xFF)<<16 | (r & 0xFF)<<8 | (b & 0xFF)

    def __getitem__(self, pos) -> tuple[int,int,int]:
        """
        Get the color of a pixel at the specified position.
        The color is returned as a tuple of three integers representing the RGB values (0-255).
        
        :param pos: Tuple of (x, y) coordinates of the pixel
        :return: Tuple of (R, G, B) color values
        :raises IndexError: If the pixel coordinates are out of range.
        """
        x,y = pos
        sm_idx, buf_idx = self.__coord_to_index(x,y)
        v = self.__bufs[sm_idx][buf_idx]
        return ((v>>8)&0xFF, (v>>16)&0xFF, v&0xFF)

    def fill(self, color:tuple[int,int,int]):
        """
        Fill the entire display with the specified color.
        The color should be a tuple of three integers representing the RGB values (0-255).
        
        :param color: Tuple of (R, G, B) color values
        :raises ValueError: If the color values are not in the range 0-255.
        """
        grb = ((color[1]&0xFF)<<16) | ((color[0]&0xFF)<<8) | (color[2]&0xFF)
        for buf in self.__bufs:
            for i in range(len(buf)):
                buf[i] = grb

    def clear(self):
        """
        Clear the display by filling it with black (0, 0, 0).
        This method sets all pixels to black and updates the display.
        """
        self.fill((0,0,0))
        self.update()
        
    def update(self):
        """
        Update the display by sending the pixel data to the state machines.
        This method processes the pixel data in the buffers and sends it to the WS2812 panels.
        """
        btab = self.__btab
        for sm, src in zip(self.__sms, self.__bufs):
            tmp = array.array('I', [0]*len(src))
            for i, v in enumerate(src):
                g = btab[v>>16 & 0xFF]
                r = btab[v>>8  & 0xFF]
                b = btab[v     & 0xFF]
                tmp[i] = g<<16 | r<<8 | b
            sm.put(tmp, 8)

    def draw_line(self, x0:int, y0:int, x1:int, y1:int, color:tuple[int,int,int]):
        """
        Draw a line on the display from (x0, y0) to (x1, y1) with the specified color.
        
        :param x0: Starting x-coordinate of the line
        :param y0: Starting y-coordinate of the line
        :param x1: Ending x-coordinate of the line
        :param y1: Ending y-coordinate of the line
        :param color: Tuple of (R, G, B) color values
        """
        dx = abs(x1-x0); sx = 1 if x0<x1 else -1
        dy = -abs(y1-y0); sy = 1 if y0<y1 else -1
        err = dx + dy
        while True:
            self[x0,y0] = color
            if x0==x1 and y0==y1: break
            e2 = err<<1
            if e2 >= dy: err += dy; x0 += sx
            if e2 <= dx: err += dx; y0 += sy

    def draw_rect(self, x:int, y:int, w:int, h:int, color:tuple[int,int,int]):
        """
        Draw a rectangle on the display with the specified position, width, height, and color.
        
        :param x: x-coordinate of the top-left corner of the rectangle
        :param y: y-coordinate of the top-left corner of the rectangle
        :param w: Width of the rectangle
        :param h: Height of the rectangle
        :param color: Tuple of (R, G, B) color values
        """
        self.draw_line(x,   y,   x+w-1, y,     color)
        self.draw_line(x,   y,   x,     y+h-1, color)
        self.draw_line(x+w-1, y, x+w-1, y+h-1, color)
        self.draw_line(x, y+h-1, x+w-1, y+h-1, color)

    def draw_circle(self, cx:int, cy:int, r:int, color:tuple[int,int,int]):
        """
        Draw a circle on the display with the specified center, radius, and color.
        
        :param cx: x-coordinate of the center of the circle
        :param cy: y-coordinate of the center of the circle
        :param r: Radius of the circle
        :param color: Tuple of (R, G, B) color values
        """
        x, y, err = r, 0, 0
        while x >= y:
            pts = [(cx+x,cy+y),(cx+y,cy+x),(cx-x,cy+y),(cx-y,cy+x),
                   (cx-x,cy-y),(cx-y,cy-x),(cx+x,cy-y),(cx+y,cy-x)]
            for px,py in pts:
                if 0<=px<self.__display_w and 0<=py<self.__display_h:
                    self[px,py] = color
            y += 1
            if err <= 0:
                err += (y<<1)+1
            if err > 0:
                x -= 1
                err -= (x<<1)+1

    def blit(self, data, dst_x:int, dst_y:int, size_x:int, size_y:int, fg:tuple[int, int, int]=(255,255,255), bg:tuple[int, int, int]|None=None):
        """
        Blit a bitmap image onto the display at the specified position.
        The bitmap data can be a 2D list or a flat array of bytes.
        Each pixel is represented by a single byte (0 for black, 1 for white).
        
        :param data: Bitmap data as a 2D list or flat array of bytes
        :param dst_x: x-coordinate of the top-left corner where the bitmap will be drawn
        :param dst_y: y-coordinate of the top-left corner where the bitmap will be drawn
        :param size_x: Width of the bitmap in pixels
        :param size_y: Height of the bitmap in pixels
        :param fg: Foreground color as a tuple of (R, G, B) values (default is white)
        :param bg: Background color as a tuple of (R, G, B) values (default is None, which means no background)
        :raises ValueError: If the data is not in the expected format.
        """
        get = None
        if isinstance(data,(bytes,bytearray,memoryview)):
            def get(ix,iy):
                return data[iy*size_x+ix]
        else:
            get = lambda ix,iy: data[iy][ix]

        for iy in range(size_y):
            py = dst_y+iy
            if py<0 or py>=self.__display_h: continue
            for ix in range(size_x):
                px = dst_x+ix
                if px<0 or px>=self.__display_w: continue
                bit = get(ix,iy)
                if bit:
                    self[px,py] = fg
                elif bg is not None:
                    self[px,py] = bg


class tLed:
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    YELLOW = (255, 255, 0)
    CYAN = (0, 255, 255)
    MAGENTA = (255, 0, 255)
    WHITE = (255, 255, 255)
    
    def __init__(self, brightness:float=1.0):
        """
        Basic WS2812 control class built into TiCLE.
        This class provides methods to turn on the LED with a specified color,
        turn it off, and define some common colors.
        
        :param brightness: Brightness level from 0.0 (off) to 1.0 (full brightness).
        """

        self.__led = WS2812Matrix([(9,11)], 1, 1, 1, 1, brightness=brightness)

    def on(self, color:tuple[int,int,int]=RED):
        """
        Turn on the LED with the specified color.

        :param color: Tuple of (R, G, B) color values (default is red).
        """
        self.__led.fill(color)
        self.__led.update()
    
    def off(self):
        """
        Turn off the LED by filling it with black (0, 0, 0).
        """
        self.__led.clear()
        
    @property
    def brightness(self) -> float:
        """
        Get the current brightness level of the matrix.
        The brightness level is a float value between 0.0 (off) and 1.0 (full brightness).
        
        :return: Brightness level (float)
        """
        return self.__led.brightness

    @brightness.setter
    def brightness(self, value:float):
        """
        Set the brightness level of the matrix.
        The brightness level should be a float value between 0.0 (off) and 1.0 (full brightness).
        
        :param value: Brightness level (float)
        :raises ValueError: If the brightness value is not between 0.0 and 1.0.
        """
        if not (0.0 <= value <= 1.0):
            raise ValueError("Brightness must be between 0.0 and 1.0.")
        self.__led.brightness = value


class VL53L0X:
    """
    A class to interface with the VL53L0X time-of-flight distance sensor.
    This class provides methods to read distances, configure the sensor, and manage continuous measurements.
    It uses I2C communication to interact with the sensor.
    The sensor can measure distances from 30 mm to 1200 mm with a resolution of 1 mm.
    It supports both single-shot and continuous measurement modes.
    """
    __SYSRANGE_START = 0x00
    __SYS_SEQUENCE_CONFIG = 0x01
    __SYS_INTERRUPT_CONFIG_GPIO = 0x0A
    __GPIO_HV_MUX_HIGH = 0x84
    __SYS_INTERRUPT_CLEAR = 0x0B
    __REG_RESULT_INT_STATUS = 0x13
    __REG_RESULT_RANGE = 0x14
    __REG_MSRC_CONFIG = 0x60
    __REG_FINAL_RANGE_VCSEL = 0x70
    __REG_SPAD_ENABLES = 0xB0
    __REG_REF_START_SELECT = 0xB6
    __REG_DYNAMIC_SPAD_COUNT = 0x4E
    __REG_DYNAMIC_SPAD_OFFSET = 0x4F

    def __init__(self, scl: int, sda: int, addr: int = 0x29):
        """
        Initialize the VL53L0X sensor with the specified I2C pins and address.
        
        :param scl: GPIO pin number for the SCL line.
        :param sda: GPIO pin number for the SDA line.
        :param addr: I2C address of the sensor (default is 0x29).
        """
        self.__bus = I2c(scl=scl, sda=sda, addr=addr)
        self.__measurement_active = False
        self.__initialize_sensor()
        self.__timing_budget_us = 33000
        self.__measurement_timing_budget = 33000  # triggers property setter to configure registers

    def read_distance(self) -> int:
        """
        Read the distance measurement from the sensor.
        This method triggers a measurement if one is not already active,
        waits for the measurement to complete, and then fetches the distance.
        
        :return: Distance in millimeters, or None if the measurement is not ready.
        """
        if not self.__measurement_active:
            self.__trigger_measurement()
        while not self.__is_measurement_ready():
            utime.sleep_ms(1)
        return self.__fetch_distance()

    def start_continuous(self, period_ms: int = 0) -> None:
        """
        Start continuous measurements with the specified period in milliseconds.
        If period_ms is 0, continuous measurements will run at the default timing budget.

        :param period_ms: Measurement period in milliseconds (default is 0, which uses the timing budget).
        :raises ValueError: If period_ms is less than the minimum required period.
        """
        min_period = self.__timing_budget_us // 1000 + 5
        if period_ms and period_ms < min_period:
            raise ValueError(f"period_ms must be ≥{min_period}")
        self.__bus.write_u8(0x80, 1)
        self.__bus.write_u8(0xFF, 1)
        self.__bus.write_u8(0, 0)
        if period_ms:
            self.__bus.write_u8(0x91, self.__stop_reg)
            self.__bus.write_u8(0, 1)
            self.__bus.write_u8(0x04, period_ms * 1000)
        else:
            self.__bus.write_u8(0, 0)
        self.__bus.write_u8(0xFF, 0)
        self.__bus.write_u8(0x80, 0)
        self.__bus.write_u8(self.__SYSRANGE_START, 0x02)

    def stop_continuous(self) -> None:
        """
        Stop continuous measurements and reset the sensor to single-shot mode.
        This method clears the interrupt and stops the measurement.
        """
        self.__bus.write_u8(self.__SYSRANGE_START, 0x01)
        self.__bus.write_u8(self.__SYS_INTERRUPT_CLEAR, 1)

    def read_continuous(self) -> int | None:
        """
        Read the distance measurement in continuous mode.
        This method checks if a measurement is ready, and if so, fetches the distance.
        
        :return: Distance in millimeters, or None if no measurement is ready.
        """
        if (self.__bus.read_u8(self.__REG_RESULT_INT_STATUS) & 0x07) == 0:
            return None
        result = self.__bus.read_u16(self.__REG_RESULT_RANGE + 10, little_endian=False)
        self.__bus.write_u8(self.__SYS_INTERRUPT_CLEAR, 1)
        return result

    def configure_long_range(self) -> None:
        """
        Configure the sensor for long-range measurements.
        This method sets the minimum signal rate and adjusts the final range VCSEL period.
        """
        self.__min_signal_rate = 0.05
        self.__bus.write_u8(self.__REG_FINAL_RANGE_VCSEL, (16 >> 1) - 1)
        self.set_timing_budget(40000)

    def configure_high_speed(self) -> None:
        """
        Configure the sensor for high-speed measurements.
        This method sets the minimum signal rate and adjusts the final range VCSEL period.
        """
        self.__min_signal_rate = 0.25
        self.set_timing_budget(20000)

    def set_timing_budget(self, budget_us: int) -> None:
        """
        Set the measurement timing budget in microseconds.
        This method updates the timing budget and configures the sensor registers accordingly.

        :param budget_us: Timing budget in microseconds (must be between 20000 and 330000).
        :raises ValueError: If budget_us is outside the valid range.
        """
        # Single assignment triggers register update
        self.__measurement_timing_budget = budget_us
        self.__timing_budget_us = budget_us

    def __decode_timeout_mclks(self, val: int) -> float:
        """
        Decode the timeout value from the sensor registers into microseconds.
        
        :param val: Encoded timeout value from the sensor registers.
        :return: Timeout in microseconds.
        """
        return float(val & 0xFF) * (2 ** ((val >> 8) & 0xFF)) + 1

    def __encode_timeout_mclks(self, mclks: int) -> int:
        """
        Encode the timeout value in microseconds into the format used by the sensor registers.
        
        :param mclks: Timeout in microseconds.
        :return: Encoded timeout value for the sensor registers.
        """
        m = mclks - 1
        e = 0
        while m > 0xFF:
            m >>= 1
            e += 1
        return ((e << 8) | (m & 0xFF)) & 0xFFFF

    def __mclks_to_microseconds(self, mclks: int, vcsel_period: int) -> int:
        """
        Convert macro clock cycles to microseconds.
        This method calculates the time in microseconds based on the number of macro clock cycles
        and the VCSEL period.
        
        :param mclks: Number of macro clock cycles.
        :param vcsel_period: VCSEL period in microseconds.
        :return: Time in microseconds.
        """
        macro_ns = ((2304 * vcsel_period * 1655) + 500) // 1000
        return ((mclks * macro_ns) + (macro_ns // 2)) // 1000

    def __microseconds_to_mclks(self, us: int, vcsel_period: int) -> int:
        """
        Convert microseconds to macro clock cycles.
        This method calculates the number of macro clock cycles based on the time in microseconds
        and the VCSEL period.

        :param us: Time in microseconds.
        :param vcsel_period: VCSEL period in microseconds.
        :return: Number of macro clock cycles.
        """
        macro_ns = ((2304 * vcsel_period * 1655) + 500) // 1000
        return ((us * 1000) + (macro_ns // 2)) // macro_ns

    def __trigger_measurement(self) -> None:
        """
        Trigger a single measurement by writing to the SYSRANGE_START register.
        This method checks if a measurement is already active, and if not, it clears the interrupt
        and starts a new measurement.
        """
        if self.__measurement_active:
            return
        self.__bus.write_u8(self.__SYS_INTERRUPT_CLEAR, 0x01)
        self.__bus.write_u8(self.__SYSRANGE_START, 0x01)
        self.__measurement_active = True

    def __is_measurement_ready(self) -> bool:
        """
        Check if a measurement is ready by reading the interrupt status register.
        This method returns True if a measurement is ready, otherwise it returns False.
        
        :return: True if measurement is ready, False otherwise.
        """
        if not self.__measurement_active:
            return False
        return (self.__bus.read_u8(self.__REG_RESULT_INT_STATUS) & 0x07) != 0

    def __fetch_distance(self) -> int:
        """
        Fetch the distance measurement from the sensor registers.
        This method reads the distance value from the RESULT_RANGE register,
        clears the interrupt, and stops the measurement.
        
        :return: Distance in millimeters.
        """
        distance = self.__bus.read_u16(self.__REG_RESULT_RANGE + 10, little_endian=False)
        self.__bus.write_u8(self.__SYS_INTERRUPT_CLEAR, 0x01)
        self.__bus.write_u8(self.__SYSRANGE_START, 0x00)
        self.__measurement_active = False
        return distance

    def __write_register_sequence(self, seq:tuple[tuple[int, int], ...]) -> None:
        """
        Write a sequence of register-value pairs to the sensor.
        This method takes a sequence of tuples, where each tuple contains a register address and a value,
        and writes them to the sensor's registers using I2C communication.

        :param seq: Sequence of tuples (register, value) to write to the sensor.
        """
        for reg, val in seq:
            self.__bus.write_u8(reg, val)

    def __initialize_sensor(self) -> None:
        """
        Initialize the VL53L0X sensor by performing a series of register writes
        """
        id_bytes = self.__bus.readfrom_mem(0xC0, 3)
        if id_bytes != b'\xEE\xAA\x10':
            raise RuntimeError("Sensor ID mismatch", id_bytes)
        self.__write_register_sequence(((0x88,0x00),(0x80,0x01),(0xFF,0x01),(0x00,0x00)))
        self.__stop_reg = self.__bus.read_u8(0x91)
        self.__write_register_sequence(((0x00,0x01),(0xFF,0x00),(0x80,0x00)))
        cfg = self.__bus.read_u8(self.__REG_MSRC_CONFIG)
        self.__bus.write_u8(self.__REG_MSRC_CONFIG, cfg | 0x12)
        self.__min_signal_rate = 0.25
        self.__bus.write_u8(self.__SYS_SEQUENCE_CONFIG, 0xFF)
        spad_count, spad_type = self.__retrieve_spad_info()
        spad_map = bytearray(7)
        self.__bus.readfrom_mem_into(self.__REG_SPAD_ENABLES, spad_map)
        self.__write_register_sequence(((0xFF,0x01),(self.__REG_DYNAMIC_SPAD_OFFSET,0x00),(self.__REG_DYNAMIC_SPAD_COUNT,0x2C),(0xFF,0x00),(self.__REG_REF_START_SELECT,0xB4)))
        first = 12 if spad_type else 0
        enabled = 0
        for i in range(48):
            idx = 1 + (i // 8)
            if i < first or enabled == spad_count:
                spad_map[idx] &= ~(1 << (i % 8))
            elif (spad_map[idx] >> (i % 8)) & 1:
                enabled += 1
        self.__bus.writeto_mem(self.__REG_SPAD_ENABLES, spad_map)
        seq = (
            (0xFF,0x01),(0x00,0x00),(0xFF,0x00),(0x09,0x00),(0x10,0x00),(0x11,0x00),(0x24,0x01),(0x25,0xFF),
            (0x75,0x00),(0xFF,0x01),(0x4E,0x2C),(0x48,0x00),(0x30,0x20),(0xFF,0x00),(0x30,0x09),(0x54,0x00),
            (0x31,0x04),(0x32,0x03),(0x40,0x83),(0x46,0x25),(0x60,0x00),(0x27,0x00),(0x50,0x06),(0x51,0x00),
            (0x52,0x96),(0x56,0x08),(0x57,0x30),(0x61,0x00),(0x62,0x00),(0x64,0x00),(0x65,0x00),(0x66,0xA0),
            (0xFF,0x01),(0x22,0x32),(0x47,0x14),(0x49,0xFF),(0x4A,0x00),(0xFF,0x00),(0x7A,0x0A),(0x7B,0x00),
            (0x78,0x21),(0xFF,0x01),(0x23,0x34),(0x42,0x00),(0x44,0xFF),(0x45,0x26),(0x46,0x05),(0x40,0x40),
            (0x0E,0x06),(0x20,0x1A),(0x43,0x40),(0xFF,0x00),(0x34,0x03),(0x35,0x44),(0xFF,0x01),(0x31,0x04),
            (0x4B,0x09),(0x4C,0x05),(0x4D,0x04),(0xFF,0x00),(0x44,0x00),(0x45,0x20),(0x47,0x08),(0x48,0x28),
            (0x67,0x00),(0x70,0x04),(0x71,0x01),(0x72,0xFE),(0x76,0x00),(0x77,0x00),(0xFF,0x01),(0x0D,0x01),
            (0xFF,0x00),(0x80,0x01),(0x01,0xF8),(0xFF,0x01),(0x8E,0x01),(0x00,0x01),(0xFF,0x00),(0x80,0x00)
        )
        self.__write_register_sequence(seq)
        self.__bus.write_u8(self.__SYS_INTERRUPT_CONFIG_GPIO, 0x04)
        gpio = self.__bus.read_u8(self.__GPIO_HV_MUX_HIGH)
        self.__bus.write_u8(self.__GPIO_HV_MUX_HIGH, gpio & ~0x10)
        self.__bus.write_u8(self.__SYS_INTERRUPT_CLEAR, 0x01)
        self.__measurement_timing_budget = self.__calculate_timing_budget()
        self.__bus.write_u8(self.__SYS_SEQUENCE_CONFIG, 0xE8)
        self.__bus.write_u8(self.__SYS_SEQUENCE_CONFIG, 0x01)
        self.__single_ref_calibration(0x40)
        self.__bus.write_u8(self.__SYS_SEQUENCE_CONFIG, 0x02)
        self.__single_ref_calibration(0x00)
        self.__bus.write_u8(self.__SYS_SEQUENCE_CONFIG, 0xE8)


class VL53L0X_old:
    """
    This VL53L0X driver implements I²C-based communication with ST’s Time-of-Flight distance sensor, 
    providing a streamlined interface to initialize the module, 
    configure ranging modes (single-shot or continuous), 
    and retrieve distance measurements with up to 120 cm range and ±13° field of view. 
    """
    __SYSRANGE_START = 0x00
    __SYSTEM_SEQUENCE_CONFIG = 0x01
    __SYSTEM_INTERRUPT_CONFIG_GPIO = 0x0A
    __GPIO_HV_MUX_ACTIVE_HIGH = 0x84
    __SYSTEM_INTERRUPT_CLEAR = 0x0B
    __RESULT_INTERRUPT_STATUS = 0x13
    __RESULT_RANGE_STATUS = 0x14
    __MSRC_CONFIG_CONTROL = 0x60
    __FINAL_RANGE_CONFIG_MIN_COUNT_RATE_RTN_LIMIT = 0x44
    __PRE_RANGE_CONFIG_VCSEL_PERIOD = 0x50
    __PRE_RANGE_CONFIG_TIMEOUT_MACROP_HI = 0x51
    __FINAL_RANGE_CONFIG_VCSEL_PERIOD = 0x70
    __FINAL_RANGE_CONFIG_TIMEOUT_MACROP_HI = 0x71
    __MSRC_CONFIG_TIMEOUT_MACROP = 0x46
    __GLOBAL_CONFIG_SPAD_ENABLES_REF_0 = 0xB0
    __GLOBAL_CONFIG_REF_EN_START_SELECT = 0xB6
    __DYNAMIC_SPAD_NUM_REQUESTED_REF_SPAD = 0x4E
    __DYNAMIC_SPAD_REF_EN_START_OFFSET = 0x4F
    __VCSEL_PERIOD_PRE_RANGE = 0
    __VCSEL_PERIOD_FINAL_RANGE = 1


    def __init__(self, scl:int,  sda:int, addr:int=0x29):
        """
        Initialize the VL53L0X sensor.
        This method sets up the I2C communication with the sensor and performs initial configuration.

        :param scl: GPIO pin number for SCL (I2C clock)
        :param sda: GPIO pin number for SDA (I2C data)
        :param addr: I2C address of the sensor (default: 0x29)
        """
        self._i2c = I2c(scl=scl, sda=sda, addr=addr)
        
        self.__range_started = False
        self._init_sensor()
        self._timing_budget_us = 33000
        
    def read(self):
        """
        Read the distance measurement from the sensor.
        
        :return: Distance in mm (millimeters)
        """
        if not self.__range_started:
            self._start_range_request()

        while not self._reading_available():
            utime.sleep_ms(1)

        return self._get_range_value()

    def start_continuous(self, period_ms=0):
        """
        Start continuous ranging mode.
        This method configures the sensor to continuously measure distances at a specified period.
        
        :param period_ms: Measurement period in milliseconds (default: 0, which uses the timing budget)
        """
        min_period = self._timing_budget_us // 1000 + 5
        if period_ms and period_ms < min_period:
            raise ValueError("period_ms must be ≥%d" % min_period)

        self._i2c.write_u8(0x80,1); self._i2c.write_u8(0xFF,1); self._i2c.write_u8(0,0)
        if period_ms:
            self._i2c.write_u8(0x91, self._stop_variable)
            self._i2c.write_u8(0,1)
            self._i2c.write_u8(0x04, period_ms*1000)
        else:
            self._i2c.write_u8(0,0)
        self._i2c.write_u8(0xFF,0); self._i2c.write_u8(0x80,0)

        self._i2c.write_u8(self.__SYSRANGE_START, 0x02) 

    def stop_continuous(self):
        """
        Stop continuous ranging mode.
        """
        self._i2c.write_u8(self.__SYSRANGE_START, 0x01)
        self._i2c.write_u8(self.__SYSTEM_INTERRUPT_CLEAR, 1)

    def read_continuous(self):
        """
        Read the distance measurement in continuous mode.
        
        :return: Distance in mm (millimeters) or None if no measurement is available
        """
        if (self._i2c.read_u8(self.__RESULT_INTERRUPT_STATUS) & 0x07) == 0:
            return None
        rng = self._i2c.read_u16(self.__RESULT_RANGE_STATUS + 10, little_endian=False)
        self._i2c.write_u8(self.__SYSTEM_INTERRUPT_CLEAR, 1)
        return rng

    def set_long_range(self):
        """
        Set the sensor to long range mode.
        """
        self._signal_rate_limit = 0.05        # MCPS under ↓
        self._i2c.write_u8(self.__FINAL_RANGE_CONFIG_VCSEL_PERIOD, (16 >> 1) - 1)  # VCSEL = 16 PCLK
        self.set_timing_budget(40000)

    def set_high_speed(self):
        """
        Set the sensor to high speed mode.
        """
        self._signal_rate_limit = 0.25
        self.set_timing_budget(20000)

    def set_timing_budget(self, budget_us):
        """
        Set the measurement timing budget.
        """
        self._measurement_timing_budget = budget_us
        self._timing_budget_us = budget_us
        
    # ST Library functions START
    def _decode_timeout(self, val):
        return float(val & 0xFF) * math.pow(2.0, ((val & 0xFF00) >> 8)) + 1

    def _encode_timeout(self, timeout_mclks):
        timeout_mclks = int(timeout_mclks) & 0xFFFF
        ls_byte = 0
        ms_byte = 0
        if timeout_mclks > 0:
            ls_byte = timeout_mclks - 1
            while ls_byte > 255:
                ls_byte >>= 1
                ms_byte += 1
            return ((ms_byte << 8) | (ls_byte & 0xFF)) & 0xFFFF
        return 0

    def _timeout_mclks_to_microseconds(self, timeout_period_mclks, vcsel_period_pclks):
        macro_period_ns = ((2304 * (vcsel_period_pclks) * 1655) + 500) // 1000
        return ((timeout_period_mclks * macro_period_ns) + (macro_period_ns // 2)) // 1000

    def _timeout_microseconds_to_mclks(self, timeout_period_us, vcsel_period_pclks):
        macro_period_ns = ((2304 * (vcsel_period_pclks) * 1655) + 500) // 1000
        return ((timeout_period_us * 1000) + (macro_period_ns // 2)) // macro_period_ns
    # ST Library functions END

    def _start_range_request(self):
        if self.__range_started == True: 
            return

        """old code
        for reg, val in ((0x80, 0x01), (0xFF, 0x01), (0x00, 0x00), (0x91, self._stop_variable), (0x00, 0x01), (0xFF, 0x00), (0x80, 0x00)):
            self._i2c.write_u8(reg, val)
        """
        self._i2c.write_u8(self.__SYSTEM_INTERRUPT_CLEAR, 0x01)
        self._i2c.write_u8(self.__SYSRANGE_START, 0x01)
        self.__range_started = True        

    def _reading_available(self):
        if self.__range_started == False: 
            return False
        
        return (self._i2c.read_u8(self.__RESULT_INTERRUPT_STATUS) & 0x07) != 0

    def _get_range_value(self):
        if not self.__range_started:
            return None

        rng = self._i2c.read_u16(self.__RESULT_RANGE_STATUS + 10, little_endian=False)
        self._i2c.write_u8(self.__SYSTEM_INTERRUPT_CLEAR, 0x01) 
        self._i2c.write_u8(self.__SYSRANGE_START, 0x00) 
        self.__range_started = False
        
        return rng
    
    def _set_register(self, config:tuple):
        """
        Configure the sensor with the given configuration.\r
\1 config: tuple containing register addresses and values
        """
        for reg, val in config:
            self._i2c.write_u8(reg, val)
    
    def _init_sensor(self):
        id_bytes = self._i2c.readfrom_mem(0xC0, 3)
        if id_bytes != b'\xEE\xAA\x10':
            raise RuntimeError("Failed to find expected ID register values. (C0,C1,C2):", id_bytes)
                
        self._set_register( ((0x88, 0x00), (0x80, 0x01), (0xFF, 0x01), (0x00, 0x00)) )

        self._stop_variable = self._i2c.read_u8(0x91)

        self._set_register( ((0x00, 0x01), (0xFF, 0x00), (0x80, 0x00)) )

        config_control = self._i2c.read_u8(self.__MSRC_CONFIG_CONTROL) | 0x12
        self._i2c.write_u8(self.__MSRC_CONFIG_CONTROL, config_control)

        self._signal_rate_limit = 0.25
        self._i2c.write_u8(self.__SYSTEM_SEQUENCE_CONFIG, 0xFF)
        spad_count, spad_is_aperture = self._get_spad_info()

        ref_spad_map = bytearray(7)
        self._i2c.readfrom_mem_into(self.__GLOBAL_CONFIG_SPAD_ENABLES_REF_0, ref_spad_map)

        self._set_register(
            ((0xFF, 0x01),
            (self.__DYNAMIC_SPAD_REF_EN_START_OFFSET, 0x00),
            (self.__DYNAMIC_SPAD_NUM_REQUESTED_REF_SPAD, 0x2C),
            (0xFF, 0x00),
            (self.__GLOBAL_CONFIG_REF_EN_START_SELECT, 0xB4))
        )

        first_spad_to_enable = 12 if spad_is_aperture else 0
        spads_enabled = 0
        
        for i in range(48):
            if i < first_spad_to_enable or spads_enabled == spad_count:
                ref_spad_map[1 + (i // 8)] &= ~(1 << (i % 8))
            elif (ref_spad_map[1 + (i // 8)] >> (i % 8)) & 0x1 > 0:
                spads_enabled += 1
        
        self._i2c.writeto_mem(self.__GLOBAL_CONFIG_SPAD_ENABLES_REF_0, ref_spad_map)
        
        self._set_register(
            ((0xFF, 0x01), (0x00, 0x00), (0xFF, 0x00), (0x09, 0x00), (0x10, 0x00), (0x11, 0x00), (0x24, 0x01), (0x25, 0xFF),
            (0x75, 0x00), (0xFF, 0x01), (0x4E, 0x2C), (0x48, 0x00), (0x30, 0x20), (0xFF, 0x00), (0x30, 0x09), (0x54, 0x00),
            (0x31, 0x04), (0x32, 0x03), (0x40, 0x83), (0x46, 0x25), (0x60, 0x00), (0x27, 0x00), (0x50, 0x06), (0x51, 0x00),
            (0x52, 0x96), (0x56, 0x08), (0x57, 0x30), (0x61, 0x00), (0x62, 0x00), (0x64, 0x00), (0x65, 0x00), (0x66, 0xA0),
            (0xFF, 0x01), (0x22, 0x32), (0x47, 0x14), (0x49, 0xFF), (0x4A, 0x00), (0xFF, 0x00), (0x7A, 0x0A), (0x7B, 0x00),
            (0x78, 0x21), (0xFF, 0x01), (0x23, 0x34), (0x42, 0x00), (0x44, 0xFF), (0x45, 0x26), (0x46, 0x05), (0x40, 0x40),
            (0x0E, 0x06), (0x20, 0x1A), (0x43, 0x40), (0xFF, 0x00), (0x34, 0x03), (0x35, 0x44), (0xFF, 0x01), (0x31, 0x04),
            (0x4B, 0x09), (0x4C, 0x05), (0x4D, 0x04), (0xFF, 0x00), (0x44, 0x00), (0x45, 0x20), (0x47, 0x08), (0x48, 0x28),
            (0x67, 0x00), (0x70, 0x04), (0x71, 0x01), (0x72, 0xFE), (0x76, 0x00), (0x77, 0x00), (0xFF, 0x01), (0x0D, 0x01),
            (0xFF, 0x00), (0x80, 0x01), (0x01, 0xF8), (0xFF, 0x01), (0x8E, 0x01), (0x00, 0x01), (0xFF, 0x00), (0x80, 0x00))
        )

        self._i2c.write_u8(self.__SYSTEM_INTERRUPT_CONFIG_GPIO, 0x04)
        gpio_hv_mux_active_high = self._i2c.read_u8(self.__GPIO_HV_MUX_ACTIVE_HIGH)
        self._i2c.write_u8(self.__GPIO_HV_MUX_ACTIVE_HIGH, gpio_hv_mux_active_high & ~0x10)
        self._i2c.write_u8(self.__SYSTEM_INTERRUPT_CLEAR, 0x01)
        self._measurement_timing_budget_us = self._measurement_timing_budget
        self._i2c.write_u8(self.__SYSTEM_SEQUENCE_CONFIG, 0xE8)
        self._measurement_timing_budget = self._measurement_timing_budget_us
        self._i2c.write_u8(self.__SYSTEM_SEQUENCE_CONFIG, 0x01)
        self._perform_single_ref_calibration(0x40)
        self._i2c.write_u8(self.__SYSTEM_SEQUENCE_CONFIG, 0x02)
        self._perform_single_ref_calibration(0x00)
        self._i2c.write_u8(self.__SYSTEM_SEQUENCE_CONFIG, 0xE8)
    
    def _get_spad_info(self):
        self._set_register( ((0x80, 0x01), (0xFF, 0x01), (0x00, 0x00), (0xFF, 0x06)) )
        self._i2c.write_u8(0x83, self._i2c.read_u8(0x83) | 0x04)
        self._set_register( ((0xFF, 0x07), (0x81, 0x01), (0x80, 0x01), (0x94, 0x6B), (0x83, 0x00)) )

        while self._i2c.read_u8(0x83) == 0x00:
            utime.sleep_ms(1)
            
        self._i2c.write_u8(0x83, 0x01)
        tmp = self._i2c.read_u8(0x92)
        count = tmp & 0x7F
        is_aperture = ((tmp >> 7) & 0x01) == 1
        
        self._set_register( ((0x81, 0x00), (0xFF, 0x06)) )        
        self._i2c.write_u8(0x83, self._i2c.read_u8(0x83) & ~0x04)
        self._set_register( ((0xFF, 0x01), (0x00, 0x01), (0xFF, 0x00), (0x80, 0x00)) )
        
        return (count, is_aperture)

    def _perform_single_ref_calibration(self, vhv_init_byte):
        self._i2c.write_u8(self.__SYSRANGE_START, 0x01 | vhv_init_byte & 0xFF)
        
        while (self._i2c.read_u8(self.__RESULT_INTERRUPT_STATUS) & 0x07) == 0:
            utime.sleep_ms(1)
            
        self._i2c.write_u8(self.__SYSTEM_INTERRUPT_CLEAR, 0x01)
        self._i2c.write_u8(self.__SYSRANGE_START, 0x00)

    def _get_vcsel_pulse_period(self, vcsel_period_type):
        ret = 255
        
        if vcsel_period_type == self.__VCSEL_PERIOD_PRE_RANGE:
            val = self._i2c.read_u8(self.__PRE_RANGE_CONFIG_VCSEL_PERIOD)
            ret = (((val) + 1) & 0xFF) << 1
        elif vcsel_period_type == self.__VCSEL_PERIOD_FINAL_RANGE:
            val = self._i2c.read_u8(self.__FINAL_RANGE_CONFIG_VCSEL_PERIOD)
            ret = (((val) + 1) & 0xFF) << 1
        
        return ret

    def _get_sequence_step_enables(self):
        sequence_config = self._i2c.read_u8(self.__SYSTEM_SEQUENCE_CONFIG)
        tcc = (sequence_config >> 4) & 0x1 > 0
        dss = (sequence_config >> 3) & 0x1 > 0
        msrc = (sequence_config >> 2) & 0x1 > 0
        pre_range = (sequence_config >> 6) & 0x1 > 0
        final_range = (sequence_config >> 7) & 0x1 > 0
        
        return (tcc, dss, msrc, pre_range, final_range)

    def _get_sequence_step_timeouts(self, pre_range):
        pre_range_vcsel_period_pclks = self._get_vcsel_pulse_period(self.__VCSEL_PERIOD_PRE_RANGE)
        msrc_dss_tcc_mclks = (self._i2c.read_u8(self.__MSRC_CONFIG_TIMEOUT_MACROP) + 1) & 0xFF
        msrc_dss_tcc_us = self._timeout_mclks_to_microseconds(msrc_dss_tcc_mclks, pre_range_vcsel_period_pclks)
        pre_range_mclks = self._decode_timeout(self._i2c.read_u16(self.__PRE_RANGE_CONFIG_TIMEOUT_MACROP_HI, little_endian=False))
        pre_range_us = self._timeout_mclks_to_microseconds(pre_range_mclks, pre_range_vcsel_period_pclks)
        final_range_vcsel_period_pclks = self._get_vcsel_pulse_period(self.__VCSEL_PERIOD_FINAL_RANGE)
        final_range_mclks = self._decode_timeout(self._i2c.read_u16(self.__FINAL_RANGE_CONFIG_TIMEOUT_MACROP_HI, little_endian=False))
        if pre_range:
            final_range_mclks -= pre_range_mclks
            
        final_range_us = self._timeout_mclks_to_microseconds(final_range_mclks, final_range_vcsel_period_pclks)
        
        return (msrc_dss_tcc_us, pre_range_us, final_range_us, final_range_vcsel_period_pclks, pre_range_mclks)

    @property
    def _signal_rate_limit(self):
        val = self._i2c.read_u16(self.__FINAL_RANGE_CONFIG_MIN_COUNT_RATE_RTN_LIMIT, little_endian=False)

        return val / (1 << 7)

    @_signal_rate_limit.setter
    def _signal_rate_limit(self, val):
        assert 0.0 <= val <= 511.99

        val = int(val * (1 << 7))
        self._i2c.write_u16(self.__FINAL_RANGE_CONFIG_MIN_COUNT_RATE_RTN_LIMIT, val)

    @property
    def _measurement_timing_budget(self):

        budget_us = 1910 + 960
        tcc, dss, msrc, pre_range, final_range = self._get_sequence_step_enables()
        step_timeouts = self._get_sequence_step_timeouts(pre_range)
        msrc_dss_tcc_us, pre_range_us, final_range_us, _, _ = step_timeouts
        
        if tcc:
            budget_us += msrc_dss_tcc_us + 590
        if dss:
            budget_us += 2 * (msrc_dss_tcc_us + 690)
        elif msrc:
            budget_us += msrc_dss_tcc_us + 660
        if pre_range:
            budget_us += pre_range_us + 660
        if final_range:
            budget_us += final_range_us + 550
        self._measurement_timing_budget_us = budget_us
        
        return budget_us

    @_measurement_timing_budget.setter
    def _measurement_timing_budget(self, budget_us):
        assert budget_us >= 20000
        
        used_budget_us = 1320 + 960
        tcc, dss, msrc, pre_range, final_range = self._get_sequence_step_enables()
        step_timeouts = self._get_sequence_step_timeouts(pre_range)
        msrc_dss_tcc_us, pre_range_us, _ = step_timeouts[:3]
        final_range_vcsel_period_pclks, pre_range_mclks = step_timeouts[3:]
        
        if tcc:
            used_budget_us += msrc_dss_tcc_us + 590
        if dss:
            used_budget_us += 2 * (msrc_dss_tcc_us + 690)
        elif msrc:
            used_budget_us += msrc_dss_tcc_us + 660
        if pre_range:
            used_budget_us += pre_range_us + 660
        if final_range:
            used_budget_us += 550

            if used_budget_us > budget_us:
                raise ValueError("Requested timeout too big.")
            
            final_range_timeout_us = budget_us - used_budget_us
            final_range_timeout_mclks = self._timeout_microseconds_to_mclks(final_range_timeout_us, final_range_vcsel_period_pclks)
            
            if pre_range:
                final_range_timeout_mclks += pre_range_mclks
            self._i2c.write_u16(self.__FINAL_RANGE_CONFIG_TIMEOUT_MACROP_HI, self._encode_timeout(final_range_timeout_mclks))
            self._measurement_timing_budget_us = budget_us


class BNO055:
    """
    A class to read data from the BNO055 9-DoF sensor.
    This class provides methods to read acceleration, gyroscope, magnetic field, Euler angles, quaternion, and temperature data.
    """
    ACCELERATION  = 0x08   # raw accel (include gravity)
    MAGNETIC      = 0x0E
    GYROSCOPE     = 0x14
    EULER         = 0x1A
    QUATERNION    = 0x20
    ACCEL_LINEAR  = 0x28   # linear accel (exclude gravity)
    ACCEL_GRAVITY = 0x2E
    TEMPERATURE   = 0x34

    __MODE_CONFIG  = 0x00
    __MODE_NDOF    = 0x0C
    __PWR_NORMAL   = 0x00

    __SCALE = {
        ACCELERATION : 1/100,           # m/s² (1 LSB = 0.01 m/s²)
        ACCEL_LINEAR : 1/100,
        ACCEL_GRAVITY: 1/100,
        MAGNETIC     : 1/16,            # µT
        GYROSCOPE    : 1/900,           # rad/s (0.0625 °/s)
        EULER        : 1/16,            # °
        QUATERNION   : 1/(1<<14),       # dimensionless
    }

    def __init__(self, scl:int, sda:int, addr:int=0x28, freq:int=400_000):
        """
        Initialize the BNO055 sensor.
        
        :param scl: SCL pin number (GPIO pin)
        :param sda: SDA pin number (GPIO pin)
        :param addr: I2C address of the BNO055 sensor (default is 0x28)
        :param freq: I2C frequency (default is 400kHz)
        """
        self._i2c  = I2c(scl=scl, sda=sda, addr=addr, freq=freq)

        w8 = self._i2c.write_u8

        w8(0x3F, 0x20)                 # SYS_TRIGGER – reset
        utime.sleep_ms(700)

        w8(0x3D, self.__MODE_CONFIG)    # OPR_MODE – CONFIG
        utime.sleep_ms(25)

        w8(0x3E, self.__PWR_NORMAL)     # PWR_MODE – Normal
        w8(0x07, 0x00)                 # PAGE_ID   – page 0

        w8(0x3F, 0x80)                 # use external crystal
        utime.sleep_ms(10)

        w8(0x3D, self.__MODE_NDOF)      # OPR_MODE – NDOF(9-DoF)
        utime.sleep_ms(20)

    def __read_vector(self, reg, count, conv):
        """
        Read a vector of integers from the specified register.
        
        :param reg: The register address to read from.
        :param count: The number of integers to read.
        :param conv: The conversion factor to apply to the read integers.
        :return: A tuple of integers, converted if `conv` is not None.
        """
        data = self._i2c.readfrom_mem(reg, count*2)
        ints = ustruct.unpack('<' + 'h'*count, data)
        if conv is None:
            return ints              # raw
        if count == 1:
            return ints[0] * conv
        return tuple(v * conv for v in ints)

    def temperature(self) -> int:
        """
        Read the temperature from the BNO055 sensor.
        
        :return: The temperature in degrees Celsius.
        """
        t = self._i2c.read_u8(self.TEMPERATURE)
        return t - 256 if t > 127 else t

    def accel(self, linear:bool=False, gravity:bool=False):
        """
        Read acceleration data from the BNO055 sensor.
        
        :param linear: If True, read linear acceleration (exclude gravity).
        :param gravity: If True, read gravity acceleration (exclude linear).
        :return: A tuple of acceleration values (x, y, z) in m/s².
        """
        if gravity:      reg = self.ACCEL_GRAVITY
        elif linear:     reg = self.ACCEL_LINEAR
        else:            reg = self.ACCELERATION
        return self.__read_vector(reg, 3, self.__SCALE[reg])

    def gyro(self):
        """
        Read gyroscope data from the BNO055 sensor.
        
        :return: A tuple of gyroscope values (x, y, z) in rad/s.
        """
        return self.__read_vector(self.GYROSCOPE, 3, self.__SCALE[self.GYROSCOPE])

    def mag(self):
        """
        Read magnetic field data from the BNO055 sensor.
        
        :return: A tuple of magnetic field values (x, y, z) in µT.
        """
        return self.__read_vector(self.MAGNETIC, 3, self.__SCALE[self.MAGNETIC])

    def euler(self):
        """
        Read Euler angles from the BNO055 sensor.
        
        :return: A tuple of Euler angles (heading, roll, pitch) in degrees.
        """
        return self.__read_vector(self.EULER, 3, self.__SCALE[self.EULER])

    def quaternion(self):
        """
        Read quaternion data from the BNO055 sensor.
        
        :return: A tuple of quaternion values (w, x, y, z).
        """
        return self.__read_vector(self.QUATERNION, 4, self.__SCALE[self.QUATERNION])

    def calibration(self):
        """
        Read the calibration status of the BNO055 sensor.
        The calibration status is returned as a tuple of four values: (system, gyro, accel, mag).
        
        :return: A tuple of calibration status values (system, gyro, accel, mag).
        """
        stat = self._i2c.read_u8(0x35)
        return (stat >> 6 & 3, stat >> 4 & 3, stat >> 2 & 3, stat & 3)

    def read(self, what):
        """
        Read data from the BNO055 sensor based on the specified register group.
        
        :param what: The register group to read from. It can be one of the following:
        - BNO055.TEMPERATURE
        - BNO055.ACCELERATION
        - BNO055.ACCEL_LINEAR
        - BNO055.ACCEL_GRAVITY
        - BNO055.GYROSCOPE
        - BNO055.MAGNETIC
        - BNO055.EULER
        - BNO055.QUATERNION
        :return: The data read from the specified register group.
        :raises ValueError: If the specified register group is unknown.
        """
        if what == self.TEMPERATURE:              return self.temperature()
        if what == self.ACCELERATION:             return self.accel()
        if what == self.ACCEL_LINEAR:             return self.accel(linear=True)
        if what == self.ACCEL_GRAVITY:            return self.accel(gravity=True)
        if what == self.GYROSCOPE:                return self.gyro()
        if what == self.MAGNETIC:                 return self.mag()
        if what == self.EULER:                    return self.euler()
        if what == self.QUATERNION:               return self.quaternion()
        raise ValueError("unknown register group")


class BME68x:
    def __init__(self, scl:int, sda:int, addr:int=0x77,
                 *,
                 temp_weighting=0.10,  pressure_weighting=0.05,
                 humi_weighting=0.20,  gas_weighting=0.65,
                 gas_ema_alpha=0.1,
                 temp_baseline=23.0,  pressure_baseline=1013.25,
                 humi_baseline=45.0,  gas_baseline=450_000):
        """
        A class to read data from the BME68x environmental sensor.
        This class provides methods to read temperature, pressure, humidity, and gas resistance data.
        
        :param scl: SCL pin number (GPIO pin)
        :param sda: SDA pin number (GPIO pin)
        :param addr: I2C address of the BME68x sensor (default is 0x77)
        :param temp_weighting: Weighting factor for temperature (default is 0.10)
        :param pressure_weighting: Weighting factor for pressure (default is 0.05)
        :param humi_weighting: Weighting factor for humidity (default is 0.20)
        :param gas_weighting: Weighting factor for gas resistance (default is 0.65)
        :param gas_ema_alpha: Exponential moving average alpha for gas resistance (default is 0.1)
        :param temp_baseline: Baseline temperature in degrees Celsius (default is 23.0)
        :param pressure_baseline: Baseline pressure in hPa (default is 1013.25)
        :param humi_baseline: Baseline humidity in % (default is 45.0)
        :param gas_baseline: Baseline gas resistance in ohms (default is 450000)
        """
        self._i2c = I2c(scl=scl, sda=sda, addr=addr)

        self._i2c.writeto_mem(0xE0, b'\xB6')      # soft-reset
        utime.sleep_ms(5)
        self._set_power_mode(0x00)                # sleep

        t_cal = bytearray(self._i2c.readfrom_mem(0x89, 25))
        t_cal += self._i2c.readfrom_mem(0xE1, 16)

        self._sw_err = (self._i2c.readfrom_mem(0x04, 1)[0] & 0xF0) >> 4

        calib = list(ustruct.unpack('<hbBHhbBhhbbHhhBBBHbbbBbHhbb',
                                    bytes(t_cal[1:39])))
        self._temp_calibration     = [calib[i] for i in (23, 0, 1)]
        self._pressure_calibration = [calib[i] for i in (3,4,5,7,8,10,9,12,13,14)]
        self._humidity_calibration = [calib[i] for i in (17,16,18,19,20,21,22)]

        self._humidity_calibration[1] = (
            self._humidity_calibration[1] * 16
            + self._humidity_calibration[0] % 16
        )
        self._humidity_calibration[0] //= 16

        self._i2c.writeto_mem(0x72, b'\x01')                # hum OSR x1
        self._i2c.writeto_mem(0x74, bytes([(0b010 << 5) | (0b011 << 2)]))
        self._i2c.writeto_mem(0x75, bytes([0b001 << 2]))    # IIR filter 3

        self._i2c.writeto_mem(0x50, b'\x1F')                # idac_heat_0
        self._i2c.writeto_mem(0x5A, b'\x73')                # res_heat_0
        self._i2c.writeto_mem(0x64, b'\x64')                # gas_wait_0 =100 ms

        self._i2c.writeto_mem(0x71, bytes([(1 << 4) | 0x00]))  # run_gas
        utime.sleep_ms(50)

        self._temperature_correction = -10
        self._t_fine = self._adc_pres = self._adc_temp = None
        self._adc_hum = self._adc_gas = self._gas_range = None

        self.temp_weighting     = temp_weighting
        self.pressure_weighting = pressure_weighting
        self.humi_weighting     = humi_weighting
        self.gas_weighting      = gas_weighting
        self.gas_ema_alpha      = gas_ema_alpha

        self.temp_baseline     = temp_baseline
        self.pressure_baseline = pressure_baseline
        self.humi_baseline     = humi_baseline
        self.gas_baseline      = gas_baseline

        if abs((temp_weighting   + pressure_weighting +
                humi_weighting   + gas_weighting) - 1.0) > 1e-3:
            raise ValueError("Weightings must sum to 1.0")

    def _set_power_mode(self, mode:int):
        """
        Set the power mode of the BME68x sensor.
        
        :param mode: The power mode to set (0x00 for sleep, 0x01 for forced, etc.).
        """
        reg = self._i2c.readfrom_mem(0x74, 1)[0] & ~0x03
        self._i2c.writeto_mem(0x74, bytes([reg | mode]))
        utime.sleep_ms(1)

    def _reset_sensor(self) -> bool:
        """
        Attempt to reset the BME68x sensor.
        This method tries to reset the sensor by writing to specific registers and checking the status.
        
        :return: True if the reset was successful, False otherwise.
        """
        self._i2c.writeto_mem(0xE0, b'\xB6')
        utime.sleep_ms(10)

        start = utime.ticks_ms()
        while utime.ticks_diff(utime.ticks_ms(), start) < 500:
            try:
                if self._i2c.readfrom_mem(0xD0, 1)[0] == 0x61:
                    # 재초기화
                    self._i2c.writeto_mem(0x72, b'\x01')
                    self._i2c.writeto_mem(0x74, bytes([(0b010 << 5) | (0b011 << 2)]))
                    self._i2c.writeto_mem(0x75, bytes([0b001 << 2]))
                    self._i2c.writeto_mem(0x50, b'\x1F')
                    self._i2c.writeto_mem(0x5A, b'\x73')
                    self._i2c.writeto_mem(0x64, b'\x64')
                    self._i2c.writeto_mem(0x71, bytes([(1 << 4) | 0x00]))
                    utime.sleep_ms(50)
                    return True
            except:
                pass
            utime.sleep_ms(10)
        return False

    def _perform_reading(self, retries:int=5):
        """
        Perform a reading from the BME68x sensor.
        This method attempts to read data from the sensor, retrying if necessary.
        
        :param retries: The number of retries to attempt if the reading fails (default is 5).
        """
        attempts, reset_done = 0, False
        while attempts < retries:
            attempts += 1
            try:
                self._i2c.writeto_mem(0x71, bytes([(1 << 4) | 0x00])) # forced mode (one-time measurement)
                self._set_power_mode(0x01)
                utime.sleep_ms(50)

                start = utime.ticks_ms()
                while utime.ticks_diff(utime.ticks_ms(), start) < 500:
                    s = self._i2c.readfrom_mem(0x1D, 1)[0]
                    if (s & 0x20) == 0 and (s & 0x80):
                        buf = self._i2c.readfrom_mem(0x1D, 17)
                        self._adc_pres = (buf[2] << 12) | (buf[3] << 4) | (buf[4] >> 4)
                        self._adc_temp = (buf[5] << 12) | (buf[6] << 4) | (buf[7] >> 4)
                        self._adc_hum  = (buf[8] << 8)  | buf[9]
                        self._adc_gas  = ((buf[13] << 2) | (buf[14] >> 6))
                        self._gas_range = buf[14] & 0x0F

                        # callculate temperature
                        v1 = (self._adc_temp / 8) - (self._temp_calibration[0] * 2)
                        v2 = (v1 * self._temp_calibration[1]) / 2048
                        v3 = ((v1 / 2) * (v1 / 2)) / 4096
                        v3 = (v3 * self._temp_calibration[2] * 16) / 16384
                        self._t_fine = int(v2 + v3)
                        return
                    utime.sleep_ms(10)

                if not reset_done and attempts >= (retries // 2):
                    reset_done = self._reset_sensor()
                    continue
            except:
                pass
            utime.sleep_ms(100 * attempts)
        raise OSError("BME68x: data not ready – power-cycle recommended")

    def _temperature(self) -> float:
        """
        Calculate the temperature in degrees Celsius.
        
        :return: The temperature in degrees Celsius.
        """
        return ((((self._t_fine * 5) + 128) / 256) / 100) + self._temperature_correction

    def _pressure(self) -> float:
        """
        Calculate the pressure in hPa.
        
        :return: The pressure in hPa.
        """
        v1 = (self._t_fine / 2) - 64000
        v2 = ((v1 / 4) ** 2) / 2048 * self._pressure_calibration[5] / 4
        v2 += (v1 * self._pressure_calibration[4] * 2)
        v2 = (v2 / 4) + (self._pressure_calibration[3] * 65536)
        v1 = (((((v1 / 4) ** 2) / 8192) * self._pressure_calibration[2] * 32) / 8 +
              (self._pressure_calibration[1] * v1) / 2) / 262144
        v1 = ((32768 + v1) * self._pressure_calibration[0]) / 32768
        p  = (1048576 - self._adc_pres - (v2 / 4096)) * 3125
        p  = (p / v1) * 2
        v1 = (self._pressure_calibration[8] * ((p / 8) ** 2) / 8192) / 4096
        v2 = ((p / 4) * self._pressure_calibration[7]) / 8192
        v3 = (((p / 256) ** 3) * self._pressure_calibration[9]) / 131072
        p += (v1 + v2 + v3 + (self._pressure_calibration[6] * 128)) / 16
        return p / 100

    def _humidity(self) -> float:
        """
        Calculate the relative humidity in percentage.
        
        :return: The relative humidity in percentage.
        """
        t = ((self._t_fine * 5) + 128) / 256
        v1 = (self._adc_hum - (self._humidity_calibration[0] * 16) -
              ((t * self._humidity_calibration[2]) / 200))
        v2 = (self._humidity_calibration[1] *
              (16384 + ((t * self._humidity_calibration[3]) / 100) +
               (((t * ((t * self._humidity_calibration[4]) / 100)) / 64) / 100))) / 1024
        v3 = v1 * v2
        v4 = (self._humidity_calibration[5] * 128 +
              ((t * self._humidity_calibration[6]) / 100)) / 16
        v5 = ((v3 / 16384) ** 2) / 1024
        v6 = (v4 * v5) / 2
        h  = ((((v3 + v6) / 1024) * 1000) / 4096) / 1000
        return max(0, min(h, 100))

    def _gas(self) -> float:
        """
        Calculate the gas resistance in ohms.
        
        :return: The gas resistance in ohms.
        """
        lookup1 = {0:2147483647.0,1:2126008810.0,2:2130303777.0,3:2147483647.0,
                   4:2143188679.0,5:2136746228.0,6:2126008810.0,7:2147483647.0}
        lookup2 = {0:4096000000.0,1:2048000000.0,2:1024000000.0,3:512000000.0,
                   4:255744255.0,5:127110228.0,6:64000000.0,7:32258064.0,
                   8:16016016.0,9:8000000.0,10:4000000.0,11:2000000.0,
                   12:1000000.0,13:500000.0,14:250000.0,15:125000.0}
        var1 = ((1340 + (5 * self._sw_err)) * lookup1.get(self._gas_range, 2**31-1)) / 65536
        var2 = (self._adc_gas * 32768) - 16777216 + var1
        var3 = (lookup2.get(self._gas_range, 125000.0) * var1) / 512
        return (var3 + (var2 / 2)) / var2

    def read(self, *, gas:bool=False):
        """
        Read sensor data from the BME68x sensor.
        
        :param gas: If True, include gas resistance in the reading.
        :return: A tuple containing temperature, pressure, humidity, and gas resistance (if requested).
        - T °C, P hPa, RH %, Gas Ω/None
        """
        self._perform_reading()
        if gas:
            return self._temperature(), self._pressure(), self._humidity(), self._gas()
        return self._temperature(), self._pressure(), self._humidity(), None

    def iaq(self):
        """
        Calculate the Indoor-Air-Quality (IAQ) score based on sensor readings.
        
        :return: A tuple containing the IAQ score (0-500) and sensor values (temperature, pressure, humidity, gas resistance).
        """
        self._perform_reading()
        t, p, h, g = self._temperature(), self._pressure(), self._humidity(), self._gas()

        hum_score  = (1 - min(abs(h - self.humi_baseline) / (self.humi_baseline*2), 1)) * self.humi_weighting * 100
        temp_score = (1 - min(abs(t - self.temp_baseline) / 10, 1)) * self.temp_weighting * 100

        self.gas_baseline = (self.gas_ema_alpha * g) + ((1 - self.gas_ema_alpha) * self.gas_baseline)
        gas_score = max(0, min((self.gas_baseline - g) / self.gas_baseline, 1)) * self.gas_weighting * 100

        press_score = (1 - min(abs(p - self.pressure_baseline) / 50, 1)) * self.pressure_weighting * 100

        iaq = round((hum_score + temp_score + gas_score + press_score) * 5)
        return iaq, t, p, h, g

