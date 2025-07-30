from . import Dout


class Relay:
    ON = Dout.HIGH
    OFF = Dout.LOW

    class _Channel:
        """
        A class representing a single relay channel.
        This class provides properties to get and set the state of the relay,
        turn the relay on or off, and set the delay in milliseconds.
        """
        def __init__(self, parent:Relay, idx:int):
            """
            Initialize the relay channel with a reference to the parent Relay instance and its index.

            :param parent: Reference to the parent Relay instance
            :param idx: Index of the relay channel (0-based)
            """

        @property
        def state(self) -> int:
            """
            Get the current state of the relay channel.
            This property returns the state of the relay channel, which can be either Relay.ON or Relay.OFF.
            
            :return: Current state of the relay channel (Dout.HIGH or Dout.LOW)
            """

        @state.setter
        def state(self, val:int):
            """
            Set the state of the relay channel.
            This property sets the state of the relay channel to either Relay.ON or Relay.OFF.

            :param val: State to set (Dout.HIGH or Dout.LOW)
            """

        def on(self):
            """
            Turn the relay channel on.
            This method sets the state of the relay channel to Relay.ON.
            """

        def off(self):
            """
            Turn the relay channel off.
            This method sets the state of the relay channel to Relay.OFF.
            """

        @property
        def delay_ms(self) -> int:
            """
            Get the minimum delay in milliseconds for the relay channel.
            This property returns the minimum delay in milliseconds that is applied after changing the state of the relay channel.
            
            :return: Minimum delay in milliseconds
            """

        @delay_ms.setter
        def delay_ms(self, ms:int):
            """
            Set the minimum delay in milliseconds for the relay channel.
            This property sets the minimum delay in milliseconds that is applied after changing the state of the relay channel.
            
            :param ms: Minimum delay in milliseconds
            """

    class _Group:
        """
        A class representing a group of relay channels.
        This class allows setting attributes for all channels in the group at once.
        """
        def __init__(self, channels:tuple[int, ...]):
            """
            Initialize the group of relay channels.
            
            :param channels: Tuple of Relay._Channel objects representing the relay channels in the group
            """

        def __setattr__(self, name, value):
            """
            Set an attribute for all channels in the group.
            If the attribute name starts with an underscore, it is set on the group itself.
            
            :param name: Attribute name
            :param value: Value to set for the attribute
            """

        def __getattr__(self, name):
            """
            Get an attribute from the first channel in the group.
            """

    def __init__(self, pins:tuple[int, ...], min_delay_ms:int=5):
        """
        Initialize the Relay with specified GPIO pins and minimum delay.

        :param pins: Tuple of GPIO pin numbers for the relay channels (e.g., (2, 3, 4))
        :param min_delay_ms: Minimum delay in milliseconds after changing the state of a relay channel (default 5 ms)
        """

    def __getitem__(self, idx:int) -> _Channel:
        """
        Get the relay channel at the specified index.

        :param idx: Index of the relay channel (0-based)
        :return: Relay._Channel object for the specified index
        """

    def __len__(self) -> int:
        """
        Get the number of relay channels.
        
        :return: Number of relay channels
        """


class ServoMotor:
    """
    A class to control servo motors using PWM.
    This class allows setting the angle of individual servo motors and provides
    methods to set the angle for all servos at once.
    """
    class _Channel:
        """
        A class representing a single servo channel.
        This class provides properties to get and set the angle, speed, and non-blocking behavior of the servo.
        """
        def __init__(self, parent:ServoMotor, idx:int):
            """
            Initialize the servo channel with a reference to the parent ServoMotor instance and its index.
            :param parent: Reference to the parent ServoMotor instance
            :param idx: Index of the servo channel (0-based)
            """

        @property
        def angle(self) -> float:
            """
            Get the current angle of the servo channel.
            This property returns the current angle in degrees (0 to 180).
            
            :return: Current angle in degrees
            """

        @angle.setter
        def angle(self, deg:float) -> None:
            """
            Set the target angle for the servo channel.
            This property clamps the angle to the range [0, 180] degrees and updates the target angle.
            
            :param deg: Target angle in degrees (0 to 180)
            """

        @property
        def speed_ms(self) -> int:
            """
            Get the speed in milliseconds for the servo channel.
            This property returns the speed in milliseconds for moving to the target angle.
            
            :return: Speed in milliseconds
            """

        @speed_ms.setter
        def speed_ms(self, ms:int):
            """
            Set the speed in milliseconds for the servo channel.
            This property sets the speed for moving to the target angle.
            
            :param ms: Speed in milliseconds (0 for immediate movement)
            """

        @property
        def nonblocking(self) -> bool:
            """
            Get the non-blocking flag for the servo channel.
            This property indicates whether the servo channel operates in non-blocking mode.
            
            :return: True if non-blocking mode is enabled, False otherwise
            """

        @nonblocking.setter
        def nonblocking(self, flag: bool) -> None:
            """
            Set the non-blocking flag for the servo channel.
            This property enables or disables non-blocking mode for the servo channel.
            
            :param flag: True to enable non-blocking mode, False to disable
            """

    class _Group:
        def __init__(self, channels:tuple[int, ...]):
            """
            Initialize the group of servo channels.
            
            :param channels: List of ServoMotor._Channel objects
            """

        def __setattr__(self, name:str, value:int):
            """
            Set an attribute for all channels in the group.
            If the attribute name starts with an underscore, it is set on the group itself.
            
            :param name: Attribute name
            :param value: Value to set for the attribute
            """

        def __getattr__(self, name):
            """
            Get an attribute from the first channel in the group.
            If the attribute does not exist, it raises an AttributeError.
            
            :param name: Attribute name
            :return: Value of the attribute from the first channel
            """

    def __init__(self, pins:tuple[int, ...], freq:int=50, default_min_us:int=500, default_max_us: int=2500, initial_angle: float=0.0):
        """
        Initialize the ServoMotor with specified GPIO pins and parameters.
        
        :param pins: Tuple of GPIO pin numbers for the servo motors (e.g., (2, 3, 4))
        :param freq: PWM frequency in Hz (default 50 Hz)
        :param default_min_us: Default minimum pulse width in microseconds (default 500 us)
        :param default_max_us: Default maximum pulse width in microseconds (default 2500 us)
        :param initial_angle: Initial angle for all servos in degrees (default 0.0)
        """
        self.__channels = [ServoMotor._Channel(self, i) for i in range(len(pins))]
        self.all = ServoMotor._Group(self.__channels)

    def __getitem__(self, idx: int) -> _Channel:
        """
        Get the servo channel at the specified index.
        
        :param idx: Index of the servo channel (0-based)
        :return: ServoMotor._Channel object for the specified index
        """
        
    def deinit(self) -> None:
        """
        Deinitialize the ServoMotor instance.
        This method stops the timer and disables all PWM channels.
        """


class PiezoBuzzer:
    """
    A class to control a piezo buzzer using PWM.
    It can play tones, melodies, and supports effects like staccato, vibrato, and tremolo.
    """

    def __init__(self, pin:int, tempo:int=120):
        """
        Initialize the PiezoBuzzer with the specified pin and tempo.
        
        :param pin: GPIO pin number for the buzzer (default 1).
        :param tempo: Tempo in beats per minute (default 120).
        """

    def tone(self, note_oct:str, length:int=4, effect:str=None):
        """
        Play a single tone with the specified note, length, and effect.
        
        :param note_oct: Musical note with octave (e.g., 'C4', 'A#5').
        :param length: Length of the note in beats (default 4).
        :param effect: Effect to apply to the note (e.g., 'staccato', 'vibrato', 'tremolo', 'gliss:C#5').
        """

    def play(self, melody, effect:str=None, background:bool=False):
        """
        Play a melody consisting of notes and lengths.
        
        :param melody: List of notes and lengths (e.g., ['C4', 4, 'D4', 2, 'E4', 1]).
        :param effect: Effect to apply to the melody (e.g., 'staccato', 'vibrato', 'tremolo').
        :param background: If True, play the melody in the background (default False).
        """

    def stop(self):
        """
        Stop playing the current melody and reset the buzzer state.
        """

    def set_tempo(self, bpm:int):
        """
        Set the tempo for the buzzer in beats per minute.
        
        :param bpm: Tempo in beats per minute
        """


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
    
    def read(self, timeout_us:int=30_000, temp_c:float|None=None) -> float|None:
        """
        Read the distance from the ultrasonic sensor.
        
        :param timeout_us: Timeout in microseconds for the echo signal.
        :return: Distance in centimeters or None if timeout occurs.
        """


class WS2812Matrix:
    def __init__(self, pin_sm_pairs:list[tuple[int,int]], panel_w:int, panel_h:int, grid_w:int,  grid_h:int, *, zigzag:bool=True, origin:str='top_left', brightness:float=0.25):
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

    def deinit(self):
        """
        Deinitialize the WS2812 matrix controller.
        This method clears the buffers, stops the state machines, and resets the pins.
        """

    @property
    def display_w(self) -> int:
        """
        Get the width of the display in pixels.
        
        :return: Width of the display in pixels
        """

    @property
    def display_h(self) -> int:
        """
        Get the height of the display in pixels.
        
        :return: Height of the display in pixels
        """

    @property
    def brightness(self) -> float:
        """
        Get the current brightness level of the matrix.
        The brightness level is a float value between 0.0 (off) and 1.0 (full brightness).
        
        :return: Brightness level (float)
        """

    @brightness.setter
    def brightness(self, value:float):
        """
        Set the brightness level of the matrix.
        The brightness level should be a float value between 0.0 (off) and 1.0 (full brightness).
        
        :param value: Brightness level (float)
        :raises ValueError: If the brightness value is not between 0.0 and 1.0.
        """

    def __setitem__(self, pos:tuple[int,int], color:tuple[int,int,int]):
        """
        Set the color of a pixel at the specified position.
        The color should be a tuple of three integers representing the RGB values (0-255).
        
        :param pos: Tuple of (x, y) coordinates of the pixel
        :param color: Tuple of (R, G, B) color values
        :raises IndexError: If the pixel coordinates are out of range.
        """

    def __getitem__(self, pos) -> tuple[int,int,int]:
        """
        Get the color of a pixel at the specified position.
        The color is returned as a tuple of three integers representing the RGB values (0-255).
        
        :param pos: Tuple of (x, y) coordinates of the pixel
        :return: Tuple of (R, G, B) color values
        :raises IndexError: If the pixel coordinates are out of range.
        """

    def fill(self, color:tuple[int,int,int]):
        """
        Fill the entire display with the specified color.
        The color should be a tuple of three integers representing the RGB values (0-255).
        
        :param color: Tuple of (R, G, B) color values
        :raises ValueError: If the color values are not in the range 0-255.
        """

    def clear(self):
        """
        Clear the display by filling it with black (0, 0, 0).
        This method sets all pixels to black and updates the display.
        """
        
    def update(self):
        """
        Update the display by sending the pixel data to the state machines.
        This method processes the pixel data in the buffers and sends it to the WS2812 panels.
        """

    def draw_line(self, x0:int, y0:int, x1:int, y1:int, color:tuple[int,int,int]):
        """
        Draw a line on the display from (x0, y0) to (x1, y1) with the specified color.
        
        :param x0: Starting x-coordinate of the line
        :param y0: Starting y-coordinate of the line
        :param x1: Ending x-coordinate of the line
        :param y1: Ending y-coordinate of the line
        :param color: Tuple of (R, G, B) color values
        """

    def draw_rect(self, x:int, y:int, w:int, h:int, color:tuple[int,int,int]):
        """
        Draw a rectangle on the display with the specified position, width, height, and color.
        
        :param x: x-coordinate of the top-left corner of the rectangle
        :param y: y-coordinate of the top-left corner of the rectangle
        :param w: Width of the rectangle
        :param h: Height of the rectangle
        :param color: Tuple of (R, G, B) color values
        """

    def draw_circle(self, cx:int, cy:int, r:int, color:tuple[int,int,int]):
        """
        Draw a circle on the display with the specified center, radius, and color.
        
        :param cx: x-coordinate of the center of the circle
        :param cy: y-coordinate of the center of the circle
        :param r: Radius of the circle
        :param color: Tuple of (R, G, B) color values
        """

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


class tLed:
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    YELLOW = (255, 255, 0)
    CYAN = (0, 255, 255)
    MAGENTA = (255, 0, 255)
    WHITE = (255, 255, 255)

    def __init__(self, bright:float=1.0):
        """
        Basic WS2812 control class built into TiCLE.
        This class provides methods to turn on the LED with a specified color,
        turn it off, and define some common colors.
        """
                
    def on(self, color:tuple[int,int,int]=RED):
        """
        Turn on the LED with the specified color.

        :param color: Tuple of (R, G, B) color values (default is red).
        """

    def off(self):
        """
        Turn off the LED by filling it with black (0, 0, 0).
        """
        
    @property
    def brightness(self) -> float:
        """
        Get the current brightness level of the matrix.
        The brightness level is a float value between 0.0 (off) and 1.0 (full brightness).
        
        :return: Brightness level (float)
        """

    @brightness.setter
    def brightness(self, value:float):
        """
        Set the brightness level of the matrix.
        The brightness level should be a float value between 0.0 (off) and 1.0 (full brightness).
        
        :param value: Brightness level (float)
        :raises ValueError: If the brightness value is not between 0.0 and 1.0.
        """


