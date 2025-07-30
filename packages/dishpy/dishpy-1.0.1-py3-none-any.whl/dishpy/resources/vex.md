<a id="vex"></a>

# vex

<a id="vex.Ports"></a>

## Ports Objects

```python
class Ports()
```

Smartport definitions

<a id="vex.vexEnum"></a>

## vexEnum Objects

```python
class vexEnum()
```

Base class for all enumerated types

<a id="vex.PercentUnits"></a>

## PercentUnits Objects

```python
class PercentUnits()
```

The measurement units for percentage values.

<a id="vex.PercentUnits.PERCENT"></a>

#### PERCENT

A percentage unit that represents a value from 0% to 100%

<a id="vex.TimeUnits"></a>

## TimeUnits Objects

```python
class TimeUnits()
```

The measurement units for time values.

<a id="vex.TimeUnits.SECONDS"></a>

#### SECONDS

A time unit that is measured in seconds.

<a id="vex.TimeUnits.SEC"></a>

#### SEC

A time unit that is measured in seconds.

<a id="vex.TimeUnits.MSEC"></a>

#### MSEC

A time unit that is measured in milliseconds.

<a id="vex.CurrentUnits"></a>

## CurrentUnits Objects

```python
class CurrentUnits()
```

The measurement units for current values.

<a id="vex.CurrentUnits.AMP"></a>

#### AMP

A current unit that is measured in amps.

<a id="vex.VoltageUnits"></a>

## VoltageUnits Objects

```python
class VoltageUnits()
```

The measurement units for voltage values.

<a id="vex.VoltageUnits.VOLT"></a>

#### VOLT

A voltage unit that is measured in volts.

<a id="vex.VoltageUnits.MV"></a>

#### MV

A voltage unit that is measured in millivolts.

<a id="vex.PowerUnits"></a>

## PowerUnits Objects

```python
class PowerUnits()
```

The measurement units for power values.

<a id="vex.PowerUnits.WATT"></a>

#### WATT

A power unit that is measured in watts.

<a id="vex.TorqueUnits"></a>

## TorqueUnits Objects

```python
class TorqueUnits()
```

The measurement units for torque values.

<a id="vex.TorqueUnits.NM"></a>

#### NM

A torque unit that is measured in Newton Meters.

<a id="vex.TorqueUnits.INLB"></a>

#### INLB

A torque unit that is measured in Inch Pounds.

<a id="vex.RotationUnits"></a>

## RotationUnits Objects

```python
class RotationUnits()
```

The measurement units for rotation values.

<a id="vex.RotationUnits.DEG"></a>

#### DEG

A rotation unit that is measured in degrees.

<a id="vex.RotationUnits.REV"></a>

#### REV

A rotation unit that is measured in revolutions.

<a id="vex.RotationUnits.RAW"></a>

#### RAW

A rotation unit that is measured in raw data form.

<a id="vex.VelocityUnits"></a>

## VelocityUnits Objects

```python
class VelocityUnits()
```

The measurement units for velocity values.

<a id="vex.VelocityUnits.PERCENT"></a>

#### PERCENT

A velocity unit that is measured in percentage.

<a id="vex.VelocityUnits.RPM"></a>

#### RPM

A velocity unit that is measured in rotations per minute.

<a id="vex.VelocityUnits.DPS"></a>

#### DPS

A velocity unit that is measured in degrees per second.

<a id="vex.DistanceUnits"></a>

## DistanceUnits Objects

```python
class DistanceUnits()
```

The measurement units for distance values.

<a id="vex.DistanceUnits.MM"></a>

#### MM

A distance unit that is measured in millimeters.

<a id="vex.DistanceUnits.IN"></a>

#### IN

A distance unit that is measured in inches.

<a id="vex.DistanceUnits.CM"></a>

#### CM

A distance unit that is measured in centimeters.

<a id="vex.AnalogUnits"></a>

## AnalogUnits Objects

```python
class AnalogUnits()
```

The measurement units for analog values.

<a id="vex.AnalogUnits.PCT"></a>

#### PCT

An analog unit that is measured in percentage.

<a id="vex.AnalogUnits.EIGHTBIT"></a>

#### EIGHTBIT

An analog unit that is measured in an 8-bit analog value
(a value with 256 possible states).

<a id="vex.AnalogUnits.TENBIT"></a>

#### TENBIT

An analog unit that is measured in an 10-bit analog value
(a value with 1024 possible states).

<a id="vex.AnalogUnits.TWELVEBIT"></a>

#### TWELVEBIT

An analog unit that is measured in an 12-bit analog value
(a value with 4096 possible states).

<a id="vex.AnalogUnits.MV"></a>

#### MV

An analog unit that is measured in millivolts.

<a id="vex.TemperatureUnits"></a>

## TemperatureUnits Objects

```python
class TemperatureUnits()
```

The measurement units for temperature values.

<a id="vex.TemperatureUnits.CELSIUS"></a>

#### CELSIUS

A temperature unit that is measured in celsius.

<a id="vex.TemperatureUnits.FAHRENHEIT"></a>

#### FAHRENHEIT

A temperature unit that is measured in fahrenheit.

<a id="vex.DirectionType"></a>

## DirectionType Objects

```python
class DirectionType()
```

The defined units for direction values.

<a id="vex.DirectionType.FORWARD"></a>

#### FORWARD

A direction unit that is defined as forward.

<a id="vex.DirectionType.REVERSE"></a>

#### REVERSE

A direction unit that is defined as backward.

<a id="vex.DirectionType.UNDEFINED"></a>

#### UNDEFINED

A direction unit used when direction is not known.

<a id="vex.TurnType"></a>

## TurnType Objects

```python
class TurnType(vexEnum)
```

The defined units for turn values.

<a id="vex.TurnType.LEFT"></a>

#### LEFT

A turn unit that is defined as left turning.

<a id="vex.TurnType.RIGHT"></a>

#### RIGHT

A turn unit that is defined as right turning.

<a id="vex.TurnType.UNDEFINED"></a>

#### UNDEFINED

A turn unit unit used when direction is not known.

<a id="vex.BrakeType"></a>

## BrakeType Objects

```python
class BrakeType()
```

The defined units for motor brake values.

<a id="vex.BrakeType.COAST"></a>

#### COAST

A brake unit that is defined as motor coast.

<a id="vex.BrakeType.BRAKE"></a>

#### BRAKE

A brake unit that is defined as motor brake.

<a id="vex.BrakeType.HOLD"></a>

#### HOLD

A brake unit that is defined as motor hold.

<a id="vex.GearSetting"></a>

## GearSetting Objects

```python
class GearSetting()
```

The defined units for gear values.

<a id="vex.GearSetting.RATIO_36_1"></a>

#### RATIO\_36\_1

A gear unit that is defined as the red 36:1 gear cartridge used in
V5 Smart Motors.

<a id="vex.GearSetting.RATIO_18_1"></a>

#### RATIO\_18\_1

A gear unit that is defined as the green 18:1 gear cartridge used in
V5 Smart Motors.

<a id="vex.GearSetting.RATIO_6_1"></a>

#### RATIO\_6\_1

A gear unit that is defined as the blue 6:1 gear cartridge used in
V5 Smart Motors.

<a id="vex.FontType"></a>

## FontType Objects

```python
class FontType()
```

A unit representing font type and size

<a id="vex.FontType.MONO20"></a>

#### MONO20

monotype font of size 20

<a id="vex.FontType.MONO30"></a>

#### MONO30

monotype font of size 30

<a id="vex.FontType.MONO40"></a>

#### MONO40

monotype font of size 40

<a id="vex.FontType.MONO60"></a>

#### MONO60

monotype font of size 60

<a id="vex.FontType.PROP20"></a>

#### PROP20

proportional font of size 20

<a id="vex.FontType.PROP30"></a>

#### PROP30

proportional font of size 30

<a id="vex.FontType.PROP40"></a>

#### PROP40

proportional font of size 40

<a id="vex.FontType.PROP60"></a>

#### PROP60

proportional font of size 60

<a id="vex.FontType.MONO15"></a>

#### MONO15

proportional font of size 15

<a id="vex.FontType.MONO12"></a>

#### MONO12

proportional font of size 12

<a id="vex.FontType.CJK16"></a>

#### CJK16

Chinese/Japanese/Korean font of size 16

<a id="vex.ThreeWireType"></a>

## ThreeWireType Objects

```python
class ThreeWireType()
```

The defined units for 3-wire devices.

<a id="vex.ThreeWireType.ANALOG_IN"></a>

#### ANALOG\_IN

A 3-wire sensor that is defined as an analog input.

<a id="vex.ThreeWireType.ANALOG_OUT"></a>

#### ANALOG\_OUT

A 3-wire sensor that is defined as an analog output.

<a id="vex.ThreeWireType.DIGITAL_IN"></a>

#### DIGITAL\_IN

A 3-wire sensor that is defined as an digital input.

<a id="vex.ThreeWireType.DIGITAL_OUT"></a>

#### DIGITAL\_OUT

A 3-wire sensor that is defined as an digital output.

<a id="vex.ThreeWireType.SWITCH"></a>

#### SWITCH

A 3-wire sensor that is defined as a switch.

<a id="vex.ThreeWireType.POTENTIOMETER"></a>

#### POTENTIOMETER

A 3-wire sensor that is defined as a potentiometer.

<a id="vex.ThreeWireType.LINE_SENSOR"></a>

#### LINE\_SENSOR

A 3-wire sensor that is defined as a line sensor.

<a id="vex.ThreeWireType.LIGHT_SENSOR"></a>

#### LIGHT\_SENSOR

A 3-wire sensor that is defined as a light sensor.

<a id="vex.ThreeWireType.GYRO"></a>

#### GYRO

A 3-wire sensor that is defined as a yaw rate gyro.

<a id="vex.ThreeWireType.ACCELEROMETER"></a>

#### ACCELEROMETER

A 3-wire sensor that is defined as a accelerometer.

<a id="vex.ThreeWireType.MOTOR"></a>

#### MOTOR

A 3-wire sensor that is defined as a legacy vex motor.

<a id="vex.ThreeWireType.SERVO"></a>

#### SERVO

A 3-wire sensor that is defined as a legacy vex servo.

<a id="vex.ThreeWireType.ENCODER"></a>

#### ENCODER

A 3-wire sensor that is defined as a quadrature encoder.

<a id="vex.ThreeWireType.SONAR"></a>

#### SONAR

A 3-wire sensor that is defined as an ultrasonic sensor (sonar)

<a id="vex.ThreeWireType.SLEW_MOTOR"></a>

#### SLEW\_MOTOR

A 3-wire sensor that is defined as a legacy vex motor using slew rate control.

<a id="vex.ControllerType"></a>

## ControllerType Objects

```python
class ControllerType()
```

The defined types for controller devices.

<a id="vex.ControllerType.PRIMARY"></a>

#### PRIMARY

A controller defined as a primary controller.

<a id="vex.ControllerType.PARTNER"></a>

#### PARTNER

A controller defined as a partner controller.

<a id="vex.AxisType"></a>

## AxisType Objects

```python
class AxisType()
```

The defined units for inertial sensor axis.

<a id="vex.AxisType.XAXIS"></a>

#### XAXIS

The X axis of the Inertial sensor.

<a id="vex.AxisType.YAXIS"></a>

#### YAXIS

The Y axis of the Inertial sensor.

<a id="vex.AxisType.ZAXIS"></a>

#### ZAXIS

The Z axis of the Inertial sensor.

<a id="vex.OrientationType"></a>

## OrientationType Objects

```python
class OrientationType()
```

The defined units for inertial sensor orientation.

<a id="vex.OrientationType.ROLL"></a>

#### ROLL

roll, orientation around the X axis of the Inertial sensor.

<a id="vex.OrientationType.PITCH"></a>

#### PITCH

pitch, orientation around the Y axis of the Inertial sensor.

<a id="vex.OrientationType.YAW"></a>

#### YAW

yaw, orientation around the Z axis of the Inertial sensor.

<a id="vex.ObjectSizeType"></a>

## ObjectSizeType Objects

```python
class ObjectSizeType()
```

The defined units for distance sensor object size.

<a id="vex.LedStateType"></a>

## LedStateType Objects

```python
class LedStateType()
```

The defined units for optical sensor led state.

<a id="vex.GestureType"></a>

## GestureType Objects

```python
class GestureType()
```

The defined units for optical sensor gesture types.

<a id="vex.VexlinkType"></a>

## VexlinkType Objects

```python
class VexlinkType()
```

The defined units for vexlink types.

<a id="vex.VexlinkType.MANAGER"></a>

#### MANAGER

A vexlink type that is defined as the manager radio.

<a id="vex.VexlinkType.WORKER"></a>

#### WORKER

A vexlink type that is defined as the worker radio.

<a id="vex.VexlinkType.GENERIC"></a>

#### GENERIC

A vexlink type that is defined as a raw unmanaged link.

<a id="vex.PERCENT"></a>

#### PERCENT

A percentage unit that represents a value from 0% to 100%

<a id="vex.FORWARD"></a>

#### FORWARD

A direction unit that is defined as forward.

<a id="vex.REVERSE"></a>

#### REVERSE

A direction unit that is defined as backward.

<a id="vex.LEFT"></a>

#### LEFT

A turn unit that is defined as left turning.

<a id="vex.RIGHT"></a>

#### RIGHT

A turn unit that is defined as right turning.

<a id="vex.DEGREES"></a>

#### DEGREES

A rotation unit that is measured in degrees.

<a id="vex.TURNS"></a>

#### TURNS

A rotation unit that is measured in revolutions.

<a id="vex.RPM"></a>

#### RPM

A velocity unit that is measured in rotations per minute.

<a id="vex.DPS"></a>

#### DPS

A velocity unit that is measured in degrees per second.

<a id="vex.SECONDS"></a>

#### SECONDS

A time unit that is measured in seconds.

<a id="vex.MSEC"></a>

#### MSEC

A time unit that is measured in milliseconds.

<a id="vex.INCHES"></a>

#### INCHES

A distance unit that is measured in inches.

<a id="vex.MM"></a>

#### MM

A distance unit that is measured in millimeters.

<a id="vex.XAXIS"></a>

#### XAXIS

The X axis of the Inertial sensor.

<a id="vex.YAXIS"></a>

#### YAXIS

The Y axis of the Inertial sensor.

<a id="vex.ZAXIS"></a>

#### ZAXIS

The Z axis of the Inertial sensor.

<a id="vex.ROLL"></a>

#### ROLL

roll, orientation around the X axis of the Inertial sensor.

<a id="vex.PITCH"></a>

#### PITCH

pitch, orientation around the Y axis of the Inertial sensor.

<a id="vex.YAW"></a>

#### YAW

yaw, orientation around the Z axis of the Inertial sensor.

<a id="vex.PRIMARY"></a>

#### PRIMARY

A controller defined as a primary controller.

<a id="vex.PARTNER"></a>

#### PARTNER

A controller defined as a partner controller.

<a id="vex.COAST"></a>

#### COAST

A brake unit that is defined as motor coast.

<a id="vex.BRAKE"></a>

#### BRAKE

A brake unit that is defined as motor brake.

<a id="vex.HOLD"></a>

#### HOLD

A brake unit that is defined as motor hold.

<a id="vex.VOLT"></a>

#### VOLT

A voltage unit that is measured in volts.

<a id="vex.MV"></a>

#### MV

A voltage unit that is measured in millivolts.

<a id="vex.info"></a>

#### info

```python
def info()
```

### return a string with VEX Python version information

<a id="vex.sleep"></a>

#### sleep

```python
def sleep(duration: vexnumber, units=TimeUnits.MSEC)
```

### delay the current thread for the provided number of seconds or milliseconds.

#### Arguments:
duration: The number of seconds or milliseconds to sleep for
units:    The units of duration, optional, default is milliseconds

#### Returns:
None

<a id="vex.wait"></a>

#### wait

```python
def wait(duration: vexnumber, units=TimeUnits.MSEC)
```

### delay the current thread for the provided number of seconds or milliseconds.

#### Arguments:
duration: The number of seconds or milliseconds to sleep for
units:    The units of duration, optional, default is milliseconds

#### Returns:
None

<a id="vex.on_screen_errors"></a>

#### on\_screen\_errors

```python
def on_screen_errors(value: int)
```

### enable or disable the display of brain on screen errors

#### Arguments:
value : True or False

#### Returns:
None

<a id="vex.clear_errors"></a>

#### clear\_errors

```python
def clear_errors()
```

### clear any brain on screen errors

#### Arguments:
None

#### Returns:
None

<a id="vex.Color"></a>

## Color Objects

```python
class Color()
```

### Color class - create a new color

This class is used to create instances of color objects

#### Arguments:
value : The color value, can be specified in various ways, see examples.

#### Returns:
An instance of the Color class

#### Examples:
# create blue using hex value\
c = Color(0x0000ff)

# create blue using r, g, b values\
c = Color(0, 0, 255)

# create blue using web string\
c = Color("`00F`")

# create blue using web string (alternate)\
c = Color("`0000FF`")

# create red using an existing object\
c = Color(Color.RED)

<a id="vex.Color.BLACK"></a>

#### BLACK

predefined Color black

<a id="vex.Color.WHITE"></a>

#### WHITE

predefined Color white

<a id="vex.Color.RED"></a>

#### RED

predefined Color red

<a id="vex.Color.GREEN"></a>

#### GREEN

predefined Color green

<a id="vex.Color.BLUE"></a>

#### BLUE

predefined Color blue

<a id="vex.Color.YELLOW"></a>

#### YELLOW

predefined Color yellow

<a id="vex.Color.ORANGE"></a>

#### ORANGE

predefined Color orange

<a id="vex.Color.PURPLE"></a>

#### PURPLE

predefined Color purple

<a id="vex.Color.CYAN"></a>

#### CYAN

predefined Color cyan

<a id="vex.Color.TRANSPARENT"></a>

#### TRANSPARENT

predefined Color transparent

<a id="vex.Color.rgb"></a>

#### rgb

```python
def rgb(*args)
```

### change existing Color instance to new rgb value

#### Arguments:
value : The color value, can be specified in various ways, see examples.

#### Returns:
integer value representing the color

#### Examples:
# create a color that is red
c = Color(0xFF0000)
# change color to blue using single value
c.rgb(0x0000FF)
# change color to green using three values
c.rgb(0, 255, 0)

<a id="vex.Color.hsv"></a>

#### hsv

```python
def hsv(hue: vexnumber, saturation: vexnumber, value: vexnumber)
```

### change existing Color instance using hsv

#### Arguments:
hue : The hue of the color
saturation : The saturation of the color
value : The brightness of the color

#### Returns:
integer value representing the color

#### Examples:
# create a color that is red
c.hsv( 0, 1.0, 1.0)

<a id="vex.Color.web"></a>

#### web

```python
def web(value: str)
```

### change existing Color instance using web string

#### Arguments:
value : The new color as a web string

#### Returns:
integer value representing the color

#### Examples:
# create a color that is red
c.web('`F00`')

<a id="vex.Color.is_transparent"></a>

#### is\_transparent

```python
def is_transparent()
```

### return whether color is transparent or not

#### Arguments:
None

#### Returns:
True or False

#### Examples:

<a id="vex.Brain"></a>

## Brain Objects

```python
class Brain()
```

### Brain class

The Brain class creates a number of instances of internal classes that allow access\
to the screen, battery, 3wire ports and sd card on the V5 brain.

#### Arguments:
None

#### Returns:
An instance of the Brain class

#### Examples:
brain = Brain()

<a id="vex.Brain.Lcd"></a>

## Lcd Objects

```python
class Lcd()
```

### Brain.Lcd class

A class used to access to screen on the V5 for drawing and receiving touch events.

#### Arguments:
None

#### Returns:
An instance of the Brain.Lcd class

<a id="vex.Brain.Lcd.set_cursor"></a>

#### set\_cursor

```python
def set_cursor(row: vexnumber, col: vexnumber)
```

### Set the cursor position used for printing text on the screen

row and column spacing will take into account the selected font.\
The base cell size if 10x20 pixels for the MONO20 font.\
text may not accurately print if using a proportional font.\
The top, left corner of the screen is position 1,1

#### Arguments:
row : The cursor row
col : The cursor column

#### Returns:
None

<a id="vex.Brain.Lcd.column"></a>

#### column

```python
def column()
```

Return the current column where text will be printed

<a id="vex.Brain.Lcd.row"></a>

#### row

```python
def row()
```

Return the current row where text will be printed

<a id="vex.Brain.Lcd.set_origin"></a>

#### set\_origin

```python
def set_origin(x: vexnumber, y: vexnumber)
```

### Set the origin used for drawing graphics on the screen

drawing functions consider the top left corner of the screen as the origin.\
This function can move the origin to an alternate position such as the center of the screen.

#### Arguments:
x : The origins x position relative to top left corner
y : The origins y position relative to top left corner

#### Returns:
None

<a id="vex.Brain.Lcd.set_font"></a>

#### set\_font

```python
def set_font(fontname: FontType.FontType)
```

### Set the font type used for printing text on the screen

#### Arguments:
fontname : The font name

#### Returns:
None

#### Examples:
brain.screen.font_type(FontType.MONO40)

<a id="vex.Brain.Lcd.set_pen_width"></a>

#### set\_pen\_width

```python
def set_pen_width(width: vexnumber)
```

### Set the pen width used for drawing lines, rectangles and circles

#### Arguments:
width : The pen width

#### Returns:
None

<a id="vex.Brain.Lcd.set_pen_color"></a>

#### set\_pen\_color

```python
def set_pen_color(color)
```

### Set the pen color used for drawing lines, rectangles and circles

The color can be passed in similar ways to the Color class.\
The color is specific to the running thread.

#### Arguments:
color : The pen color

#### Returns:
None

#### Examples:
# set pen color red using a hex value\
brain.screen.set_pen_color(0xFF0000)

# set pen color blue using predefined color\
brain.screen.set_pen_color(Color.BLUE)

# set pen color green using web string\
brain.screen.set_pen_color("`00FF00`")

<a id="vex.Brain.Lcd.set_fill_color"></a>

#### set\_fill\_color

```python
def set_fill_color(color)
```

### Set the fill color used for drawing rectangles and circles

The color can be passed in similar ways to the Color class.\
The color is specific to the running thread.

#### Arguments:
color : The fill color

#### Returns:
None

#### Examples:
# set pen color red using a hex value\
brain.screen.set_fill_color(0xFF0000)

# set pen color blue using predefined color\
brain.screen.set_fill_color(Color.BLUE)

# set pen color green using web string\
brain.screen.set_fill_color("`00FF00`")

<a id="vex.Brain.Lcd.clear_screen"></a>

#### clear\_screen

```python
def clear_screen(color=Color.BLACK)
```

### Clear the whole screen to a single color

The color can be passed in similar ways to the Color class.\

#### Arguments:
color (optional) : The color the screen will be set to, default is BLACK

#### Returns:
None

#### Examples:
# clear screen to black\
brain.screen.clear_screen()

# clear screen to blue using predefined color\
brain.screen.clear_screen(Color.BLUE)

<a id="vex.Brain.Lcd.clear_row"></a>

#### clear\_row

```python
def clear_row(number=None, color=Color.BLACK)
```

### Clear screen row to a single color

The color can be passed in similar ways to the Color class.\

#### Arguments:
row (optional) : The row to clear, default is current cursor row
color (optional) : The color the screen will be set to, default is BLACK

#### Returns:
None

#### Examples:
# clear row to black\
brain.screen.clear_row()

# clear row 2 to red\
brain.screen.clear_row(2, Color.RED)

<a id="vex.Brain.Lcd.next_row"></a>

#### next\_row

```python
def next_row()
```

### Move the cursor to the beginning of the next row

#### Arguments:
None

#### Returns:
None

<a id="vex.Brain.Lcd.draw_pixel"></a>

#### draw\_pixel

```python
def draw_pixel(x: vexnumber, y: vexnumber)
```

### Draw a pixel on the screen using the current pen color.

#### Arguments:
x : The x position to draw the pixel referenced to the screen origin.
y : The y position to draw the pixel referenced to the screen origin.

#### Returns:
None

#### Examples:
# draw a red pixel on the screen\
brain.screen.set_pen_color(Color.RED)\
brain.screen.draw_pixel(10, 10)

<a id="vex.Brain.Lcd.draw_line"></a>

#### draw\_line

```python
def draw_line(x1: vexnumber, y1: vexnumber, x2: vexnumber, y2: vexnumber)
```

### Draw a line on the screen using the current pen color.

#### Arguments:
x1 : The x position of the beginning of the line referenced to the screen origin.
y1 : The y position of the beginning of the line referenced to the screen origin.
x2 : The x position of the end of the line referenced to the screen origin.
y2 : The y position of the end of the line referenced to the screen origin.

#### Returns:
None

#### Examples:
# draw a red line on the screen\
brain.screen.set_pen_color(Color.RED)\
brain.screen.draw_line(10, 10, 20, 20)

<a id="vex.Brain.Lcd.draw_rectangle"></a>

#### draw\_rectangle

```python
def draw_rectangle(x: vexnumber,
                   y: vexnumber,
                   width: vexnumber,
                   height: vexnumber,
                   color: Any = None)
```

### Draw a rectangle on the screen using the current pen and fill colors.

#### Arguments:
x : The x position of the rectangle top/left corner referenced to the screen origin.
y : The y position of the rectangle top/left corner referenced to the screen origin.
width : The width of the rectangle.
height : The height of the rectangle.
color (optional) : An optional fill color, the current fill color will be used if not supplied

#### Returns:
None

#### Examples:
# draw a green rectangle on the screen that is filled using blue\
brain.screen.set_pen_color(Color.GREEN)\
brain.screen.set_fill_color(Color.BLUE)\
brain.screen.draw_rectangle(10, 10, 20, 20)

# draw a green rectangle on the screen that is filled using red\
brain.screen.set_pen_color(Color.GREEN)\
brain.screen.draw_rectangle(50, 50, 20, 20, Color.RED)

<a id="vex.Brain.Lcd.draw_circle"></a>

#### draw\_circle

```python
def draw_circle(x: vexnumber,
                y: vexnumber,
                radius: vexnumber,
                color: Any = None)
```

### Draw a circle on the screen using the current pen and fill colors.

#### Arguments:
x : The x position of the circle center referenced to the screen origin.
y : The y position of the circle center referenced to the screen origin.
radius : The height of the circle.
color (optional) : An optional fill color, the current fill color will be used if not supplied

#### Returns:
None

#### Examples:
# draw a green circle on the screen that is filled using blue\
brain.screen.set_pen_color(Color.GREEN)\
brain.screen.set_fill_color(Color.BLUE)\
brain.screen.draw_circle(50, 50, 10)

# draw a green circle on the screen that is filled using red\
brain.screen.set_pen_color(Color.GREEN)\
brain.screen.draw_circle(100, 50, 10, Color.RED)

<a id="vex.Brain.Lcd.get_string_width"></a>

#### get\_string\_width

```python
def get_string_width(*args)
```

### get width of a string

#### Arguments:
arguments are in the same format as can be passed to the print function.

#### Returns:
width of string as integer.

<a id="vex.Brain.Lcd.get_string_height"></a>

#### get\_string\_height

```python
def get_string_height(*args)
```

### get height of a string

#### Arguments:
arguments are in the same format as can be passed to the print function.

#### Returns:
height of string as integer.

<a id="vex.Brain.Lcd.print"></a>

#### print

```python
def print(*args, **kwargs)
```

### print text on the screen using current curser position.

#### Arguments:
Optional keyword arguments:
sep : string inserted between values, default a space.
precision : the number of decimal places to display when printing simple numbers, default is 2

#### Returns:
None

#### Examples:
# print the number 1 on the screen at current cursor position\
brain.screen.print(1)

# print the numbers 1, 2, 3 and 4 on the screen at current cursor position separated by a '-'\
brain.screen.print(1, 2, 3, 4, sep='-')

# print motor1 velocity on the screen using a format string\
brain.screen.print("motor  1 : % 7.2f" %(motor1.velocity()))

<a id="vex.Brain.Lcd.print_at"></a>

#### print\_at

```python
def print_at(*args, **kwargs)
```

### print text on the screen at x and coordinates.

#### Arguments:
Required keyword arguments
x : The x position of the text referenced to the screen origin.
y : The y position of the text referenced to the screen origin.

Optional keyword arguments:
sep : string inserted between values, default a space.
precision : the number of decimal places to display when printing simple numbers, default is 2
opaque : text does not clear background pixels if set to False. default is True.

#### Returns:
None

#### Examples:
# print the number 1 on the screen at position x=100, y=40\
brain.screen.print_at(1, x=100, y=40)

# print the numbers 1, 2, 3 and 4 on the screen at position x=100, y=40\
brain.screen.print_at(1, 2, 3, 4, x=100, y=40)

# print motor1 velocity on the screen using a format string at position x=100, y=40\
brain.screen.print_at("motor  1 : % 7.2f" %(motor1.velocity()), x=100, y=40)

<a id="vex.Brain.Lcd.pressed"></a>

#### pressed

```python
def pressed(callback: Callable[..., None], arg: tuple = ())
```

### Register a function to be called when the screen is pressed

#### Arguments:
callback : A function that will be called when the screen is pressed
arg (optional) : A tuple that is used to pass arguments to the callback function.

#### Returns:
An instance of the Event class

#### Examples:
def foo():
print("screen pressed")

brain.screen.pressed(foo)

<a id="vex.Brain.Lcd.released"></a>

#### released

```python
def released(callback: Callable[..., None], arg: tuple = ())
```

### Register a function to be called when the screen is released (touch removed)

#### Arguments:
callback : A function that will be called when the screen is released
arg (optional) : A tuple that is used to pass arguments to the callback function.

#### Returns:
An instance of the Event class

#### Examples:
def foo():
print("screen released")

brain.screen.released(foo)

<a id="vex.Brain.Lcd.x_position"></a>

#### x\_position

```python
def x_position()
```

### The X coordinate of the last screen event, press or release

#### Arguments:
None

#### Returns:
The X coordinate as an int

#### Examples:
def foo():
print("screen pressed at ", brain.screen.x_position())

brain.screen.pressed(foo)

<a id="vex.Brain.Lcd.y_position"></a>

#### y\_position

```python
def y_position()
```

### The Y coordinate of the last screen event, press or release

#### Arguments:
None

#### Returns:
The Y coordinate as an int

#### Examples:
def foo():
print("screen pressed at ", brain.screen.y_position())

brain.screen.pressed(foo)

<a id="vex.Brain.Lcd.pressing"></a>

#### pressing

```python
def pressing()
```

### Returns whether the screen is currently being pressed (touched)

#### Arguments:
None

#### Returns:
True or False

<a id="vex.Brain.Lcd.draw_image_from_file"></a>

#### draw\_image\_from\_file

```python
def draw_image_from_file(filename: str, x: vexnumber, y: vexnumber)
```

### Display the named image from the SD Card

#### Arguments:
filename : The file name of the image.
x : The X coordinate for the top left corner of the image on the screen
y : The Y coordinate for the top left corner of the image on the screen

#### Returns:
True if successfully drawn, False on error

#### Examples:
# draw the vex.bmp image on the screen at coordinate 0, 0\
# an image named vex.bmp must be on the SD Card in the root folder\
brain.screen.draw_image_from_file('vex.bmp', 0, 0)

<a id="vex.Brain.Lcd.render"></a>

#### render

```python
def render()
```

### Switch drawing to double buffered and render too screen.

Once called, further drawing will not appear on the screen until the next time\
render is called.  This function will block until the screen can be updated.

#### Arguments:
None

#### Returns:
True if buffer was successfully rendered to screen.

#### Examples:

<a id="vex.Brain.Lcd.set_clip_region"></a>

#### set\_clip\_region

```python
def set_clip_region(x: vexnumber, y: vexnumber, width: vexnumber,
                    height: vexnumber)
```

### Sets the clip region for drawing to the supplied rectangle.

All drawing is clipped to the given rectangle.\
This is set on a per thread basis.

#### Arguments:
x : The x position of the rectangle top/left corner referenced to the screen origin.
y : The y position of the rectangle top/left corner referenced to the screen origin.
width : The width of the rectangle.
height : The height of the rectangle.

#### Returns:
None

#### Examples:

<a id="vex.Brain.Battery"></a>

## Battery Objects

```python
class Battery()
```

### Battery class - access the brain battery

#### Arguments:
None

#### Returns:
Instance of Battery class

#### Examples:

<a id="vex.Brain.Battery.capacity"></a>

#### capacity

```python
def capacity()
```

### read remaining capacity of the battery

#### Arguments:
None

#### Returns:
capacity as percentage

#### Examples:

<a id="vex.Brain.Battery.temperature"></a>

#### temperature

```python
def temperature(units: TemperaturePercentUnits = PercentUnits.PERCENT)
```

### read the temperature of the battery

#### Arguments:
units (optional) : PERCENT, CELSIUS or FAHRENHEIT, default is CELSIUS

#### Returns:
temperature in supplied units

#### Examples:

<a id="vex.Brain.Battery.voltage"></a>

#### voltage

```python
def voltage(units=VoltageUnits.MV)
```

### read the voltage of the battery

#### Arguments:
units (optional) : VOLTS or MV, default is MV

#### Returns:
voltage in supplied units

#### Examples:

<a id="vex.Brain.Battery.current"></a>

#### current

```python
def current(units=CurrentUnits.AMP)
```

### read the current of the battery

#### Arguments:
units (optional) : AMP, default is mA but jot available as an enum.

#### Returns:
current in supplied units

#### Examples:

<a id="vex.Brain.Sdcard"></a>

## Sdcard Objects

```python
class Sdcard()
```

### Sdcard class - access the brain sdcard

#### Arguments:
None

#### Returns:
Instance of Sdcard class

#### Examples:

<a id="vex.Brain.Sdcard.is_inserted"></a>

#### is\_inserted

```python
def is_inserted()
```

### returns status of SD Card

#### Arguments:
None

#### Returns:
True if an sdcard is inserted into the brain

#### Examples:

<a id="vex.Brain.Sdcard.filesize"></a>

#### filesize

```python
def filesize(filename: str)
```

### returns the size in bytes of the named file

#### Arguments:
filename : The name of the file to check

#### Returns:
size of file in bytes

#### Examples:

<a id="vex.Brain.Sdcard.loadfile"></a>

#### loadfile

```python
def loadfile(filename: str, *args)
```

### load the named file

#### Arguments:
filename : The name of the file to read
buffer (optional) : A bytearray to read the file into

#### Returns:
A bytearray with file data

#### Examples:
# read file into new bytearray\
b = brain.sdcard.loadfile('MyTextFile.txt')

<a id="vex.Brain.Sdcard.savefile"></a>

#### savefile

```python
def savefile(filename: str, *args)
```

### Save a bytearray into a named file

If the optional bytearray is None, then an empty file is created.

#### Arguments:
filename : The name of the file to write
buffer (optional) : A bytearray to write into the file

#### Returns:
The number of bytes written

#### Examples:
# write bytearray into file\
brain.sdcard.savefile('MyTextFile.txt', bytearray("Hello "))

<a id="vex.Brain.Sdcard.appendfile"></a>

#### appendfile

```python
def appendfile(filename: str, *args)
```

### append a bytearray into a named file

Append is used to add more data to an existing file.

#### Arguments:
filename : The name of the file to write
buffer : A bytearray to write into the file

#### Returns:
The number of bytes written

#### Examples:
# append bytearray into file\
brain.sdcard.appendfile('MyTextFile.txt', bytearray("World "))

<a id="vex.Brain.Sdcard.size"></a>

#### size

```python
def size(filename: str)
```

### returns the size in bytes of the named file

#### Arguments:
filename : The name of the file to check

#### Returns:
size of file in bytes

#### Examples:

<a id="vex.Brain.Sdcard.exists"></a>

#### exists

```python
def exists(*args)
```

### check to see if named file exists on the sd card

#### Arguments:
filename : The name of the file to check

#### Returns:
True if file exists

#### Examples:

<a id="vex.Competition"></a>

## Competition Objects

```python
class Competition()
```

### Competition class - create a class used for competition control

#### Arguments:
driver : A function called as a thread when the driver control period starts.
autonomous : A function called as a thread when the driver control period starts.

#### Returns:
An instance of the Competition class

#### Examples:
def driver():
print("driver called")

def auton():
print("auton called")

comp = Competition(driver, auton)

<a id="vex.Competition.is_enabled"></a>

#### is\_enabled

```python
@staticmethod
def is_enabled()
```

### return enable/disable state of the robot

#### Arguments:
None

#### Returns:
True if the robot is enabled

<a id="vex.Competition.is_driver_control"></a>

#### is\_driver\_control

```python
@staticmethod
def is_driver_control()
```

### return driver control state of the robot

#### Arguments:
None

#### Returns:
True if driver control is enabled

<a id="vex.Competition.is_autonomous"></a>

#### is\_autonomous

```python
def is_autonomous()
```

### return autonomous state of the robot

#### Arguments:
None

#### Returns:
True if autonomous is enabled

<a id="vex.Competition.is_competition_switch"></a>

#### is\_competition\_switch

```python
def is_competition_switch()
```

### return connection state of the competition switch

#### Arguments:
None

#### Returns:
True if competition switch is connected

<a id="vex.Competition.is_field_control"></a>

#### is\_field\_control

```python
def is_field_control()
```

### return connection state of field controller

#### Arguments:
None

#### Returns:
True if field controller is connected

<a id="vex.Controller"></a>

## Controller Objects

```python
class Controller()
```

### Controller class - create a class to access the controller

#### Arguments:
None

#### Returns:
An instance of the Controller class

#### Examples:

<a id="vex.Controller.Axis"></a>

## Axis Objects

```python
class Axis()
```

### Axis class

#### Arguments:
None

#### Returns:
An instance of an Axis class

#### Examples:

<a id="vex.Controller.Axis.value"></a>

#### value

```python
def value()
```

### Return the current position of the axis

#### Arguments:
None

#### Returns:
A value in the range +/- 127

#### Examples:
a = controller.axis1.position()

<a id="vex.Controller.Axis.position"></a>

#### position

```python
def position()
```

### Return the current position of the axis in percentage

#### Arguments:
None

#### Returns:
A value in the range +/- 100

#### Examples:
a = controller.axis1.position()

<a id="vex.Controller.Axis.changed"></a>

#### changed

```python
def changed(callback: Callable[..., None], arg: tuple = ())
```

### Register a function to be called when the axis value changes

#### Arguments:
callback : A function that will be called when the axis value changes
arg (optional) : A tuple that is used to pass arguments to the callback function.

#### Returns:
An instance of the Event class

#### Examples:
def foo():
print("axis changed")

controller.axis1.changed(foo)

<a id="vex.Controller.Button"></a>

## Button Objects

```python
class Button()
```

<a id="vex.Controller.Button.pressing"></a>

#### pressing

```python
def pressing()
```

### Returns whether a button is currently being pressed

#### Arguments:
None

#### Returns:
True or False

<a id="vex.Controller.Button.pressed"></a>

#### pressed

```python
def pressed(callback: Callable[..., None], arg: tuple = ())
```

### Register a function to be called when a button is pressed

#### Arguments:
callback : A function that will be called when the button is pressed
arg (optional) : A tuple that is used to pass arguments to the callback function.

#### Returns:
An instance of the Event class

#### Examples:
def foo():
print("button pressed")

controller.buttonL1.pressed(foo)

<a id="vex.Controller.Button.released"></a>

#### released

```python
def released(callback: Callable[..., None], arg: tuple = ())
```

### Register a function to be called when a button is released

#### Arguments:
callback : A function that will be called when the button is released
arg (optional) : A tuple that is used to pass arguments to the callback function.

#### Returns:
An instance of the Event class

#### Examples:
def foo():
print("button released")

controller.buttonL1.released(foo)

<a id="vex.Controller.Lcd"></a>

## Lcd Objects

```python
class Lcd()
```

### Controller.Lcd class

A class used to access the screen on the V5 controller.

#### Arguments:
None

#### Returns:
An instance of the Brain.Lcd class

<a id="vex.Controller.Lcd.set_cursor"></a>

#### set\_cursor

```python
def set_cursor(row: vexnumber, col: vexnumber)
```

### Set the cursor position used for printing text on the screen

V5 controller has at most 3 lines of text

#### Arguments:
row : The cursor row.  1, 2 or 3
col : The cursor column.  The first column is 1.

#### Returns:
None

<a id="vex.Controller.Lcd.column"></a>

#### column

```python
def column()
```

Return the current column where text will be printed

<a id="vex.Controller.Lcd.row"></a>

#### row

```python
def row()
```

Return the current row where text will be printed

<a id="vex.Controller.Lcd.print"></a>

#### print

```python
def print(*args)
```

### print text on the screen using current curser position.

#### Arguments:
Optional keyword arguments:
sep : string inserted between values, default a space.
precision : the number of decimal places to display when printing simple numbers, default is 2

#### Returns:
None

#### Examples:
# print the number 1 on the screen at current cursor position\
controller.screen.print(1)

# print the numbers 1, 2, 3 and 4 on the screen at current cursor position separated by a '-'\
controller.screen.print(1, 2, 3, 4, sep='-')

# print motor1 velocity on the screen using a format string\
controller.screen.print("motor  1 : % 7.2f" %(motor1.velocity()))

<a id="vex.Controller.Lcd.clear_screen"></a>

#### clear\_screen

```python
def clear_screen()
```

### Clear the whole screen

#### Arguments:
None

#### Returns:
None

#### Examples:
controller.screen.clear_screen()

<a id="vex.Controller.Lcd.clear_row"></a>

#### clear\_row

```python
def clear_row(number: vexnumber)
```

### Clear screen row

#### Arguments:
row (optional) : The row to clear, 1, 2, or 3, default is current cursor row

#### Returns:
None

#### Examples:
# clear row 2\
controller.screen.clear_row(2)

<a id="vex.Controller.Lcd.next_row"></a>

#### next\_row

```python
def next_row()
```

### Move the cursor to the beginning of the next row

#### Arguments:
None

#### Returns:
None

<a id="vex.Controller.rumble"></a>

#### rumble

```python
def rumble(pattern: str)
```

### Send a rumble string to the V5 controller

#### Arguments:
pattern : A pattern using '.' and '-' for short and long rumbles.

#### Returns:
None

#### Examples:
controller.rumble('..--')

<a id="vex.Event"></a>

## Event Objects

```python
class Event()
```

### Event class - create a new event

A function is registered that will be called when the event broadcast() function is called.
More than one function can be assigned to a single event.

#### Arguments:
callback (optional) : A function that will be called when the event is broadcast.
arg (optional) : A tuple that is used to pass arguments to the event callback function.

#### Returns:
An instance of the Event class

#### Examples:
def foo():
print("foo")

def bar():
print("bar")

e = Event(foo)\
e.set(bar)

# There needs to be some small delay after events are created before they can be broadcast to\
sleep(20)

# cause both foo and bar to be called\
e.broadcast()

<a id="vex.Event.__call__"></a>

#### \_\_call\_\_

```python
def __call__(callback: Callable[..., None], arg: tuple = ())
```

### Add callback function to an existing event

#### Arguments:
callback : A function that will be called when the event is broadcast.
arg (optional) : A tuple that is used to pass arguments to the event callback function.

#### Returns:
None

#### Examples:
def bar():
print("bar")

# add callback function to existing event e\
e(bar)

<a id="vex.Event.set"></a>

#### set

```python
def set(callback: Callable[..., None], arg: tuple = ())
```

### Add callback function to an existing event

#### Arguments:
callback : A function that will be called when the event is broadcast.
arg (optional) : A tuple that is used to pass arguments to the event callback function.

#### Returns:
None

#### Examples:
def bar():
print("bar")

# add callback function to existing event e\
e.set(bar)

<a id="vex.Event.broadcast"></a>

#### broadcast

```python
def broadcast()
```

### Broadcast to the event and cause all registered callback function to run

#### Arguments:
None

#### Returns:
None

#### Examples:
# broadcast to an existing event e\
e.broadcast()

<a id="vex.Event.broadcast_and_wait"></a>

#### broadcast\_and\_wait

```python
def broadcast_and_wait(timeout=60000)
```

### Broadcast to the event and cause all registered callback function to run

This is similar to broadcast except that it will wait for all registered callbacks to complete before returning.

#### Arguments:
None

#### Returns:
None

#### Examples:
# broadcast to an existing event e, wait for completion\
e.broadcast_and_wait()

<a id="vex.Gps"></a>

## Gps Objects

```python
class Gps()
```

### Gps class - a class for working with the gps sensor

#### Arguments:
port : The smartport this device is attached to
origin_x (optional) : The X location of the GPS with respect to origin of the robot.
origin_y (optional) : The Y location of the GPS with respect to origin of the robot.\
note. both X and Y must be supplied
units (optional) : The units that X and Y location are specified in, default is MM

#### Returns:
An instance of the Gps class

#### Examples:
gps1 = Gps(Ports.PORT1)

<a id="vex.Gps.installed"></a>

#### installed

```python
def installed(*args)
```

### Check for device connection

#### Arguments:
None

#### Returns:
True or False

<a id="vex.Gps.timestamp"></a>

#### timestamp

```python
def timestamp()
```

### Request the timestamp of last received message from the sensor

#### Arguments:
None

#### Returns:
timestamp of the last status packet in mS

<a id="vex.Gps.set_heading"></a>

#### set\_heading

```python
def set_heading(value, units=RotationUnits.DEG)
```

### set the gps heading to a new value

The new value for heading should be in the range 0 - 359.99 degrees.

#### Arguments:
value : The new value to use for heading.
units (optional) : The rotation units type for value, the default is DEGREES

#### Returns:
None

#### Examples:
# set the value of heading to 180 degrees\
gps1.set_heading(180)

<a id="vex.Gps.reset_heading"></a>

#### reset\_heading

```python
def reset_heading()
```

### Reset the gps heading to 0

#### Arguments:
None

#### Returns:
None

<a id="vex.Gps.heading"></a>

#### heading

```python
def heading(units=RotationUnits.DEG)
```

### read the current heading of the gps

heading will be returned in the range 0 - 359.99 degrees

#### Arguments:
units (optional) : The units to return the heading in, default is DEGREES

#### Returns:
A value for heading in the range that is specified by the units.

#### Examples:
# get the current heading for the gps\
value = gps1.heading()

<a id="vex.Gps.set_rotation"></a>

#### set\_rotation

```python
def set_rotation(value, units=RotationUnits.DEG)
```

### set the gps rotation to a new value

#### Arguments:
value : The new value to use for rotation.
units (optional) : The rotation units type for value, the default is DEGREES

#### Returns:
None

#### Examples:
# set the value of rotation to 180 degrees\
gps1.set_rotation(180)

<a id="vex.Gps.reset_rotation"></a>

#### reset\_rotation

```python
def reset_rotation()
```

### Reset the gps rotation to 0

#### Arguments:
None

#### Returns:
None

<a id="vex.Gps.rotation"></a>

#### rotation

```python
def rotation(units=RotationUnits.DEG)
```

### read the current rotation of the gps

rotation is not limited, it can be both positive and negative and shows the absolute angle of the gps.

#### Arguments:
units (optional) : The units to return the rotation in, default is DEGREES

#### Returns:
A value for heading in the range that is specified by the units.

#### Examples:
# get the current rotation for the gps\
value = gps1.rotation()

<a id="vex.Gps.x_position"></a>

#### x\_position

```python
def x_position(units=DistanceUnits.MM)
```

### read the current x coordinate of the gps

#### Arguments:
units (optional) : The units to return the position in, default is MM

#### Returns:
A value for the x coordinate in the units specified.

#### Examples:
# get the current x coordinate for the gps\
posx = gps1.x_position()

<a id="vex.Gps.y_position"></a>

#### y\_position

```python
def y_position(units=DistanceUnits.MM)
```

### read the current y coordinate of the gps

#### Arguments:
units (optional) : The units to return the position in, default is MM

#### Returns:
A value for the y coordinate in the units specified.

#### Examples:
# get the current y coordinate for the gps\
posy = gps1.y_position()

<a id="vex.Gps.quality"></a>

#### quality

```python
def quality()
```

### read the current quality of the gps data

A quality of 100 indicates the gps can see the gps field strip and is returning good readings\
The value for quality will reduce as the confidence in x and y location lowers.

#### Arguments:
None

#### Returns:
A value of quality in the range 0 to 100

#### Examples:
# get the current location and heading quality for the gps\
q = gps1.quality()

<a id="vex.Gps.set_origin"></a>

#### set\_origin

```python
def set_origin(x=0, y=0, units=DistanceUnits.MM)
```

### set the origin of the gps sensor

An alternate way of setting sensor origin if not provided in the Gps class constructor.

#### Arguments:
x : The X location of the GPS with respect to origin of the robot.
y : The Y location of the GPS with respect to origin of the robot.\
note. both X and Y must be supplied
units (optional) : The units that X and Y location are specified in, default is MM

#### Returns:
None

#### Examples:
# set the origin of the gps\
gps1.set_origin(6, -6, INCHES)

<a id="vex.Gps.set_location"></a>

#### set\_location

```python
def set_location(x,
                 y,
                 units=DistanceUnits.MM,
                 angle=0,
                 units_r=RotationUnits.DEG)
```

### set the initial location of the robot

This gives a hint as to the location of the robot/gps sensor when it is first initialized.\
This can be used if in the initial position the gps cannot see the gps field strip.

#### Arguments:
x : The initial X coordinate.
y : The initial Y coordinate.\
note. both X and Y must be supplied
units (optional) : The units that X and Y coordinates are specified in, default is MM
angle (optional) : The initial heading of the robot.
units_r (optional) : The units that angle is specified in, default is DEGREES

#### Returns:
None

#### Examples:
# set the initial location of the gps\
gps1.set_location(1000, -1000, MM, 90, DEGREES)

<a id="vex.Gps.calibrate"></a>

#### calibrate

```python
def calibrate()
```

not used on the GPS sensor

<a id="vex.Gps.is_calibrating"></a>

#### is\_calibrating

```python
def is_calibrating()
```

not used on the GPS sensor

<a id="vex.Gps.orientation"></a>

#### orientation

```python
def orientation(axis: OrientationType.OrientationType,
                units=RotationUnits.DEG)
```

### read the orientation for one axis of the gps

#### Arguments:
axis : The axis to read
units (optional) : The units to return the orientation in, default is DEGREES

#### Returns:
A value for the axis orientation in the units specified.

#### Examples:
# get the pitch value for the gps\
pitch = gps1.orientation(OrientationType.PITCH)

<a id="vex.Gps.gyro_rate"></a>

#### gyro\_rate

```python
def gyro_rate(axis: AxisType.AxisType, units=VelocityUnits.DPS)
```

### read the gyro rate for one axis of the gps

#### Arguments:
axis : The axis to read
units (optional) : The units to return the gyro rate in, default is DPS

#### Returns:
A value for the gyro rate of the axis in the units specified.

#### Examples:
# get the gyro rate for the Z axis of the gps\
zrate = gps1.gyro_rate(ZAXIS)

<a id="vex.Gps.acceleration"></a>

#### acceleration

```python
def acceleration(axis: AxisType.AxisType)
```

### read the acceleration for one axis of the gps

#### Arguments:
axis : The axis to read

#### Returns:
A value for the acceleration of the axis in units of gravity.

#### Examples:
# get the acceleration for the Z axis of the gps\
zaccel = gps1.acceleration(ZAXIS)

<a id="vex.Gps.set_sensor_rotation"></a>

#### set\_sensor\_rotation

```python
def set_sensor_rotation(value, units=RotationUnits.DEG)
```

### set the sensor rotation of the gps sensor with respect to the robot.

This allows heading and rotation methods to return angles relative to the robot rather than the gps.

#### Arguments:
value : The angle of the GPS with respect to the robot.
units (optional) : The units that value is specified in, default is DEGREES

#### Returns:
None

#### Examples:
# set the sensor rotation of the gps\
gps1.set_sensor_rotation(180, DEGREES)

<a id="vex.Gps.changed"></a>

#### changed

```python
def changed(callback: Callable[..., None], arg: tuple = ())
```

### Register a function to be called when the value of the gps heading changes

This is not particularly useful as gps heading is not stable and will cause many events.

#### Arguments:
callback : A function that will be called when the value of the gps heading changes
arg (optional) : A tuple that is used to pass arguments to the callback function.

#### Returns:
An instance of the Event class

#### Examples:
def foo():
print("heading changed")

gps1.changed(foo)

<a id="vex.Gps.set_turn_type"></a>

#### set\_turn\_type

```python
def set_turn_type(turntype)
```

### set the direction that returns positive values for heading

An advanced function that is not generally used.

#### Arguments:
turntype : TurnType.LEFT or TurnType.RIGHT

#### Returns:
None

<a id="vex.Gps.get_turn_type"></a>

#### get\_turn\_type

```python
def get_turn_type()
```

### get the direction that returns positive values for heading

An advanced function that is not generally used.

#### Arguments:
None

#### Returns:
The current TurnType, LEFT or RIGHT

<a id="vex.Inertial"></a>

## Inertial Objects

```python
class Inertial()
```

### Inertial class - a class for working with the inertial sensor

#### Arguments:
port : The smartport this device is attached to

#### Returns:
An instance of the Inertial class

#### Examples:
imu1 = Inertial(Ports.PORT1)

<a id="vex.Inertial.installed"></a>

#### installed

```python
def installed(*args)
```

### Check for device connection

#### Arguments:
None

#### Returns:
True or False

<a id="vex.Inertial.timestamp"></a>

#### timestamp

```python
def timestamp()
```

### Request the timestamp of last received message from the sensor

#### Arguments:
None

#### Returns:
timestamp of the last status packet in mS

<a id="vex.Inertial.set_heading"></a>

#### set\_heading

```python
def set_heading(value, units=RotationUnits.DEG)
```

### set the inertial sensor heading to a new value

The new value for heading should be in the range 0 - 359.99 degrees.

#### Arguments:
value : The new value to use for heading.
units (optional) : The rotation units type for value, the default is DEGREES

#### Returns:
None

#### Examples:
# set the value of heading to 180 degrees\
imu1.set_heading(180)

<a id="vex.Inertial.reset_heading"></a>

#### reset\_heading

```python
def reset_heading()
```

### Reset the inertial sensor heading to 0

#### Arguments:
None

#### Returns:
None

<a id="vex.Inertial.heading"></a>

#### heading

```python
def heading(units=RotationUnits.DEG)
```

### read the current heading of the inertial sensor

heading will be returned in the range 0 - 359.99 degrees

#### Arguments:
units (optional) : The units to return the heading in, default is DEGREES

#### Returns:
A value for heading in the range that is specified by the units.

#### Examples:
# get the current heading for the inertial sensor\
value = imu1.heading()

<a id="vex.Inertial.set_rotation"></a>

#### set\_rotation

```python
def set_rotation(value, units=RotationUnits.DEG)
```

### set the inertial sensor rotation to a new value

#### Arguments:
value : The new value to use for rotation.
units (optional) : The rotation units type for value, the default is DEGREES

#### Returns:
None

#### Examples:
# set the value of rotation to 180 degrees\
imu1.set_rotation(180)

<a id="vex.Inertial.reset_rotation"></a>

#### reset\_rotation

```python
def reset_rotation()
```

### Reset the inertial sensor rotation to 0

#### Arguments:
None

#### Returns:
None

<a id="vex.Inertial.rotation"></a>

#### rotation

```python
def rotation(units=RotationUnits.DEG)
```

### read the current rotation of the inertial sensor

rotation is not limited, it can be both positive and negative and shows the absolute angle of the gps.

#### Arguments:
units (optional) : The units to return the rotation in, default is DEGREES

#### Returns:
A value for heading in the range that is specified by the units.

#### Examples:
# get the current rotation for the inertial sensor\
value = imu1.rotation()

<a id="vex.Inertial.calibrate"></a>

#### calibrate

```python
def calibrate()
```

### Start calibration of the inertial sensor

Calibration should done when the inertial sensor is not moving.

#### Arguments:
None

#### Returns:
None

#### Examples:
# start calibration\
imu1.calibrate()\
# wait for completion\
while imu1.is_calibrating():\
sleep(50, MSEC)

<a id="vex.Inertial.is_calibrating"></a>

#### is\_calibrating

```python
def is_calibrating()
```

### check the calibration status of the inertial sensor

Calibration should done when the inertial sensor is not moving.

#### Arguments:
None

#### Returns:
True when the inertial sensor is calibrating

#### Examples:
# start calibration\
imu1.calibrate()\
# wait for completion\
while imu1.is_calibrating():\
sleep(50, MSEC)

<a id="vex.Inertial.orientation"></a>

#### orientation

```python
def orientation(axis: OrientationType.OrientationType,
                units=RotationUnits.DEG)
```

### read the orientation for one axis of the inertial sensor

#### Arguments:
axis : The axis to read
units (optional) : The units to return the orientation in, default is DEGREES

#### Returns:
A value for the axis orientation in the units specified.

#### Examples:
# get the pitch value for the inertial sensor\
pitch = imu1.orientation(OrientationType.PITCH)

<a id="vex.Inertial.gyro_rate"></a>

#### gyro\_rate

```python
def gyro_rate(axis: AxisType.AxisType, units=VelocityUnits.DPS)
```

### read the gyro rate for one axis of the inertial sensor

#### Arguments:
axis : The axis to read
units (optional) : The units to return the gyro rate in, default is DPS

#### Returns:
A value for the gyro rate of the axis in the units specified.

#### Examples:
# get the gyro rate for the Z axis of the inertial sensor\
zrate = imu1.gyro_rate(ZAXIS)

<a id="vex.Inertial.acceleration"></a>

#### acceleration

```python
def acceleration(axis: AxisType.AxisType)
```

### read the acceleration for one axis of the inertial sensor

#### Arguments:
axis : The axis to read

#### Returns:
A value for the acceleration of the axis in units of gravity.

#### Examples:
# get the acceleration for the Z axis of the inertial sensor\
zaccel = imu1.acceleration(ZAXIS)

<a id="vex.Inertial.changed"></a>

#### changed

```python
def changed(callback: Callable[..., None], arg: tuple = ())
```

### Register a function to be called when the value of the inertial sensor heading changes

#### Arguments:
callback : A function that will be called when the value of the inertial sensor heading changes
arg (optional) : A tuple that is used to pass arguments to the callback function.

#### Returns:
An instance of the Event class

#### Examples:
def foo():
print("heading changed")

imu1.changed(foo)

<a id="vex.Inertial.collision"></a>

#### collision

```python
def collision(callback: Callable[..., None], arg: tuple = ())
```

### Register a function to be called when the inertial sensor detects a collision

#### Arguments:
callback : A function that will be called when the inertial sensor detects a collision
arg (optional) : A tuple that is used to pass arguments to the callback function.

#### Returns:
An instance of the Event class

#### Examples:
def foo():
print("collision")

imu1.collision(foo)

<a id="vex.Inertial.set_turn_type"></a>

#### set\_turn\_type

```python
def set_turn_type(turntype)
```

### set the direction that returns positive values for heading

An advanced function that is not generally used.

#### Arguments:
turntype : TurnType.LEFT or TurnType.RIGHT

#### Returns:
None

<a id="vex.Inertial.get_turn_type"></a>

#### get\_turn\_type

```python
def get_turn_type()
```

### get the direction that returns positive values for heading

An advanced function that is not generally used.

#### Arguments:
None

#### Returns:
The current TurnType, LEFT or RIGHT

<a id="vex.Motor"></a>

## Motor Objects

```python
class Motor()
```

### Motor class - use this to create an instance of a V5 smart motor

#### Arguments:
port : The smartport this device is attached to
gears (optional) : The gear cartridge installed in the motor, default is the green 18_1
reverse (optional) : Should the motor's spin direction be reversed, default is False

#### Returns:
A new Motor object.

#### Examples:
motor1 = Motor(Ports.PORT1)\
motor2 = Motor(Ports.PORT2, GearSetting.RATIO_36_1)\
motor3 = Motor(Ports.PORT3, True)\
motor4 = Motor(Ports.PORT4, GearSetting.RATIO_6_1, True)

<a id="vex.Motor.installed"></a>

#### installed

```python
def installed()
```

### Check for device connection

#### Arguments:
None

#### Returns:
True or False

<a id="vex.Motor.timestamp"></a>

#### timestamp

```python
def timestamp()
```

### Request the timestamp of last received message from the motor

#### Arguments:
None

#### Returns:
timestamp of the last status packet in mS

<a id="vex.Motor.set_velocity"></a>

#### set\_velocity

```python
def set_velocity(value: vexnumber,
                 units: VelocityPercentUnits = VelocityUnits.RPM)
```

### Set default velocity for the motor
This will be the velocity used for subsequent calls to spin if a velocity is not provided
to that function.

#### Arguments:
value : The new velocity
units : The units for the supplied velocity, the default is RPM

#### Returns:
None

<a id="vex.Motor.set_reversed"></a>

#### set\_reversed

```python
def set_reversed(value: bool)
```

### Set the reverse flag for the motor
Setting the reverse flag will cause spin commands to run the motor in reverse.

#### Arguments:
value : Reverse flag, True or False

#### Returns:
None

<a id="vex.Motor.set_stopping"></a>

#### set\_stopping

```python
def set_stopping(value: BrakeType.BrakeType)
```

### Set the stopping mode of the motor
Setting the action for the motor when stopped.

#### Arguments:
value : The stopping mode, COAST, BRAKE or HOLD

#### Returns:
None

<a id="vex.Motor.reset_position"></a>

#### reset\_position

```python
def reset_position()
```

### Reset the motor position to 0

#### Arguments:
None

#### Returns:
None

<a id="vex.Motor.set_position"></a>

#### set\_position

```python
def set_position(value: vexnumber, units=RotationUnits.DEG)
```

### Set the current position of the motor
The position returned by the position() function is set to this value.

#### Arguments:
value : The new position
units : The units for the provided position, the default is DEGREES

#### Returns:
None

<a id="vex.Motor.set_timeout"></a>

#### set\_timeout

```python
def set_timeout(value: vexnumber, units=TimeUnits.MSEC)
```

### Set the timeout value used by the motor
The timeout value is used when performing spin_to_position and spin_for commands.  If timeout is
reached and the motor has not completed moving, then the spin... function will return False.

#### Arguments:
value : The new timeout
units : The units for the provided timeout, the default is MSEC

#### Returns:
None

<a id="vex.Motor.get_timeout"></a>

#### get\_timeout

```python
def get_timeout()
```

### Returns the current value of motor timeout

#### Arguments:
None

#### Returns:
The current timeout value

<a id="vex.Motor.spin"></a>

#### spin

```python
def spin(direction: DirectionType.DirectionType, *args, **kwargs)
```

### Spin the motor using the provided arguments

#### Arguments:
direction : The direction to spin the motor, FORWARD or REVERSE
velocity (optional) : spin the motor using this velocity, the default velocity set by set_velocity will be used if not provided.
units (optional) : The units of the provided velocity, default is RPM

#### Returns:
None

#### Examples:
# spin motor forward at velocity set with set_velocity\
motor1.spin(FORWARD)

# spin motor forward at 50 rpm\
motor1.spin(FORWARD, 50)

# spin with negative velocity, ie. backwards\
motor1.spin(FORWARD, -20)

# spin motor forwards with 100% velocity\
motor1.spin(FORWARD, 100, PERCENT)

# spin motor forwards at 50 rpm\
motor1.spin(FORWARD, 50, RPM)

# spin motor forwards at 360 dps\
motor1.spin(FORWARD, 360.0, VelocityUnits.DPS)

<a id="vex.Motor.spin_to_position"></a>

#### spin\_to\_position

```python
def spin_to_position(rotation: vexnumber, *args, **kwargs)
```

### Spin the motor to an absolute position using the provided arguments
Move the motor to the requested position.\
This function supports keyword arguments.

#### Arguments:
rotation : The position to spin the motor to
units (optional) : The units for the provided position, the default is DEGREES
velocity (optional) : spin the motor using this velocity, the default velocity set by set_velocity will be used if not provided.
units_v (optional) : The units of the provided velocity, default is RPM
wait (optional) : This indicates if the function should wait for the command to complete or return immediately, default is True.

#### Returns:
None

#### Examples:
# spin to 180 degrees\
motor1.spin_to_position(180)

# spin to 2 TURNS (revolutions)\
motor1.spin_to_position(2, TURNS)

# spin to 180 degrees at 25 rpm\
motor1.spin_to_position(180, DEGREES, 25, RPM)

# spin to 180 degrees and do not wait for completion\
motor1.spin_to_position(180, DEGREES, False)

# spin to 180 degrees and do not wait for completion\
motor1.spin_to_position(180, DEGREES, wait=False)

<a id="vex.Motor.spin_for"></a>

#### spin\_for

```python
def spin_for(direction: DirectionType.DirectionType, rot_or_time: vexnumber,
             *args, **kwargs)
```

### Spin the motor to a relative position using the provided arguments
Move the motor to the requested position or for the specified amount of time.\
The position is relative (ie. an offset) to the current position\
This function supports keyword arguments.

#### Arguments:
dir : The direction to spin the motor, FORWARD or REVERSE
rot_or_time : The relative position to spin the motor to or tha amount of time to spin for
units (optional) : The units for the provided position or time, the default is DEGREES or MSEC
velocity (optional) : spin the motor using this velocity, the default velocity set by set_velocity will be used if not provided.
units_v (optional) : The units of the provided velocity, default is RPM
wait (optional) : This indicates if the function should wait for the command to complete or return immediately, default is True.

#### Returns:
None

#### Examples:
# spin 180 degrees from the current position\
motor1.spin_for(FORWARD, 180)

# spin reverse 2 TURNS (revolutions) from the current position\
motor1.spin_for(REVERSE, 2, TURNS)

# spin 180 degrees from the current position at 25 rpm\
motor1.spin_for(FORWARD, 180, DEGREES, 25, RPM)

# spin 180 degrees  from the current position and do not wait for completion\
motor1.spin_for(FORWARD, 180, DEGREES, False)

# spin 180 degrees  from the current position and do not wait for completion\
motor1.spin_for(FORWARD, 180, DEGREES, wait=False)

<a id="vex.Motor.is_spinning"></a>

#### is\_spinning

```python
def is_spinning()
```

### Returns the current status of the spin_to_position or spin_for command
This function is used when False has been passed as the wait parameter to spin_to_position or spin_for\
It will return True if the motor is still spinning or False if it has completed the move or a timeout occurred.

#### Arguments:
None

#### Returns:
The current spin_to_position or spin_for status

<a id="vex.Motor.is_done"></a>

#### is\_done

```python
def is_done()
```

### Returns the current status of the spin_to_position or spin_for command
This function is used when False has been passed as the wait parameter to spin_to_position or spin_for\
It will return False if the motor is still spinning or True if it has completed the move or a timeout occurred.

#### Arguments:
None

#### Returns:
The current spin_to_position or spin_for status

<a id="vex.Motor.stop"></a>

#### stop

```python
def stop(mode=None)
```

### Stop the motor, set to 0 velocity and set current stopping_mode
The motor will be stopped and set to COAST, BRAKE or HOLD

#### Arguments:
None

#### Returns:
None

<a id="vex.Motor.set_max_torque"></a>

#### set\_max\_torque

```python
def set_max_torque(value, units: TorquePercentCurrentUnits)
```

### Set the maximum torque the motor will use
The torque can be set as torque, current or percent of maximum.

#### Arguments:
value : the new maximum torque to use
units : the units that value is passed in

#### Returns:
None

#### Examples:
# set maximum torque to 2 Nm\
motor1.set_max_torque(2, TorqueUnits.NM)

# set maximum torque to 1 Amp\
motor1.set_max_torque(1, CurrentUnits.AMP)

# set maximum torque to 20 percent\
motor1.set_max_torque(20, PERCENT)

<a id="vex.Motor.direction"></a>

#### direction

```python
def direction()
```

### Returns the current direction the motor is spinning in

#### Arguments:
None

#### Returns:
The spin direction, FORWARD, REVERSE or UNDEFINED

<a id="vex.Motor.position"></a>

#### position

```python
def position(*args)
```

### Returns the position of the motor

#### Arguments:
units (optional) : The units for the returned position, the default is DEGREES

#### Returns:
The motor position in provided units

<a id="vex.Motor.velocity"></a>

#### velocity

```python
def velocity(*args)
```

### Returns the velocity of the motor

#### Arguments:
units (optional) : The units for the returned velocity, the default is RPM

#### Returns:
The motor velocity in provided units

<a id="vex.Motor.current"></a>

#### current

```python
def current(*args)
```

### Returns the current the motor is using

#### Arguments:
units (optional) : The units for the returned current, the default is AMP

#### Returns:
The motor current in provided units

<a id="vex.Motor.power"></a>

#### power

```python
def power(*args)
```

### Returns the power the motor is providing

#### Arguments:
units (optional) : The units for the returned power, the default is WATT

#### Returns:
The motor power in provided units

<a id="vex.Motor.torque"></a>

#### torque

```python
def torque(*args)
```

### Returns the torque the motor is providing

#### Arguments:
units (optional) : The units for the returned torque, the default is NM

#### Returns:
The motor torque in provided units

<a id="vex.Motor.efficiency"></a>

#### efficiency

```python
def efficiency(*args)
```

### Returns the efficiency of the motor

#### Arguments:
units (optional) : The units for the efficiency, the only valid value is PERCENT

#### Returns:
The motor efficiency in percent

<a id="vex.Motor.temperature"></a>

#### temperature

```python
def temperature(*args)
```

### Returns the temperature of the motor

#### Arguments:
units (optional) : The units for the returned temperature, the default is CELSIUS

#### Returns:
The motor temperature in provided units

<a id="vex.Motor.command"></a>

#### command

```python
def command(*args)
```

### Returns the last velocity sent to the motor

#### Arguments:
units (optional) : The units for the returned velocity, the default is RPM

#### Returns:
The motor command velocity in provided units

<a id="vex.Thread"></a>

## Thread Objects

```python
class Thread()
```

### Thread class - create a new thread of execution

This class is used to create a new thread using the vexos scheduler.

#### Arguments:
callback : A function used as the entry point for the thread
arg (optional) : A tuple that is used to pass arguments to the thread entry function.

#### Returns:
An instance of the Thread class

#### Examples:
def foo():
print('the callback was called')

t1 = Thread( foo )

def bar(p1, p2):
print('the callback was called with ', p1, ' and ', p2)

t2 = Thread( bar, (1,2) )

<a id="vex.Thread.stop"></a>

#### stop

```python
def stop()
```

### Stop a thread

#### Arguments:
None

#### Returns:
None

<a id="vex.Thread.sleep_for"></a>

#### sleep\_for

```python
@staticmethod
def sleep_for(duration: vexnumber, units=TimeUnits.MSEC)
```

### sleep a thread

#### Arguments:
duration : time to sleep this thread for
units (optional) : units of time, default is MSEC

#### Returns:
None

<a id="vex.Timer"></a>

## Timer Objects

```python
class Timer()
```

### Timer class - create a new timer

This class is used to create a new timer\
A timer can be used to measure time, access the system time and run a function at a time in the future.

#### Arguments:
None

#### Returns:
An instance of the Timer class

#### Examples:
t1 = Timer()

<a id="vex.Timer.time"></a>

#### time

```python
def time(units=TimeUnits.MSEC)
```

### return the current time for this timer

#### Arguments:
units (optional) : the units that the time should be returned in, default is MSEC

#### Returns:
An the current time in specified units.

#### Examples:

<a id="vex.Timer.value"></a>

#### value

```python
def value()
```

### return the current time for this timer in seconds

#### Arguments:
None

#### Returns:
An the current time in seconds.

#### Examples:

<a id="vex.Timer.clear"></a>

#### clear

```python
def clear()
```

### reset the timer to 0

#### Arguments:
None

#### Returns:
None

#### Examples:

<a id="vex.Timer.reset"></a>

#### reset

```python
def reset()
```

### reset the timer to 0

#### Arguments:
None

#### Returns:
None

#### Examples:

<a id="vex.Timer.system"></a>

#### system

```python
def system()
```

### return the system time in mS

#### Arguments:
None

#### Returns:
system time in mS

#### Examples:

<a id="vex.Timer.system_high_res"></a>

#### system\_high\_res

```python
def system_high_res()
```

### return the high resolution system time in uS

#### Arguments:
None

#### Returns:
system time in uS

#### Examples:

<a id="vex.Timer.event"></a>

#### event

```python
def event(callback: Callable[..., None], delay: int, arg: tuple = ())
```

### register a function to be called in the future

#### Arguments:
callback : A function that will called after the supplied delay
delay : The delay before the callback function is called.
arg (optional) : A tuple that is used to pass arguments to the function.

#### Returns:
None

#### Examples:
def foo(arg):
print('timer has expired ', arg)

t1 = Timer()\
t1.event(foo, 1000, ('Hello',))

<a id="vex.Triport"></a>

## Triport Objects

```python
class Triport()
```

<a id="vex.Triport.installed"></a>

#### installed

```python
def installed()
```

### Check for device connection

#### Arguments:
None

#### Returns:
True or False

<a id="vex.Triport.timestamp"></a>

#### timestamp

```python
def timestamp()
```

### Request the timestamp of last received message from the sensor

#### Arguments:
None

#### Returns:
timestamp of the last status packet in mS

<a id="vex.Limit"></a>

## Limit Objects

```python
class Limit()
```

### Limit class - create a new limit switch

#### Arguments:
port : The 3wire port the limit switch is connected to

#### Returns:
An instance of the Limit class

#### Examples:
limit1 = Limit(brain.three_wire_port.a)

<a id="vex.Limit.value"></a>

#### value

```python
def value()
```

### The current value of the limit switch

#### Arguments:
None

#### Returns:
1 or 0

<a id="vex.Limit.pressed"></a>

#### pressed

```python
def pressed(callback: Callable[..., None], arg: tuple = ())
```

### Register a function to be called when the limit switch is pressed

#### Arguments:
callback : A function that will be called when the limit switch is pressed
arg (optional) : A tuple that is used to pass arguments to the callback function.

#### Returns:
An instance of the Event class

#### Examples:
def foo():
print("switch pressed")

limit1.pressed(foo)

<a id="vex.Limit.released"></a>

#### released

```python
def released(callback: Callable[..., None], arg: tuple = ())
```

### Register a function to be called when the limit switch is released

#### Arguments:
callback : A function that will be called when the limit switch is released
arg (optional) : A tuple that is used to pass arguments to the callback function.

#### Returns:
An instance of the Event class

#### Examples:
def foo():
print("switch released")

limit1.released(foo)

<a id="vex.Limit.pressing"></a>

#### pressing

```python
def pressing()
```

### Returns whether the limit switch is currently being pressed

#### Arguments:
None

#### Returns:
True or False

<a id="vex.Bumper"></a>

## Bumper Objects

```python
class Bumper()
```

### Bumper class - create a new bumper switch

#### Arguments:
port : The 3wire port the bumper switch is connected to

#### Returns:
An instance of the Bumper class

#### Examples:
bumper1 = Bumper(brain.three_wire_port.a)

<a id="vex.Bumper.value"></a>

#### value

```python
def value()
```

### The current value of the bumper switch

#### Arguments:
None

#### Returns:
1 or 0

<a id="vex.Bumper.pressed"></a>

#### pressed

```python
def pressed(callback: Callable[..., None], arg: tuple = ())
```

### Register a function to be called when the bumper switch is pressed

#### Arguments:
callback : A function that will be called when the bumper switch is pressed
arg (optional) : A tuple that is used to pass arguments to the callback function.

#### Returns:
An instance of the Event class

#### Examples:
def foo():
print("switch pressed")

bumper1.pressed(foo)

<a id="vex.Bumper.released"></a>

#### released

```python
def released(callback: Callable[..., None], arg: tuple = ())
```

### Register a function to be called when the bumper switch is released

#### Arguments:
callback : A function that will be called when the bumper switch is released
arg (optional) : A tuple that is used to pass arguments to the callback function.

#### Returns:
An instance of the Event class

#### Examples:
def foo():
print("switch released")

bumper1.released(foo)

<a id="vex.Bumper.pressing"></a>

#### pressing

```python
def pressing()
```

### Returns whether the bumper switch is currently being pressed

#### Arguments:
None

#### Returns:
True or False

<a id="vex.DigitalIn"></a>

## DigitalIn Objects

```python
class DigitalIn()
```

### DigitalIn class - create a new digital input

#### Arguments:
port : The 3wire port to use for the digital input

#### Returns:
An instance of the DigitalIn class

#### Examples:
dig1 = DigitalIn(brain.three_wire_port.a)

<a id="vex.DigitalIn.value"></a>

#### value

```python
def value()
```

### The current value of the digital input

#### Arguments:
None

#### Returns:
1 or 0

<a id="vex.DigitalIn.high"></a>

#### high

```python
def high(callback: Callable[..., None], arg: tuple = ())
```

### Register a function to be called when the digital input goes to the logic high state

#### Arguments:
callback : A function that will be called when the digital input goes to the logic high state
arg (optional) : A tuple that is used to pass arguments to the callback function.

#### Returns:
An instance of the Event class

#### Examples:
def foo():
print("input high")

dig1.high(foo)

<a id="vex.DigitalIn.low"></a>

#### low

```python
def low(callback: Callable[..., None], arg: tuple = ())
```

### Register a function to be called when the digital input goes to the logic low state

#### Arguments:
callback : A function that will be called when the digital input goes to the logic low state
arg (optional) : A tuple that is used to pass arguments to the callback function.

#### Returns:
An instance of the Event class

#### Examples:
def foo():
print("input low")

dig1.low(foo)

<a id="vex.DigitalOut"></a>

## DigitalOut Objects

```python
class DigitalOut()
```

### DigitalOut class - create a new digital output

#### Arguments:
port : The 3wire port to use for the digital output

#### Returns:
An instance of the DigitalOut class

#### Examples:
dig1 = DigitalOut(brain.three_wire_port.a)

<a id="vex.DigitalOut.value"></a>

#### value

```python
def value()
```

### The current value of the digital output

#### Arguments:
None

#### Returns:
1 or 0

<a id="vex.DigitalOut.set"></a>

#### set

```python
def set(value)
```

### Set the output level for the digital output

#### Arguments:
value : 0, 1, True or False

#### Returns:
None

#### Examples:
dig1.set(True)

<a id="vex.Led"></a>

## Led Objects

```python
class Led()
```

### Led class - create a new led

#### Arguments:
port : The 3wire port to use for the led

#### Returns:
An instance of the Led class

#### Examples:
led1 = Led(brain.three_wire_port.a)

<a id="vex.Led.value"></a>

#### value

```python
def value()
```

### The current value of the led

#### Arguments:
None

#### Returns:
1 or 0

<a id="vex.Led.on"></a>

#### on

```python
def on()
```

### Turn the led on

#### Arguments:
None

#### Returns:
None

#### Examples:
led1.on()

<a id="vex.Led.off"></a>

#### off

```python
def off()
```

### Turn the led off

#### Arguments:
None

#### Returns:
None

#### Examples:
led1.off()

<a id="vex.Pneumatics"></a>

## Pneumatics Objects

```python
class Pneumatics()
```

### Pneumatics class - create a new pneumatics driver class

#### Arguments:
port : The 3wire port to use for the pneumatics

#### Returns:
An instance of the Pneumatics class

#### Examples:
p1 = Pneumatics(brain.three_wire_port.a)

<a id="vex.Pneumatics.value"></a>

#### value

```python
def value()
```

### The current state of the pneumatics driver

#### Arguments:
None

#### Returns:
1 or 0

<a id="vex.Pneumatics.open"></a>

#### open

```python
def open()
```

### Set the pneumatics driver to the open state

#### Arguments:
None

#### Returns:
None

#### Examples:
p1.open()

<a id="vex.Pneumatics.close"></a>

#### close

```python
def close()
```

### Set the pneumatics driver to the close state

#### Arguments:
None

#### Returns:
None

#### Examples:
p1.close()

<a id="vex.Potentiometer"></a>

## Potentiometer Objects

```python
class Potentiometer()
```

### Potentiometer class - create a new potentiometer

#### Arguments:
port : The 3wire port to use for the potentiometer

#### Returns:
An instance of the Potentiometer class

#### Examples:
pot1 = Potentiometer(brain.three_wire_port.a)

<a id="vex.Potentiometer.value"></a>

#### value

```python
def value(units: AnalogPercentUnits = AnalogUnits.TWELVEBIT)
```

### The current value of the potentiometer

#### Arguments:
units (optional) : A valid AnalogUnits type or PERCENT, the default is 12 bit analog

#### Returns:
A value in the range that is specified by the units.

#### Examples:
# get potentiometer in range 0 - 4095\
value = pot1.value()

# get potentiometer in range 0 - 1023\
value = pot1.value(AnalogUnits.TENBIT)

<a id="vex.Potentiometer.angle"></a>

#### angle

```python
def angle(units: RotationPercentUnits = RotationUnits.DEG)
```

### The current angle of the potentiometer

#### Arguments:
units (optional) : A valid RotationUnits type or PERCENT, the default is DEGREES

#### Returns:
A value in the range that is specified by the units.

#### Examples:
# get potentiometer in range 0 - 250 degrees\
angle = pot1.angle()

# get potentiometer in range 0 - 100%\
angle = pot1.angle(PERCENT)

<a id="vex.Potentiometer.changed"></a>

#### changed

```python
def changed(callback: Callable[..., None], arg: tuple = ())
```

### Register a function to be called when the value of the potentiometer changes

#### Arguments:
callback : A function that will be called when the value of the potentiometer changes
arg (optional) : A tuple that is used to pass arguments to the callback function.

#### Returns:
An instance of the Event class

#### Examples:
def foo():
print("pot changed")

pot1.changed(foo)

<a id="vex.PotentiometerV2"></a>

## PotentiometerV2 Objects

```python
class PotentiometerV2()
```

### PotentiometerV2 class - create a new potentiometer

#### Arguments:
port : The 3wire port to use for the potentiometer

#### Returns:
An instance of the PotentiometerV2 class

#### Examples:
pot1 = PotentiometerV2(brain.three_wire_port.a)

<a id="vex.PotentiometerV2.value"></a>

#### value

```python
def value(units: AnalogPercentUnits = AnalogUnits.TWELVEBIT)
```

### The current value of the potentiometer

#### Arguments:
units (optional) : A valid AnalogUnits type or PERCENT, the default is 12 bit analog

#### Returns:
A value in the range that is specified by the units.

#### Examples:
# get potentiometer in range 0 - 4095\
value = pot1.value()

# get potentiometer in range 0 - 1023\
value = pot1.value(AnalogUnits.TENBIT)

<a id="vex.PotentiometerV2.angle"></a>

#### angle

```python
def angle(units: RotationPercentUnits = RotationUnits.DEG)
```

### The current angle of the potentiometer

#### Arguments:
units (optional) : A valid RotationUnits type or PERCENT, the default is DEGREES

#### Returns:
A value in the range that is specified by the units.

#### Examples:
# get potentiometer in range 0 - 250 degrees\
angle = pot1.angle()

# get potentiometer in range 0 - 100%\
angle = pot1.angle(PERCENT)

<a id="vex.PotentiometerV2.changed"></a>

#### changed

```python
def changed(callback: Callable[..., None], arg: tuple = ())
```

### Register a function to be called when the value of the potentiometer changes

#### Arguments:
callback : A function that will be called when the value of the potentiometer changes
arg (optional) : A tuple that is used to pass arguments to the callback function.

#### Returns:
An instance of the Event class

#### Examples:
def foo():
print("pot changed")

pot1.changed(foo)

<a id="vex.Line"></a>

## Line Objects

```python
class Line()
```

### Line class - create a new line sensor

#### Arguments:
port : The 3wire port to use for the line sensor

#### Returns:
An instance of the Line class

#### Examples:
line1 = Line(brain.three_wire_port.a)

<a id="vex.Line.value"></a>

#### value

```python
def value(units: AnalogPercentUnits = AnalogUnits.TWELVEBIT)
```

### The current value of the line sensor

#### Arguments:
units (optional) : A valid AnalogUnits type or PERCENT, the default is 12 bit analog

#### Returns:
A value in the range that is specified by the units.

#### Examples:
# get line sensor in range 0 - 4095\
value = line1.value()

# get line sensor in range 0 - 1023\
value = line1.value(AnalogUnits.TENBIT)

<a id="vex.Line.reflectivity"></a>

#### reflectivity

```python
def reflectivity(units=PercentUnits.PERCENT)
```

### The current reflectivity of the line sensor

The reflectivity of the line sensor is an estimation based on the raw value of the sensor.\
A reflectivity of 0% is a raw value of approximated 3000 or greater\
A reflectivity of 100% is a raw value of 0

#### Arguments:
units (optional) : The only valid value is PERCENT

#### Returns:
A value in the range 0 to 100%

#### Examples:
# get line sensor reflectivity in range of 0 -100%\
value = line1.reflectivity()

<a id="vex.Line.changed"></a>

#### changed

```python
def changed(callback: Callable[..., None], arg: tuple = ())
```

### Register a function to be called when the value of the line sensor changes

#### Arguments:
callback : A function that will be called when the value of the line sensor changes
arg (optional) : A tuple that is used to pass arguments to the callback function.

#### Returns:
An instance of the Event class

#### Examples:
def foo():
print("line sensor changed")

line1.changed(foo)

<a id="vex.Light"></a>

## Light Objects

```python
class Light()
```

### Light class - create a new light sensor

#### Arguments:
port : The 3wire port to use for the light sensor

#### Returns:
An instance of the Light class

#### Examples:
light1 = Light(brain.three_wire_port.a)

<a id="vex.Light.value"></a>

#### value

```python
def value(units: AnalogPercentUnits = AnalogUnits.TWELVEBIT)
```

### The current value of the light sensor

#### Arguments:
units (optional) : A valid AnalogUnits type or PERCENT, the default is 12 bit analog

#### Returns:
A value in the range that is specified by the units.

#### Examples:
# get light sensor in range 0 - 4095\
value = light1.value()

# get light sensor in range 0 - 1023\
value = light1.value(AnalogUnits.TENBIT)

<a id="vex.Light.brightness"></a>

#### brightness

```python
def brightness(units=PercentUnits.PERCENT)
```

### The current brightness of light falling on the light sensor

The brightness of the light sensor is an estimation based on the raw value of the sensor.\
A brightness of 0% is a raw value of approximated 900 or greater\
A brightness of 100% is a raw value of 0

#### Arguments:
units (optional) : The only valid value is PERCENT

#### Returns:
A value in the range 0 to 100%

#### Examples:
# get light sensor brightness in range of 0 -100%\
value = light1.brightness()

<a id="vex.Light.changed"></a>

#### changed

```python
def changed(callback: Callable[..., None], arg: tuple = ())
```

### Register a function to be called when the value of the light sensor changes

#### Arguments:
callback : A function that will be called when the value of the light sensor changes
arg (optional) : A tuple that is used to pass arguments to the callback function.

#### Returns:
An instance of the Event class

#### Examples:
def foo():
print("light sensor changed")

light1.changed(foo)

<a id="vex.Gyro"></a>

## Gyro Objects

```python
class Gyro()
```

### Gyro class - create a new gyro sensor

#### Arguments:
port : The 3wire port to use for the gyro sensor

#### Returns:
An instance of the Gyro class

#### Examples:
gyro1 = Gyro(brain.three_wire_port.a)

<a id="vex.Gyro.value"></a>

#### value

```python
def value(units: RotationPercentUnits = DEGREES)
```

### The current value of the gyro

This method is generally not used, see heading() and rotation()

#### Arguments:
units (optional) : A valid RotationUnits type or PERCENT, the default is DEGREES

#### Returns:
A value in the range that is specified by the units.

#### Examples:
# get gyro value in range 0 - 360 degrees\
value = gyro1.value()

<a id="vex.Gyro.calibrate"></a>

#### calibrate

```python
def calibrate()
```

### Start calibration of the gyro

Calibration should done when the gyro is not moving.

#### Arguments:
None

#### Returns:
None

#### Examples:
# start calibration\
gyro1.calibrate()\
# wait for completion\
while gyro1.is_calibrating():\
sleep(50, MSEC)

<a id="vex.Gyro.is_calibrating"></a>

#### is\_calibrating

```python
def is_calibrating()
```

### check the calibration status of the gyro

Calibration should done when the gyro is not moving.

#### Arguments:
None

#### Returns:
True when the gyro is calibrating

#### Examples:
# start calibration\
gyro1.calibrate()\
# wait for completion\
while gyro1.is_calibrating():\
sleep(50, MSEC)

<a id="vex.Gyro.changed"></a>

#### changed

```python
def changed(callback: Callable[..., None], arg: tuple = ())
```

### Register a function to be called when the value of the gyro heading changes

#### Arguments:
callback : A function that will be called when the value of the gyro heading changes
arg (optional) : A tuple that is used to pass arguments to the callback function.

#### Returns:
An instance of the Event class

#### Examples:
def foo():
print("gyro changed")

gyro1.changed(foo)

<a id="vex.Gyro.reset_heading"></a>

#### reset\_heading

```python
def reset_heading()
```

### Reset the gyro heading to 0

#### Arguments:
None

#### Returns:
None

<a id="vex.Gyro.reset_rotation"></a>

#### reset\_rotation

```python
def reset_rotation()
```

### Reset the gyro rotation to 0

#### Arguments:
None

#### Returns:
None

<a id="vex.Gyro.set_heading"></a>

#### set\_heading

```python
def set_heading(value: vexnumber, units=RotationUnits.DEG)
```

### set the gyro heading to a new value

The new value for heading should be in the range 0 - 359.99 degrees.

#### Arguments:
value : The new value to use for heading.
units (optional) : The rotation units type for value, the default is DEGREES

#### Returns:
None

#### Examples:
# set the value of heading to 180 degrees\
gyro1.set_heading(180)

<a id="vex.Gyro.heading"></a>

#### heading

```python
def heading(units=RotationUnits.DEG)
```

### read the current heading of the gyro

heading will be returned in the range 0 - 359.99 degrees

#### Arguments:
units (optional) : The units to return the heading in, default is DEGREES

#### Returns:
A value for heading in the range that is specified by the units.

#### Examples:
# get the current heading for the gyro\
value = gyro1.heading()

<a id="vex.Gyro.set_rotation"></a>

#### set\_rotation

```python
def set_rotation(value, units=RotationUnits.DEG)
```

### set the gyro rotation to a new value

#### Arguments:
value : The new value to use for rotation.
units (optional) : The rotation units type for value, the default is DEGREES

#### Returns:
None

#### Examples:
# set the value of rotation to 180 degrees\
gyro1.set_rotation(180)

<a id="vex.Gyro.rotation"></a>

#### rotation

```python
def rotation(units=RotationUnits.DEG)
```

### read the current rotation of the gyro

rotation is not limited, it can be both positive and negative and shows the absolute angle of the gyro.

#### Arguments:
units (optional) : The units to return the rotation in, default is DEGREES

#### Returns:
A value for heading in the range that is specified by the units.

#### Examples:
# get the current rotation for the gyro\
value = gyro1.rotation()

<a id="vex.Gyro.set_turn_type"></a>

#### set\_turn\_type

```python
def set_turn_type(turntype: TurnType.TurnType)
```

### set the direction that returns positive values for heading

An advanced function that is not generally used.

#### Arguments:
turntype : TurnType.LEFT or TurnType.RIGHT

#### Returns:
None

<a id="vex.Gyro.get_turn_type"></a>

#### get\_turn\_type

```python
def get_turn_type()
```

### get the direction that returns positive values for heading

An advanced function that is not generally used.

#### Arguments:
None

#### Returns:
The current TurnType, LEFT or RIGHT

<a id="vex.Accelerometer"></a>

## Accelerometer Objects

```python
class Accelerometer()
```

### Accelerometer class - create a new accelerometer

For full functionality, three Accelerometer instances would need to be created, one for each axis.

#### Arguments:
port : The 3wire port to use for the accelerometer
sensitivity (optional) : set high sensitivity mode (+/- 2G), use True or 1

#### Returns:
An instance of the Accelerometer class

#### Examples:
accx = Accelerometer(brain.three_wire_port.a)\
accy = Accelerometer(brain.three_wire_port.b)\
accz = Accelerometer(brain.three_wire_port.c)

<a id="vex.Accelerometer.value"></a>

#### value

```python
def value(units: AnalogPercentUnits = AnalogUnits.TWELVEBIT)
```

### The current value of the accelerometer

#### Arguments:
units (optional) : A valid AnalogUnits type or PERCENT, the default is 12 bit analog

#### Returns:
A value in the range that is specified by the units.

#### Examples:
# get accelerometer in range 0 - 4095\
value = accz.value()

# get accelerometer in range 0 - 1023\
value = accz.value(AnalogUnits.TENBIT)

<a id="vex.Accelerometer.acceleration"></a>

#### acceleration

```python
def acceleration()
```

### The current value of the accelerometer scaled to units of gravity

#### Arguments:
None

#### Returns:
A value in the range +/- 6 or +/-2G if high sensitivity mode is set

#### Examples:
# get accelerometer in range+/- 6G
value = accz.acceleration()

<a id="vex.Accelerometer.changed"></a>

#### changed

```python
def changed(callback: Callable[..., None], arg: tuple = ())
```

### Register a function to be called when the value of the accelerometer changes

#### Arguments:
callback : A function that will be called when the value of the accelerometer changes
arg (optional) : A tuple that is used to pass arguments to the callback function.

#### Returns:
An instance of the Event class

#### Examples:
def foo():
print("accelerometer changed")

accz.changed(foo)

<a id="vex.AnalogIn"></a>

## AnalogIn Objects

```python
class AnalogIn()
```

### AnalogIn class - create a new analog input

#### Arguments:
port : The 3wire port to use for the analog input

#### Returns:
An instance of the AnalogIn class

#### Examples:
ana1 = AnalogIn(brain.three_wire_port.a)

<a id="vex.AnalogIn.value"></a>

#### value

```python
def value(units: AnalogPercentUnits = AnalogUnits.TWELVEBIT)
```

### The current value of the analog input

#### Arguments:
units (optional) : A valid AnalogUnits type or PERCENT, the default is 12 bit analog

#### Returns:
A value in the range that is specified by the units.

#### Examples:
# get analog input in range 0 - 4095\
value = ana1.value()

# get analog input in range 0 - 1023\
value = ana1.value(AnalogUnits.TENBIT)

<a id="vex.AnalogIn.changed"></a>

#### changed

```python
def changed(callback: Callable[..., None], arg: tuple = ())
```

### Register a function to be called when the value of the analog input changes

#### Arguments:
callback : A function that will be called when the value of the analog input changes
arg (optional) : A tuple that is used to pass arguments to the callback function.

#### Returns:
An instance of the Event class

#### Examples:
def foo():
print("analog input changed")

ana1.changed(foo)

<a id="vex.Encoder"></a>

## Encoder Objects

```python
class Encoder()
```

### Encoder class - create a new encoder sensor

An encoder uses two adjacent 3wire ports.\
valid port pairs are a/b, c/d, e/f and g/h

#### Arguments:
port : The 3wire port to use for the encoder sensor

#### Returns:
An instance of the Encoder class

#### Examples:
enc1 = Encoder(brain.three_wire_port.a)

<a id="vex.Encoder.value"></a>

#### value

```python
def value()
```

### The current value of the encoder in raw counts

One full turn of the encoder is 360 counts.

#### Arguments:
None

#### Returns:
A value for encoder counts.

#### Examples:
# get encoder raw counts\
value = enc1.value()

<a id="vex.Encoder.reset_position"></a>

#### reset\_position

```python
def reset_position()
```

### Reset the encoder position to 0

#### Arguments:
None

#### Returns:
None

<a id="vex.Encoder.set_position"></a>

#### set\_position

```python
def set_position(value, units=RotationUnits.DEG)
```

### set the encoder position to a new value

#### Arguments:
value : The new value to use for position.
units (optional) : The rotation units type for value, the default is DEGREES

#### Returns:
None

#### Examples:
# set the value of position to 180 degrees\
enc1.set_position(180)

<a id="vex.Encoder.position"></a>

#### position

```python
def position(units=RotationUnits.DEG)
```

### The current position of the encoder

#### Arguments:
units (optional) : The rotation units to return the position value in, default is DEGREES.

#### Returns:
A value for encoder position in the specified units.

#### Examples:
# get encoder position\
value = enc1.position()

<a id="vex.Encoder.velocity"></a>

#### velocity

```python
def velocity(units: VelocityPercentUnits = VelocityUnits.RPM)
```

### The current velocity of the encoder

#### Arguments:
units (optional) : The velocity units to return the value in, default is RPM.

#### Returns:
A value for encoder velocity in the specified units.

#### Examples:
# get encoder velocity in rpm\
value = enc1.velocity()

<a id="vex.Sonar"></a>

## Sonar Objects

```python
class Sonar()
```

### Sonar class - create a new sonar (ultrasonic) sensor

A sonar uses two adjacent 3wire ports.\
valid port pairs are a/b, c/d, e/f and g/h\
connect the wire labeled "output" to the lower 3wire port, eg. a

#### Arguments:
port : The 3wire port to use for the sonar sensor

#### Returns:
An instance of the Sonar class

#### Examples:
sonar1 = Sonar(brain.three_wire_port.a)

<a id="vex.Sonar.value"></a>

#### value

```python
def value(units: AnalogPercentUnits = AnalogUnits.TWELVEBIT)
```

### The current value of the sonar

This method has no practical use, see distance.

#### Arguments:
units (optional) : A valid AnalogUnits type or PERCENT, the default is 12 bit analog

#### Returns:
A value in the range that is specified by the units.

#### Examples:
# get sonar raw value\
value = sonar1.value()

<a id="vex.Sonar.distance"></a>

#### distance

```python
def distance(units: DistanceUnits.DistanceUnits)
```

### The current distance the sonar is detecting an object at.

The sonar will return a large positive number if no object is detected in range.

#### Arguments:
units : The distance units to return the position value in.

#### Returns:
A value for sonar distance in the specified units.

#### Examples:
# get sonar distance in mm\
value = sonar1.distance(MM)

<a id="vex.Sonar.found_object"></a>

#### found\_object

```python
def found_object()
```

### Check for an object in the range 0 - 1000mm

The sonar will return True if an object is detected closer than 1000mm.

#### Arguments:
None

#### Returns:
True of an object is detected.

#### Examples:
# is an object closer than 1000mm\
if sonar1.found_object():\
print("object found")

<a id="vex.Pwm"></a>

## Pwm Objects

```python
class Pwm()
```

### Pwm class - create a new pwm output

The pwm class will create raw RC style pwm waveform.\
A pwm output of 0% corresponds to pulse width of 1.5mS every 16mS\
A pwm output of 100% corresponds to pulse width of 2mS\
A pwm output of -100% corresponds to pulse width of 1mS

#### Arguments:
port : The 3wire port to use for the pwm output

#### Returns:
An instance of the Pwm class

#### Examples:
pwm1 = Pwm(brain.three_wire_port.a)

<a id="vex.Pwm.value"></a>

#### value

```python
def value()
```

### Read the current PWM value in percent.

#### Arguments:
None

#### Returns:
A value in the range -100 to +100 percent.

#### Examples:
# get pwm1 current value\
value = pwm1.value()

<a id="vex.Pwm.state"></a>

#### state

```python
def state(value, units=PercentUnits.PERCENT)
```

### Set the current PWM value in percent.

#### Arguments:
value : The new value for pwm output, -100 to +100 percent.
units (optional) : units must be specified in PERCENT

#### Returns:
None

#### Examples:
# set pwm1 output to 50%\
pwm1.state(50)

<a id="vex.Servo"></a>

## Servo Objects

```python
class Servo()
```

### Servo class - create a new servo output

The Servo class will create raw RC style pwm waveform.\
An output of 0 corresponds to pulse width of 1.5mS every 16mS\
An output of 50 degrees corresponds to pulse width of 2mS\
An output of -50 degrees corresponds to pulse width of 1mS

#### Arguments:
port : The 3wire port to use for the servo output

#### Returns:
An instance of the Servo class

#### Examples:
servo1 = Servo(brain.three_wire_port.a)

<a id="vex.Servo.value"></a>

#### value

```python
def value()
```

### Read the current raw servo pwm value.

This is the raw internal pwm value\
A servo position of 0 will return 127\
A maximum positive servo position will return 255

#### Arguments:
None

#### Returns:
A value in the range 0 to 255.

#### Examples:
# get servo1 current value\
value = servo1.value()

<a id="vex.Servo.set_position"></a>

#### set\_position

```python
def set_position(value, units: RotationPercentUnits = RotationUnits.DEG)
```

### Set the servo position

#### Arguments:
value : The new value for the servo using the supplied units.
units (optional) : The rotation units, default is PERCENT

#### Returns:
None

#### Examples:
# set servo output to 10 degrees\
servo1.set_position(10, DEGREES)

<a id="vex.Motor29"></a>

## Motor29 Objects

```python
class Motor29()
```

### Motor29 class - create a new pwm motor output

The Motor29 class will create raw RC style pwm waveform.\
This is primarily for use with the VEX MC29 motor controller\
To minimize current draw, new values sent to the motor will have slew rate control applied

#### Arguments:
port : The 3wire port to use for the motor controller
reverse_flag (optional) : set reverse flag for this motor, spin commands will cause opposite rotation if set True.  default is False.

#### Returns:
An instance of the Motor29 class

#### Examples:
motor1 = Motor29(brain.three_wire_port.a)

<a id="vex.Motor29.value"></a>

#### value

```python
def value()
```

### Read the current raw motor controller pwm value.

This is the raw internal pwm value\
A motor velocity of 0 will return 127\
A maximum positive motor velocity will return 255

#### Arguments:
None

#### Returns:
A value in the range 0 to 255.

#### Examples:
# get motor current pwm value\
value = motor1.value()

<a id="vex.Motor29.set_velocity"></a>

#### set\_velocity

```python
def set_velocity(value, units: VelocityPercentUnits = VelocityUnits.RPM)
```

### Set default velocity for the motor
This will be the velocity used for subsequent calls to spin of a velocity is not provided
to that function.

#### Arguments:
value : The new velocity
units : The units for the supplied velocity, the default is RPM

#### Returns:
None

<a id="vex.Motor29.set_reversed"></a>

#### set\_reversed

```python
def set_reversed(value)
```

### Set the reversed flag for the motor

#### Arguments:
value : 1, 0, True or False

#### Returns:
None

#### Examples:
# set motor reversed flag True\
motor1.set_reversed(True)

<a id="vex.Motor29.spin"></a>

#### spin

```python
def spin(direction: DirectionType.DirectionType, velocity=None, units=None)
```

### Spin the motor using the provided arguments

The motor is assumed to have a maximum velocity of 100 rpm.

#### Arguments:
direction : The direction to spin the motor, FORWARD or REVERSE
velocity (optional) : spin the motor using this velocity, the default velocity set by set_velocity will be used if not provided.
units (optional) : The units of the provided velocity, default is RPM

#### Returns:
None

#### Examples:
# spin motor forward at velocity set with set_velocity\
motor1.spin(FORWARD)

# spin motor forward at 50 rpm\
motor1.spin(FORWARD, 50)

# spin with negative velocity, ie. backwards\
motor1.spin(FORWARD, -20)

# spin motor forwards with 100% velocity\
motor1.spin(FORWARD, 100, PERCENT)

# spin motor forwards at 50 rpm\
motor1.spin(FORWARD, 50, RPM)

# spin motor forwards at 360 dps\
motor1.spin(FORWARD, 360.0, VelocityUnits.DPS)

<a id="vex.Motor29.stop"></a>

#### stop

```python
def stop()
```

### Stop the  motor, set to 0 velocity

#### Arguments:
None

#### Returns:
None

<a id="vex.MotorVictor"></a>

## MotorVictor Objects

```python
class MotorVictor()
```

### MotorVictor class - create a new pwm motor output

The MotorVictor class will create raw RC style pwm waveform.\
This is primarily for use with the VEX Victor motor controller\

#### Arguments:
port : The 3wire port to use for the motor controller
reverse_flag (optional) : set reverse flag for this motor, spin commands will cause opposite rotation if set True.  default is False.

#### Returns:
An instance of the MotorVictor class

#### Examples:
motor1 = MotorVictor(brain.three_wire_port.a)

<a id="vex.MotorVictor.value"></a>

#### value

```python
def value()
```

### Read the current raw motor controller pwm value.

This is the raw internal pwm value\
A motor velocity of 0 will return 127\
A maximum positive motor velocity will return 255

#### Arguments:
None

#### Returns:
A value in the range 0 to 255.

#### Examples:
# get motor current pwm value\
value = motor1.value()

<a id="vex.MotorVictor.set_velocity"></a>

#### set\_velocity

```python
def set_velocity(value, units: VelocityPercentUnits = VelocityUnits.RPM)
```

### Set default velocity for the motor
This will be the velocity used for subsequent calls to spin of a velocity is not provided
to that function.

#### Arguments:
value : The new velocity
units : The units for the supplied velocity, the default is RPM

#### Returns:
None

<a id="vex.MotorVictor.set_reversed"></a>

#### set\_reversed

```python
def set_reversed(value)
```

### Set the reversed flag for the motor

#### Arguments:
value : 1, 0, True or False

#### Returns:
None

#### Examples:
# set motor reversed flag True\
motor1.set_reversed(True)

<a id="vex.MotorVictor.spin"></a>

#### spin

```python
def spin(direction, velocity=None, units=None)
```

### Spin the motor using the provided arguments

The motor is assumed to have a maximum velocity of 100 rpm.

#### Arguments:
direction : The direction to spin the motor, FORWARD or REVERSE
velocity (optional) : spin the motor using this velocity, the default velocity set by set_velocity will be used if not provided.
units (optional) : The units of the provided velocity, default is RPM

#### Returns:
None

#### Examples:
# spin motor forward at velocity set with set_velocity\
motor1.spin(FORWARD)

# spin motor forward at 50 rpm\
motor1.spin(FORWARD, 50)

# spin with negative velocity, ie. backwards\
motor1.spin(FORWARD, -20)

# spin motor forwards with 100% velocity\
motor1.spin(FORWARD, 100, PERCENT)

# spin motor forwards at 50 rpm\
motor1.spin(FORWARD, 50, RPM)

# spin motor forwards at 360 dps\
motor1.spin(FORWARD, 360.0, VelocityUnits.DPS)

<a id="vex.MotorVictor.stop"></a>

#### stop

```python
def stop()
```

### Stop the  motor, set to 0 velocity

#### Arguments:
None

#### Returns:
None

<a id="vex.Vision"></a>

## Vision Objects

```python
class Vision()
```

### Vision class - a class for working with the vision sensor

#### Arguments:
port : The smartport this device is attached to
brightness (optional) : set the brightness value for the vision sensor
sigs (optional) : one or more signature objects

#### Returns:
An instance of the Vision class

#### Examples:
SIG_1 = Signature(1, 6035, 7111, 6572, -1345, -475, -910, 3.000, 0)\
vision1 = Vision(Ports.PORT1, 50, SIG_1)

<a id="vex.Vision.installed"></a>

#### installed

```python
def installed()
```

### Check for device connection

#### Arguments:
None

#### Returns:
True or False

<a id="vex.Vision.timestamp"></a>

#### timestamp

```python
def timestamp()
```

### Request the timestamp of last received message from the vision sensor

#### Arguments:
None

#### Returns:
timestamp of the last status packet in mS

<a id="vex.Vision.take_snapshot"></a>

#### take\_snapshot

```python
def take_snapshot(index, count=1)
```

### Request the vision sensor to filter latest objects to match signature or code

#### Arguments:
index : A signature, code or signature id.
count (optional) : the maximum number of objects to obtain.  default is 1.

#### Returns:
tuple of VisionObject or None if nothing is available

#### Examples:
# look for and return 1 object matching SIG_1\
objects = vision1.take_snapshot(SIG_1)

# look for and return a maximum of 4 objects matching SIG_1\
objects = vision1.take_snapshot(SIG_1, 4)

<a id="vex.VisionObject"></a>

## VisionObject Objects

```python
class VisionObject()
```

A vision object, not instantiated by user programs

<a id="vex.Signature"></a>

## Signature Objects

```python
class Signature()
```

### Signature class - a class for holding vision sensor signatures

#### Arguments:
index : The signature index
p0 : signature value p0
p1 : signature value p1
p2 : signature value p2
p3 : signature value p3
p4 : signature value p4
p5 : signature value p5
sigrange : signature range
sigtype : signature type

#### Returns:
An instance of the Signature class

#### Examples:
SIG_1 = Signature(1, 6035, 7111, 6572, -1345, -475, -910, 3.000, 0)\
vision1 = Vision(Ports.PORT1, 50, SIG_1)

<a id="vex.Signature.id"></a>

#### id

```python
def id()
```

Not used, always returns 0

<a id="vex.Code"></a>

## Code Objects

```python
class Code()
```

### Code class - a class for holding vision sensor codes

A vision code is a collection of up to five vision signatures.
#### Arguments:
sig1 : A vision signature
sig2 : A vision signature
sig3 (optional) : A vision signature
sig4 (optional) : A vision signature
sig5 (optional) : A vision signature

#### Returns:
An instance of the Signature class

#### Examples:
SIG_1 = Signature(1, 6035, 7111, 6572, -1345, -475, -910, 3.000, 0)\
SIG_2 = Signature(2, 6035, 7111, 6572, -1345, -475, -910, 3.000, 0)\
C1 = Code(SIG_1, SIG_2)

<a id="vex.Code.id"></a>

#### id

```python
def id()
```

Not used, always returns 0

<a id="vex.MessageLink"></a>

## MessageLink Objects

```python
class MessageLink()
```

### MessageLink class - a class for communicating using VEXlink

#### Arguments:
port : The smartport the VEXlink radio is attached to
name : The name of this link
linktype : The type of this link, either VexlinkType.MANAGER or VexlinkType.WORKER
wired (optional) : Set to True if this is a wired link

#### Returns:
An instance of the MessageLink class

#### Examples:
link = MessageLink(Ports.PORT1, 'james', VexlinkType.MANAGER)

<a id="vex.MessageLink.installed"></a>

#### installed

```python
def installed()
```

### Check for device connection

#### Arguments:
None

#### Returns:
True or False

<a id="vex.MessageLink.is_linked"></a>

#### is\_linked

```python
def is_linked()
```

### Return link status

#### Arguments:
None

#### Returns:
True if the link is active and connected to the paired brain.

<a id="vex.MessageLink.send"></a>

#### send

```python
def send(message: str, *args)
```

### Send a message with optional parameters

#### Arguments:
message : A string, the message to send
index (optional) : A int such as port number
value (optional) : A float

#### Returns:
length of transmitted data or None on error

#### Examples:
# send the message 'test' with no parameters\
link.send('test')

# send the message 'test' with parameters\
link.send('test', 1, 3.14)

<a id="vex.MessageLink.receive"></a>

#### receive

```python
def receive(timeout=300000)
```

### Receive the next message

#### Arguments:
timeout (optional) : An optional timeout value in mS before the function returns.

#### Returns:
None or received message

#### Examples:
message = link.receive()

<a id="vex.MessageLink.received"></a>

#### received

```python
def received(*args)
```

### Register a function to be called when a message is received

If the message is omitted then the callback will be called for all messages.

#### Arguments:
message (optional) : A message name for which the callback will be called
callback : A function that will be called when a message is received

#### Returns:
None

#### Examples:
def cb(message, link, index, value):
print(link, message, index, value)

link.received('test', cb)

<a id="vex.SerialLink"></a>

## SerialLink Objects

```python
class SerialLink()
```

### SerialLink class - a class for communicating using VEXlink

#### Arguments:
port : The smartport the VEXlink radio is attached to
name : The name of this link
linktype : The type of this link, either VexlinkType.MANAGER or VexlinkType.WORKER
wired (optional) : Set to True if this is a wired link

#### Returns:
An instance of the SerialLink class

#### Examples:
link = SerialLink(Ports.PORT1, 'james', VexlinkType.MANAGER)

<a id="vex.SerialLink.installed"></a>

#### installed

```python
def installed()
```

### Check for device connection

#### Arguments:
None

#### Returns:
True or False

<a id="vex.SerialLink.is_linked"></a>

#### is\_linked

```python
def is_linked()
```

### Return link status

#### Arguments:
None

#### Returns:
True if the link is active and connected to the paired brain.

<a id="vex.SerialLink.send"></a>

#### send

```python
def send(buffer)
```

### Send a buffer of length length

#### Arguments:
buffer : A string or bytearray, the message to send

#### Returns:
None

#### Examples:
# send the string 'test'\
link.send('test')

# send the bytearray 'test' with parameters\
link.send('test', 1, 3.14)

<a id="vex.SerialLink.receive"></a>

#### receive

```python
def receive(length, timeout=300000)
```

### Receive data in the serial link

#### Arguments:
length : maximum amount of data to wait for
timeout (optional) : An optional timeout value in mS before the function returns.

#### Returns:
None or bytearray with data

#### Examples:
# wait for 128 bytes of data for 1000mS\
buffer = link.receive(128, 1000)

<a id="vex.SerialLink.received"></a>

#### received

```python
def received(callback: Callable[..., None])
```

### Register a function to be called when data is received

This will receive a bytearray and a length indicating how much

#### Arguments:
callback : A function that will be called when data is received

#### Returns:
None

#### Examples:
def cb(buffer, length):
print(buffer, length)

link.received(cb)

<a id="vex.Rotation"></a>

## Rotation Objects

```python
class Rotation()
```

### Rotation class - a class for working with the rotation sensor

#### Arguments:
port : The smartport this device is attached to
reverse (optional) : set to reverse the angle and position returned by the sensor.

#### Returns:
An instance of the Rotation class

#### Examples:
rot1 = Rotation(Ports.PORT1)\
rot2 = Rotation(Ports.PORT2, True)

<a id="vex.Rotation.installed"></a>

#### installed

```python
def installed()
```

### Check for device connection

#### Arguments:
None

#### Returns:
True or False

<a id="vex.Rotation.timestamp"></a>

#### timestamp

```python
def timestamp()
```

### Request the timestamp of last received message from the sensor

#### Arguments:
None

#### Returns:
timestamp of the last status packet in mS

<a id="vex.Rotation.set_reversed"></a>

#### set\_reversed

```python
def set_reversed(value)
```

### Set the reversed flag for the sensor

Usually this would be done in the constructor.

#### Arguments:
value : 1, 0, True or False

#### Returns:
None

#### Examples:
# set reversed flag True\
rot1.set_reversed(True)

<a id="vex.Rotation.angle"></a>

#### angle

```python
def angle(units=RotationUnits.DEG)
```

### The current angle of the rotation sensor

#### Arguments:
units (optional) : A valid RotationUnits type, the default is DEGREES

#### Returns:
A value in the range that is specified by the units.

#### Examples:
# get rotation sensor angle            angle = rot1.angle()

<a id="vex.Rotation.reset_position"></a>

#### reset\_position

```python
def reset_position()
```

### Reset the rotation sensor position to 0

#### Arguments:
None

#### Returns:
None

<a id="vex.Rotation.set_position"></a>

#### set\_position

```python
def set_position(value, units=RotationUnits.DEG)
```

### Set the current position of the rotation sensor
The position returned by the position() function is set to this value.

The position is an absolute value that continues to increase or decrease as the\
sensor is rotated.

#### Arguments:
value : The new position
units : The units for the provided position, the default is DEGREES

#### Returns:
None

<a id="vex.Rotation.position"></a>

#### position

```python
def position(units=RotationUnits.DEG)
```

### Returns the position of the rotation sensor

The position is an absolute value that continues to increase or decrease as the\
sensor is rotated.

#### Arguments:
units (optional) : The units for the returned position, the default is DEGREES

#### Returns:
The rotation sensor in provided units

<a id="vex.Rotation.velocity"></a>

#### velocity

```python
def velocity(units=VelocityUnits.RPM)
```

### Returns the velocity of the rotation sensor

#### Arguments:
units (optional) : The units for the returned velocity, the default is RPM

#### Returns:
The rotation sensor velocity in provided units

<a id="vex.Rotation.changed"></a>

#### changed

```python
def changed(callback: Callable[..., None], arg: tuple = ())
```

### Register a function to be called when the value of the rotation sensor changes

#### Arguments:
callback : A function that will be called when the value of the rotation sensor changes
arg (optional) : A tuple that is used to pass arguments to the callback function.

#### Returns:
An instance of the Event class

#### Examples:
def foo():
print("rotation changed")

rot1.changed(foo)

<a id="vex.Optical"></a>

## Optical Objects

```python
class Optical()
```

### Optical class - a class for working with the optical sensor

#### Arguments:
port : The smartport this device is attached to

#### Returns:
An instance of the Optical class

#### Examples:
opt1 = Optical(Ports.PORT1)

<a id="vex.Optical.installed"></a>

#### installed

```python
def installed()
```

### Check for device connection

#### Arguments:
None

#### Returns:
True or False

<a id="vex.Optical.timestamp"></a>

#### timestamp

```python
def timestamp()
```

### Request the timestamp of last received message from the sensor

#### Arguments:
None

#### Returns:
timestamp of the last status packet in mS

<a id="vex.Optical.hue"></a>

#### hue

```python
def hue()
```

### read the hue value from the optical sensor

#### Arguments:
None

#### Returns:
hue as a float in the range 0 - 359.99 degrees

#### Examples:
hue = opt1.hue()

<a id="vex.Optical.brightness"></a>

#### brightness

```python
def brightness(readraw=False)
```

### read the brightness value from the optical sensor

#### Arguments:
readraw (optional) : return raw brightness value if True rather than percentage.

#### Returns:
brightness as a float in the range 0 - 100%

#### Examples:
brightness = opt1.brightness()

<a id="vex.Optical.color"></a>

#### color

```python
def color()
```

### read the color from the optical sensor

#### Arguments:
None

#### Returns:
color as an instance of the Color class

#### Examples:
c = opt1.color()

<a id="vex.Optical.is_near_object"></a>

#### is\_near\_object

```python
def is_near_object()
```

### check to see if the optical proximity sensor detects an object

#### Arguments:
None

#### Returns:
True if near an object

#### Examples:
if opt1.is_near_object():
print('near object')

<a id="vex.Optical.set_light"></a>

#### set\_light

```python
def set_light(*args)
```

### set optical sensor led on or of

#### Arguments:
value : LedStateType.ON, LedStateType.OFF or power of led, 0 to 100%

#### Returns:
None

#### Examples:
# turn on led with previous intensity\
opt1.set_light(LedStateType.ON)

# turn on led with new intensity\
opt1.set_light(65)

<a id="vex.Optical.set_light_power"></a>

#### set\_light\_power

```python
def set_light_power(value: vexnumber)
```

### set optical sensor led to the requested power

#### Arguments:
value : power of led, 0 to 100%

#### Returns:
None

#### Examples:
opt1.set_light_power(50)

<a id="vex.Optical.integration_time"></a>

#### integration\_time

```python
def integration_time(value: vexnumber = -1)
```

### set optical sensor led to the requested power

#### Arguments:
value (optional) : integration time in mS (5 to 700)

#### Returns:
The current integration time

#### Examples:
opt1.set_light_power(50)

<a id="vex.Optical.rgb"></a>

#### rgb

```python
def rgb(raw=False)
```

### get the optical sensor rgb value

#### Arguments:
raw (optional) : return raw or processed values

#### Returns:
A tuple with red, green, blue and brightness

#### Examples:
value=opt1.rgb()

<a id="vex.Optical.object_detect_threshold"></a>

#### object\_detect\_threshold

```python
def object_detect_threshold(value: vexnumber)
```

### set the threshold for object detection

#### Arguments:
value : Number in the range 0 to 255.  A value of 0 will just return current value.

#### Returns:
current value

#### Examples:
opt1.object_detect_threshold(100)

<a id="vex.Optical.gesture_enable"></a>

#### gesture\_enable

```python
def gesture_enable()
```

### Enable gesture mode

#### Arguments:
None

#### Returns:
None

#### Examples:
opt1.gesture_enable()

<a id="vex.Optical.gesture_disable"></a>

#### gesture\_disable

```python
def gesture_disable()
```

### Disable gesture mode

#### Arguments:
None

#### Returns:
None

#### Examples:
opt1.gesture_disable()

<a id="vex.Optical.get_gesture"></a>

#### get\_gesture

```python
def get_gesture(newobject=False)
```

### get gesture data

#### Arguments:
newobject (optional) : create a new Gesture object to return data in

#### Returns:
An object with the last gesture data

#### Examples:
opt1.gesture_disable()

<a id="vex.Optical.object_detected"></a>

#### object\_detected

```python
def object_detected(callback: Callable[..., None], arg: tuple = ())
```

### Register a function to be called when an object detected event occurs

#### Arguments:
callback : A function that will be called when an object detected event occurs
arg (optional) : A tuple that is used to pass arguments to the callback function.

#### Returns:
An instance of the Event class

#### Examples:
def foo():
print("object detected")

opt1.object_detected(foo)

<a id="vex.Optical.object_lost"></a>

#### object\_lost

```python
def object_lost(callback: Callable[..., None], arg: tuple = ())
```

### Register a function to be called when an object lost event occurs

#### Arguments:
callback : A function that will be called when an object lost event occurs
arg (optional) : A tuple that is used to pass arguments to the callback function.

#### Returns:
An instance of the Event class

#### Examples:
def foo():
print("object lost")

opt1.object_lost(foo)

<a id="vex.Optical.gesture_up"></a>

#### gesture\_up

```python
def gesture_up(callback: Callable[..., None], arg: tuple = ())
```

### Register a function to be called when a gesture up event is detected

gesture must be enabled for events to fire.

#### Arguments:
callback : A function that will be called when a gesture up event is detected
arg (optional) : A tuple that is used to pass arguments to the callback function.

#### Returns:
An instance of the Event class

#### Examples:
def foo():
print("up detected")

opt1.gesture_up(foo)

<a id="vex.Optical.gesture_down"></a>

#### gesture\_down

```python
def gesture_down(callback: Callable[..., None], arg: tuple = ())
```

### Register a function to be called when a gesture down event is detected

gesture must be enabled for events to fire.

#### Arguments:
callback : A function that will be called when a gesture down event is detected
arg (optional) : A tuple that is used to pass arguments to the callback function.

#### Returns:
An instance of the Event class

#### Examples:
def foo():
print("down detected")

opt1.gesture_down(foo)

<a id="vex.Optical.gesture_left"></a>

#### gesture\_left

```python
def gesture_left(callback: Callable[..., None], arg: tuple = ())
```

### Register a function to be called when a gesture left event is detected

gesture must be enabled for events to fire.

#### Arguments:
callback : A function that will be called when a gesture left event is detected
arg (optional) : A tuple that is used to pass arguments to the callback function.

#### Returns:
An instance of the Event class

#### Examples:
def foo():
print("left detected")

opt1.gesture_left(foo)

<a id="vex.Optical.gesture_right"></a>

#### gesture\_right

```python
def gesture_right(callback: Callable[..., None], arg: tuple = ())
```

### Register a function to be called when a gesture right event is detected

gesture must be enabled for events to fire.

#### Arguments:
callback : A function that will be called when a gesture right event is detected
arg (optional) : A tuple that is used to pass arguments to the callback function.

#### Returns:
An instance of the Event class

#### Examples:
def foo():
print("right detected")

opt1.gesture_right(foo)

<a id="vex.Distance"></a>

## Distance Objects

```python
class Distance()
```

### Distance class - a class for working with the distance sensor

#### Arguments:
port : The smartport this device is attached to

#### Returns:
An instance of the Distance class

#### Examples:
dist1 = Distance(Ports.PORT1)

<a id="vex.Distance.installed"></a>

#### installed

```python
def installed()
```

### Check for device connection

#### Arguments:
None

#### Returns:
True or False

<a id="vex.Distance.timestamp"></a>

#### timestamp

```python
def timestamp()
```

### Request the timestamp of last received message from the sensor

#### Arguments:
None

#### Returns:
timestamp of the last status packet in mS

<a id="vex.Distance.object_distance"></a>

#### object\_distance

```python
def object_distance(units=DistanceUnits.MM)
```

### The current distance the sensor is reading.

The distance will return a large positive number if no object is detected.

#### Arguments:
units (optional): The distance units to return the distance value in.  default is MM.

#### Returns:
A value for distance in the specified units.

#### Examples:
# get distance in mm\
value = dist1.object_distance()

# get distance in inches\
value = dist1.object_distance(INCHES)

<a id="vex.Distance.object_size"></a>

#### object\_size

```python
def object_size()
```

### Get an estimation of the object size the sensor is detecting.

#### Arguments:
None

#### Returns:
A value for object size.\
The value will be of type ObjectSizeType

#### Examples:
# get object size\
size = dist1.object_size()

<a id="vex.Distance.object_rawsize"></a>

#### object\_rawsize

```python
def object_rawsize()
```

### Get the raw value of object size the sensor is detecting.

Raw size will be a number ranging from 0 to about 400\
Larger and more reflective objects will return larger values.

#### Arguments:
None

#### Returns:
A value for object size that is a number.\

#### Examples:
# get object raw size\
size = dist1.object_rawsize()

<a id="vex.Distance.object_velocity"></a>

#### object\_velocity

```python
def object_velocity()
```

### Returns the object velocity

velocity is calculated from change of distance over time

#### Arguments:
None

#### Returns:
The velocity in m/s

<a id="vex.Distance.is_object_detected"></a>

#### is\_object\_detected

```python
def is_object_detected()
```

### Returns if an object is detected

#### Arguments:
None

#### Returns:
True or False

<a id="vex.Distance.changed"></a>

#### changed

```python
def changed(callback: Callable[..., None], arg: tuple = ())
```

### Register a function to be called when the distance value changes

#### Arguments:
callback : A function that will be called when the distance value changes
arg (optional) : A tuple that is used to pass arguments to the callback function.

#### Returns:
An instance of the Event class

#### Examples:
def foo():
print("distance changed")

dist1.changed(foo)

<a id="vex.Electromagnet"></a>

## Electromagnet Objects

```python
class Electromagnet()
```

### Electromagnet class - a class for working with the electromagnet

#### Arguments:
port : The smartport this device is attached to

#### Returns:
An instance of the Electromagnet class

#### Examples:
em1 = Electromagnet(Ports.PORT1)

<a id="vex.Electromagnet.installed"></a>

#### installed

```python
def installed()
```

### Check for device connection

#### Arguments:
None

#### Returns:
True or False

<a id="vex.Electromagnet.timestamp"></a>

#### timestamp

```python
def timestamp()
```

### Request the timestamp of last received message from the sensor

#### Arguments:
None

#### Returns:
timestamp of the last status packet in mS

<a id="vex.Electromagnet.set_power"></a>

#### set\_power

```python
def set_power(value)
```

### set the default power to use for drop and pickup methods

#### Arguments:
value : power in range 0 to 100

#### Returns:
None

#### Examples:
# set default power to 80\
em1.set_power(80)

<a id="vex.Electromagnet.pickup"></a>

#### pickup

```python
def pickup(duration=1000, units=MSEC, power=50)
```

### energize the electromagnet to pickup objects

#### Arguments:
duration (optional) : the duration to energize the magnet for, default is 1 second
units (optional) : the units for duration, default is MSEC
power (optional) : the power used when energizing.

#### Returns:
None

#### Examples:
# pickup with default values\
em1.pickup()

# pickup with custom values\
em1.pickup(250, MSEC, 90)

<a id="vex.Electromagnet.drop"></a>

#### drop

```python
def drop(duration=1000, units=MSEC, power=50)
```

### energize the electromagnet to drop objects

#### Arguments:
duration (optional) : the duration to energize the magnet for, default is 1 second
units (optional) : the units for duration, default is MSEC
power (optional) : the power used when energizing.

#### Returns:
None

#### Examples:
# drop with default values\
em1.drop()

# drop with custom values\
em1.drop(250, MSEC, 90)

<a id="vex.Electromagnet.temperature"></a>

#### temperature

```python
def temperature(*args)
```

### Returns the temperature of the electromagnet

#### Arguments:
units (optional) : The units for the returned temperature, the default is CELSIUS

#### Returns:
The electromagnet temperature in provided units

<a id="vex.AddressableLed"></a>

## AddressableLed Objects

```python
class AddressableLed()
```

### Addressable led class

#### Arguments:
port : The 3wire port to use for the addressable led strip

#### Returns:
An instance of the AddressableLed class

#### Examples:
addr1 = AddressableLed(brain.three_wire_port.a)

<a id="vex.AddressableLed.clear"></a>

#### clear

```python
def clear()
```

### clear all addressable led to off

#### Arguments:
None

#### Returns:
None

#### Examples:
addr1.clear()

<a id="vex.AddressableLed.set"></a>

#### set

```python
def set(data: AddressableLedList, offset: vexnumber = 0)
```

### Set the addressable led strip to provided values

#### Arguments:
data : An list of Color values
offset (optional) : index of led to start at, 0 based

#### Returns:
None

#### Examples:
addr1 = AddressableLed(brain.three_wire_port.a)\
pix = [Color(0x800000),Color(0x008000),Color(0x000080)]\
addr1.set(pix)

<a id="vex.MotorGroup"></a>

## MotorGroup Objects

```python
class MotorGroup()
```

### MotorGroup class - use this to create a group of motors

#### Arguments:
One or more Motor class instances

#### Returns:
A new MotorGroup object.

#### Examples:
motor1 = Motor(Ports.PORT1)\
motor2 = Motor(Ports.PORT2)\
mg1 = MotorGroup(motor1, motor2)

<a id="vex.MotorGroup.count"></a>

#### count

```python
def count()
```

### return the number of motors in the group

#### Arguments:
None

#### Returns:
The number of motors in the group

<a id="vex.MotorGroup.set_velocity"></a>

#### set\_velocity

```python
def set_velocity(velocity, units=None)
```

### Set default velocity for all motors in the group
This will be the velocity used for subsequent calls to spin if a velocity is not provided
to that function.

#### Arguments:
velocity : The new velocity
units : The units for the supplied velocity, the default is RPM

#### Returns:
None

<a id="vex.MotorGroup.set_stopping"></a>

#### set\_stopping

```python
def set_stopping(mode=BrakeType.COAST)
```

### Set the stopping mode for all motors in the group
Setting the action for the motor when stopped.

#### Arguments:
mode : The stopping mode, COAST, BRAKE or HOLD

#### Returns:
None

<a id="vex.MotorGroup.reset_position"></a>

#### reset\_position

```python
def reset_position()
```

### Reset the motor position to 0 for all motors in the group

#### Arguments:
None

#### Returns:
None

<a id="vex.MotorGroup.set_position"></a>

#### set\_position

```python
def set_position(value, units=None)
```

### Set the current position for all motors in the group
The position returned by the position() function is set to this value.

#### Arguments:
value : The new position
units : The units for the provided position, the default is DEGREES

#### Returns:
None

<a id="vex.MotorGroup.set_timeout"></a>

#### set\_timeout

```python
def set_timeout(timeout, units=TimeUnits.MSEC)
```

### Set the timeout value used for all motors in the group
The timeout value is used when performing spin_to_position and spin_for commands.  If timeout is
reached and the motor has not completed moving, then the spin... function will return False.

#### Arguments:
timeout : The new timeout
units : The units for the provided timeout, the default is MSEC

#### Returns:
None

<a id="vex.MotorGroup.spin"></a>

#### spin

```python
def spin(direction,
         velocity=None,
         units: VelocityPercentUnits = VelocityUnits.RPM)
```

### Spin all motors in the group using the provided arguments

#### Arguments:
direction : The direction to spin the motor, FORWARD or REVERSE
velocity (optional) : spin the motor using this velocity, the default velocity set by set_velocity will be used if not provided.
units (optional) : The units of the provided velocity, default is RPM

#### Returns:
None

#### Examples:
# spin motors forward at velocity set with set_velocity\
mg1.spin(FORWARD)

# spin motors forward at 50 rpm\
mg1.spin(FORWARD, 50)

# spin with negative velocity, ie. backwards\
mg1.spin(FORWARD, -20)

# spin motors forwards with 100% velocity\
mg1.spin(FORWARD, 100, PERCENT)

# spin motors forwards at 50 rpm\
mg1.spin(FORWARD, 50, RPM)

# spin motors forwards at 360 dps\
mg1.spin(FORWARD, 360.0, VelocityUnits.DPS)

<a id="vex.MotorGroup.spin_to_position"></a>

#### spin\_to\_position

```python
def spin_to_position(rotation,
                     units=RotationUnits.DEG,
                     velocity=None,
                     units_v: VelocityPercentUnits = VelocityUnits.RPM,
                     wait=True)
```

### Spin all motors in the group to an absolute position using the provided arguments
Move the motor to the requested position.\
This function supports keyword arguments.

#### Arguments:
rotation : The position to spin the motor to
units (optional) : The units for the provided position, the default is DEGREES
velocity (optional) : spin the motor using this velocity, the default velocity set by set_velocity will be used if not provided.
units_v (optional) : The units of the provided velocity, default is RPM
wait (optional) : This indicates if the function should wait for the command to complete or return immediately, default is True.

#### Returns:
None

#### Examples:
# spin to 180 degrees\
mg1.spin_to_position(180)

# spin to 2 TURNS (revolutions)\
mg1.spin_to_position(2, TURNS)

# spin to 180 degrees at 25 rpm\
mg1.spin_to_position(180, DEGREES, 25, RPM)

# spin to 180 degrees and do not wait for completion\
mg1.spin_to_position(180, DEGREES, False)

# spin to 180 degrees and do not wait for completion\
mg1.spin_to_position(180, DEGREES, wait=False)

<a id="vex.MotorGroup.spin_for"></a>

#### spin\_for

```python
def spin_for(direction,
             rotation,
             units: RotationTimeUnits = RotationUnits.DEG,
             velocity=None,
             units_v: VelocityPercentUnits = VelocityUnits.RPM,
             wait=True)
```

### Spin all motors in the group to a relative position using the provided arguments
Move the motor to the requested position or for the specified amount of time.\
The position is relative (ie. an offset) to the current position\
This function supports keyword arguments.

#### Arguments:
direction : The direction to spin the motor, FORWARD or REVERSE
rotation : The relative position to spin the motor to or tha amount of time to spin for
units (optional) : The units for the provided position or time, the default is DEGREES or MSEC
velocity (optional) : spin the motor using this velocity, the default velocity set by set_velocity will be used if not provided.
units_v (optional) : The units of the provided velocity, default is RPM
wait (optional) : This indicates if the function should wait for the command to complete or return immediately, default is True.

#### Returns:
None

#### Examples:
# spin 180 degrees from the current position\
mg1.spin_for(FORWARD, 180)

# spin reverse 2 TURNS (revolutions) from the current position\
mg1.spin_for(REVERSE, 2, TURNS)

# spin 180 degrees from the current position at 25 rpm\
mg1.spin_for(FORWARD, 180, DEGREES, 25, RPM)

# spin 180 degrees  from the current position and do not wait for completion\
mg1.spin_for(FORWARD, 180, DEGREES, False)

# spin 180 degrees  from the current position and do not wait for completion\
mg1.spin_for(FORWARD, 180, DEGREES, wait=False)

<a id="vex.MotorGroup.is_spinning"></a>

#### is\_spinning

```python
def is_spinning()
```

### Returns the current status of the spin_to_position or spin_for command
This function is used when False has been passed as the wait parameter to spin_to_position or spin_for\
It will return True if any motor is still spinning or False if they have completed the move or a timeout occurred.

#### Arguments:
None

#### Returns:
The current spin_to_position or spin_for status

<a id="vex.MotorGroup.is_done"></a>

#### is\_done

```python
def is_done()
```

### Returns the current status of the spin_to_position or spin_for command
This function is used when False has been passed as the wait parameter to spin_to_position or spin_for\
It will return False if any motor is still spinning or True if they have completed the move or a timeout occurred.

#### Arguments:
None

#### Returns:
The current spin_to_position or spin_for status

<a id="vex.MotorGroup.stop"></a>

#### stop

```python
def stop(mode=None)
```

### Stop all motors in the group, set to 0 velocity and set current stopping_mode
The motor will be stopped and set to COAST, BRAKE or HOLD

#### Arguments:
None

#### Returns:
None

<a id="vex.MotorGroup.set_max_torque"></a>

#### set\_max\_torque

```python
def set_max_torque(value, units: TorquePercentCurrentUnits = TorqueUnits.NM)
```

### Set the maximum torque all motors in the group will use
The torque can be set as torque, current or percent of maximum.

#### Arguments:
value : the new maximum torque to use
units : the units that value is passed in

#### Returns:
None

#### Examples:
# set maximum torque to 2 Nm\
motor1.set_max_torque(2, TorqueUnits.NM)

# set maximum torque to 1 Amp\
motor1.set_max_torque(1, CurrentUnits.AMP)

# set maximum torque to 20 percent\
motor1.set_max_torque(20, PERCENT)

<a id="vex.MotorGroup.direction"></a>

#### direction

```python
def direction()
```

### Returns the current direction the first motor is spinning in

#### Arguments:
None

#### Returns:
The spin direction, FORWARD, REVERSE or UNDEFINED

<a id="vex.MotorGroup.position"></a>

#### position

```python
def position(units=RotationUnits.DEG)
```

### Returns the position of the first motor

#### Arguments:
units (optional) : The units for the returned position, the default is DEGREES

#### Returns:
The motor position in provided units

<a id="vex.MotorGroup.velocity"></a>

#### velocity

```python
def velocity(units: VelocityPercentUnits = VelocityUnits.RPM)
```

### Returns the velocity of the first motor

#### Arguments:
units (optional) : The units for the returned velocity, the default is RPM

#### Returns:
The motor velocity in provided units

<a id="vex.MotorGroup.current"></a>

#### current

```python
def current(units=CurrentUnits.AMP)
```

### Returns the total current all motors are using

#### Arguments:
units (optional) : The units for the returned current, the default is AMP

#### Returns:
The motor current in provided units

<a id="vex.MotorGroup.power"></a>

#### power

```python
def power(units=PowerUnits.WATT)
```

### Returns the power the first motor is providing

#### Arguments:
units (optional) : The units for the returned power, the default is WATT

#### Returns:
The motor power in provided units

<a id="vex.MotorGroup.torque"></a>

#### torque

```python
def torque(units: TorquePercentCurrentUnits = TorqueUnits.NM)
```

### Returns the torque the first motor is providing

#### Arguments:
units (optional) : The units for the returned torque, the default is NM

#### Returns:
The motor torque in provided units

<a id="vex.MotorGroup.efficiency"></a>

#### efficiency

```python
def efficiency(units=PercentUnits.PERCENT)
```

### Returns the efficiency of the first motor

#### Arguments:
units (optional) : The units for the efficiency, the only valid value is PERCENT

#### Returns:
The motor efficiency in percent

<a id="vex.MotorGroup.temperature"></a>

#### temperature

```python
def temperature(units=TemperatureUnits.CELSIUS)
```

### Returns the temperature of the first motor

#### Arguments:
units (optional) : The units for the returned temperature, the default is CELSIUS

#### Returns:
The motor temperature in provided units

<a id="vex.DriveTrain"></a>

## DriveTrain Objects

```python
class DriveTrain()
```

### DriveTrain class - use this to create a simple drivetrain

#### Arguments:
lm : Left motor or motorgroup
rm : Right motor or motorgroup
wheelTravel (optional) : The circumference of the driven wheels, default is 300 mm
trackWidth (optional) : The trackwidth of the drivetrain, default is 320 mm
wheelBase (optional) : The wheelBase of the drivetrain, default is 320 mm
units (optional) : The units that wheelTravel, trackWidth and wheelBase are specified in, default is MM.
externalGearRatio (optional) : An optional gear ratio used to compensate drive distances if gearing is used.

#### Returns:
A new DriveTrain object.

#### Examples:
# A simple two motor drivetrain using default values\
motor1 = Motor(Ports.PORT1)\
motor2 = Motor(Ports.PORT2, True)\
drive1 = DriveTrain(motor1, motor2)

# A four motor drivetrain using custom values\
motor1 = Motor(Ports.PORT1)\
motor2 = Motor(Ports.PORT2)\
motor3 = Motor(Ports.PORT3, True)\
motor4 = Motor(Ports.PORT4, True)\
mgl = MotorGroup(motor1, motor3)\
mgr = MotorGroup(motor2, motor4)\
drive1 = DriveTrain(mgl, mgr, 8.6, 10, 12, INCHES)

<a id="vex.DriveTrain.set_drive_velocity"></a>

#### set\_drive\_velocity

```python
def set_drive_velocity(velocity,
                       units: VelocityPercentUnits = VelocityUnits.RPM)
```

### Set default velocity for drive commands
This will be the velocity used for subsequent calls to drive if a velocity is not provided
to that function.

#### Arguments:
velocity : The new velocity
units : The units for the supplied velocity, the default is RPM

#### Returns:
None

<a id="vex.DriveTrain.set_turn_velocity"></a>

#### set\_turn\_velocity

```python
def set_turn_velocity(velocity,
                      units: VelocityPercentUnits = VelocityUnits.RPM)
```

### Set default velocity for turn commands
This will be the velocity used for subsequent calls to turn if a velocity is not provided
to that function.

#### Arguments:
velocity : The new velocity
units : The units for the supplied velocity, the default is RPM

#### Returns:
None

<a id="vex.DriveTrain.set_stopping"></a>

#### set\_stopping

```python
def set_stopping(mode=BrakeType.COAST)
```

### Set the stopping mode for all motors on the drivetrain
Setting the action for the motors when stopped.

#### Arguments:
mode : The stopping mode, COAST, BRAKE or HOLD

#### Returns:
None

<a id="vex.DriveTrain.set_timeout"></a>

#### set\_timeout

```python
def set_timeout(timeout, units=TimeUnits.MSEC)
```

### Set the timeout value used all motors on the drivetrain
The timeout value is used when performing drive_for and turn_for commands.  If timeout is
reached and the motor has not completed moving, then the function will return False.

#### Arguments:
timeout : The new timeout
units : The units for the provided timeout, the default is MSEC

#### Returns:
None

<a id="vex.DriveTrain.get_timeout"></a>

#### get\_timeout

```python
def get_timeout()
```

### Get the current timeout value used by the drivetrain

#### Arguments:
None

#### Returns:
Timeout value in mS

<a id="vex.DriveTrain.drive"></a>

#### drive

```python
def drive(direction,
          velocity=None,
          units: VelocityPercentUnits = VelocityUnits.RPM)
```

### drive the drivetrain using the provided arguments

The drive command is similar to the motor spin command.\
all drive motors are commanded using the provided parameters.

#### Arguments:
direction : The direction to drive, FORWARD or REVERSE
velocity (optional) : spin the motors using this velocity, the default velocity set by set_velocity will be used if not provided.
units (optional) : The units of the provided velocity, default is RPM

#### Returns:
None

#### Examples:
# drive forward at velocity set with set_velocity\
drive1.drive(FORWARD)

# drive forward at 50 rpm\
drive1.drive(FORWARD, 50)

# drive with negative velocity, ie. backwards\
drive1.drive(FORWARD, -20)

# drive forwards with 100% velocity\
drive1.drive(FORWARD, 100, PERCENT)

# drive forwards at 50 rpm\
drive1.drive(FORWARD, 50, RPM)

# drive forwards at 360 dps\
drive1.drive(FORWARD, 360.0, VelocityUnits.DPS)

<a id="vex.DriveTrain.drive_for"></a>

#### drive\_for

```python
def drive_for(direction,
              distance,
              units=DistanceUnits.IN,
              velocity=None,
              units_v: VelocityPercentUnits = VelocityUnits.RPM,
              wait=True)
```

### move the drivetrain using the provided arguments

The drive_for command is similar to the motor spin_for command,\
however, the drivetrain is commanded to move a distance.

#### Arguments:
direction : The direction to drive
distance : The distance to drive
units (optional) : The units for the provided distance, the default is INCHES
velocity (optional) : drive using this velocity, the default velocity set by set_drive_velocity will be used if not provided.
units_v (optional) : The units of the provided velocity, default is RPM
wait (optional) : This indicates if the function should wait for the command to complete or return immediately, default is True.

#### Returns:
None or if wait is True then completion success or failure

#### Examples:
# drive forward 10 inches from the current position\
drive1.drive_for(FORWARD, 10, INCHES)

# drive reverse 1000mm from the current position with motors at 50 rpm\
drive1.drive_for(REVERSE, 10000, MM, 50, RPM)

<a id="vex.DriveTrain.turn"></a>

#### turn

```python
def turn(direction,
         velocity=None,
         units: VelocityPercentUnits = VelocityUnits.RPM)
```

### turn the drivetrain using the provided arguments

The drive command is similar to the motor spin command.\
all drive motors are commanded using the provided parameters.

#### Arguments:
direction : The turn direction, LEFT or RIGHT
velocity (optional) : spin the motors using this velocity, the default velocity set by set_turn_velocity will be used if not provided.
units (optional) : The units of the provided velocity, default is RPM

#### Returns:
None

#### Examples:
# turn left at velocity set with set_turn_velocity\
drive1.turn(LEFT)

# drive right at 50 rpm\
drive1.turn(RIGHT, 50)

# turn right with 100% velocity\
drive1.turn(RIGHT, 100, PERCENT)

# turn right at 50 rpm\
drive1.turn(RIGHT, 50, RPM)

# turn right at 360 dps\
drive1.turn(RIGHT, 360.0, VelocityUnits.DPS)

<a id="vex.DriveTrain.turn_for"></a>

#### turn\_for

```python
def turn_for(direction,
             angle,
             units=RotationUnits.DEG,
             velocity=None,
             units_v: VelocityPercentUnits = VelocityUnits.RPM,
             wait=True)
```

### turn the drivetrain using the provided arguments

The turn_for command is similar to the motor spin_for command,\
however, the drivetrain is commanded to turn a specified angle.

#### Arguments:
direction : The direction to turn, LEFT or RIGHT
angle : The angle to turn
units (optional) : The units for the provided angle, the default is DEGREES
velocity (optional) : drive using this velocity, the default velocity set by set_drive_velocity will be used if not provided.
units_v (optional) : The units of the provided velocity, default is RPM
wait (optional) : This indicates if the function should wait for the command to complete or return immediately, default is True.

#### Returns:
None or if wait is True then completion success or failure

#### Examples:
# turn right 90 degrees\
drive1.turn_for(RIGHT, 90, DEGREES)

# turn left 180 degrees with motors at 50 rpm\
drive1.turn_for(LEFT, 180, DEGREES, 50, RPM)

<a id="vex.DriveTrain.is_moving"></a>

#### is\_moving

```python
def is_moving()
```

### Returns the current status of the drive_for or turn_for command
This function is used when False has been passed as the wait parameter to drive_for or turn_for\
It will return True if the drivetrain is still moving or False if it has completed the move or a timeout occurred.

#### Arguments:
None

#### Returns:
The current drive_for or turn_for status

<a id="vex.DriveTrain.is_done"></a>

#### is\_done

```python
def is_done()
```

### Returns the current status of the drive_for or turn_for command
This function is used when False has been passed as the wait parameter to drive_for or turn_for\
It will return False if the drivetrain is still moving or True if it has completed the move or a timeout occurred.

#### Arguments:
None

#### Returns:
The current drive_for or turn_for status

<a id="vex.DriveTrain.stop"></a>

#### stop

```python
def stop(mode=None)
```

### Stop the drivetrain, set to 0 velocity and set current stopping_mode
The motors will be stopped and set to COAST, BRAKE or HOLD

#### Arguments:
None

#### Returns:
None

<a id="vex.DriveTrain.velocity"></a>

#### velocity

```python
def velocity(units: VelocityPercentUnits = VelocityUnits.RPM)
```

### Returns average velocity of the left and right motors

#### Arguments:
units (optional) : The units for the returned velocity, the default is RPM

#### Returns:
The drivetrain velocity in provided units

<a id="vex.DriveTrain.current"></a>

#### current

```python
def current(units=CurrentUnits.AMP)
```

### Returns the total current all drivetrain motors are using

#### Arguments:
units (optional) : The units for the returned current, the default is AMP

#### Returns:
The drivetrain current in provided units

<a id="vex.DriveTrain.power"></a>

#### power

```python
def power(units=PowerUnits.WATT)
```

### Returns the total power all drivetrain motors are using

This command only considers the first motor for left and right sides of the drive.

#### Arguments:
units (optional) : The units for the returned power, the default is WATT

#### Returns:
The drivetrain power in provided units

<a id="vex.DriveTrain.torque"></a>

#### torque

```python
def torque(units=TorqueUnits.NM)
```

### Returns the total torque all drivetrain motors are using

This command only considers the first motor for left and right sides of the drive.

#### Arguments:
units (optional) : The units for the returned torque, the default is NM

#### Returns:
The motor torque in provided units

<a id="vex.DriveTrain.efficiency"></a>

#### efficiency

```python
def efficiency(units=PercentUnits.PERCENT)
```

### Returns the average efficiency of the left and right motors

This command only considers the first motor for left and right sides of the drive.

#### Arguments:
units (optional) : The units for the efficiency, the only valid value is PERCENT

#### Returns:
The motor efficiency in percent

<a id="vex.DriveTrain.temperature"></a>

#### temperature

```python
def temperature(units=TemperatureUnits.CELSIUS)
```

### Returns the average temperature of the left and right motors

This command only considers the first motor for left and right sides of the drive.

#### Arguments:
units (optional) : The units for the returned temperature, the default is CELSIUS

#### Returns:
The motor temperature in provided units

<a id="vex.SmartDrive"></a>

## SmartDrive Objects

```python
class SmartDrive(DriveTrain)
```

### SmartDrive class - use this to create a smart drivetrain

A smart drivetrain uses a gyro or similar sensor to turn more accurately.\
The smartdrive inherits all drivetrain functions.

#### Arguments:
lm : Left motor or motorgroup
rm : Right motor or motorgroup
g : The gyro, inertial sensor or gps to use for turns
wheelTravel (optional) : The circumference of the driven wheels, default is 300 mm
trackWidth (optional) : The trackwidth of the drivetrain, default is 320 mm
wheelBase (optional) : The wheelBase of the drivetrain, default is 320 mm
units (optional) : The units that wheelTravel, trackWidth and wheelBase are specified in, default is MM.
externalGearRatio (optional) : An optional gear ratio used to compensate drive distances if gearing is used.

#### Returns:
A new SmartDrive object.

#### Examples:
# A simple two motor smart drivetrain using default values\
motor1 = Motor(Ports.PORT1)\
motor2 = Motor(Ports.PORT2, True)\
imu1 = Inertial(Ports.PORT9)\
smart1 = SmartDrive(motor1, motor2, imu1)

# A four motor smart drivetrain using custom values\
motor1 = Motor(Ports.PORT1)\
motor2 = Motor(Ports.PORT2)\
motor3 = Motor(Ports.PORT3, True)\
motor4 = Motor(Ports.PORT4, True)\
imu1 = Inertial(Ports.PORT9)\
mgl = MotorGroup(motor1, motor3)\
mgr = MotorGroup(motor2, motor4)\
smart1 = SmartDrive(mgl, mgr, imu1, 8.6, 10, 12, INCHES)

<a id="vex.SmartDrive.set_turn_threshold"></a>

#### set\_turn\_threshold

```python
def set_turn_threshold(value)
```

### Set the turning threshold for the smartdrive

This is the threshold value used to determine that turns are complete.\
If this is too large then turns will not be accurate, if too small then turns ma\
not complete.

#### Arguments:
value : The new turn threshold in degrees, the default for a smartdrive is 1 degree

#### Returns:
None

<a id="vex.SmartDrive.set_turn_constant"></a>

#### set\_turn\_constant

```python
def set_turn_constant(value)
```

### Set the turning constant for the smartdrive

The smartdrive uses a simple P controller when doing turns.\
This constant, generally known as kp, is the gain used in the equation that\
turns angular error into motor velocity.

#### Arguments:
value : The new turn constant in the range 0.1 - 4.0, the default is 1.0

#### Returns:
None

<a id="vex.SmartDrive.set_turn_direction_reverse"></a>

#### set\_turn\_direction\_reverse

```python
def set_turn_direction_reverse(value)
```

### Set the expected turn direction for positive heading change

#### Arguments:
value : True or False

#### Returns:
None

<a id="vex.SmartDrive.set_heading"></a>

#### set\_heading

```python
def set_heading(value, units=RotationUnits.DEG)
```

### set the smartdrive heading to a new value

The new value for heading should be in the range 0 - 359.99 degrees.

#### Arguments:
value : The new value to use for heading.
units (optional) : The rotation units type for value, the default is DEGREES

#### Returns:
None

#### Examples:
# set the value of heading to 180 degrees\
smart1.set_heading(180)

<a id="vex.SmartDrive.heading"></a>

#### heading

```python
def heading(units=RotationUnits.DEG)
```

### read the current heading of the smartdrive

heading will be returned in the range 0 - 359.99 degrees

#### Arguments:
units (optional) : The units to return the heading in, default is DEGREES

#### Returns:
A value for heading in the range that is specified by the units.

#### Examples:
# get the current heading for the smartdrive\
value = smart1.heading()

<a id="vex.SmartDrive.set_rotation"></a>

#### set\_rotation

```python
def set_rotation(value, units=RotationUnits.DEG)
```

### set the smartdrive rotation to a new value

#### Arguments:
value : The new value to use for rotation.
units (optional) : The rotation units type for value, the default is DEGREES

#### Returns:
None

#### Examples:
# set the value of rotation to 180 degrees\
smart1.set_rotation(180)

<a id="vex.SmartDrive.rotation"></a>

#### rotation

```python
def rotation(units=RotationUnits.DEG)
```

### read the current rotation of the smartdrive

rotation is not limited, it can be both positive and negative and shows the absolute angle of the gyro.

#### Arguments:
units (optional) : The units to return the rotation in, default is DEGREES

#### Returns:
A value for heading in the range that is specified by the units.

#### Examples:
# get the current rotation for the smartdrive\
value = smart1.rotation()

<a id="vex.SmartDrive.turn_to_heading"></a>

#### turn\_to\_heading

```python
def turn_to_heading(angle,
                    units=RotationUnits.DEG,
                    velocity=None,
                    units_v: VelocityPercentUnits = VelocityUnits.RPM,
                    wait=True)
```

### turn the smartdrive to an absolute position using the provided arguments

The turn_to_heading command is similar to the motor spin_to_position command,\
however, the smartdrive is commanded to turn to a specified angle.\
This function uses the value of heading() when turning the smartdrive\
This function supports keyword arguments.

#### Arguments:
angle : The angle to turn to
units (optional) : The units for the provided angle, the default is DEGREES
velocity (optional) : spin the motor using this velocity, the default velocity set by set_velocity will be used if not provided.
units_v (optional) : The units of the provided velocity, default is RPM
wait (optional) : This indicates if the function should wait for the command to complete or return immediately, default is True.

#### Returns:
None

#### Examples:
# turn to heading 180 degrees\
smart1.turn_to_heading(180)

# turn to heading 180 degrees at 25 rpm\
smart1.turn_to_heading(180, DEGREES, 25, RPM)

# turn to heading 180 degrees and do not wait for completion\
smart1.turn_to_heading(180, DEGREES, False)

# turn to heading 180 degrees and do not wait for completion\
smart1.turn_to_heading(180, DEGREES, wait=False)

<a id="vex.SmartDrive.turn_to_rotation"></a>

#### turn\_to\_rotation

```python
def turn_to_rotation(angle,
                     units=RotationUnits.DEG,
                     velocity=None,
                     units_v: VelocityPercentUnits = VelocityUnits.RPM,
                     wait=True)
```

### turn the smartdrive to an absolute position using the provided arguments

The turn_to_rotation command is similar to the motor spin_to_position command,\
however, the smartdrive is commanded to turn to a specified angle.\
This function uses the value of rotation() when turning the smartdrive\
This function supports keyword arguments.

#### Arguments:
angle : The angle to turn to
units (optional) : The units for the provided angle, the default is DEGREES
velocity (optional) : spin the motor using this velocity, the default velocity set by set_velocity will be used if not provided.
units_v (optional) : The units of the provided velocity, default is RPM
wait (optional) : This indicates if the function should wait for the command to complete or return immediately, default is True.

#### Returns:
None

#### Examples:
# turn to rotation 180 degrees\
smart1.turn_to_rotation(180)

# turn to rotation 400 degrees at 25 rpm\
smart1.turn_to_rotation(400, DEGREES, 25, RPM)

# turn to rotation 180 degrees and do not wait for completion\
smart1.turn_to_rotation(180, DEGREES, False)

# turn to rotation 180 degrees and do not wait for completion\
smart1.turn_to_rotation(180, DEGREES, wait=False)

<a id="vex.SmartDrive.turn_for"></a>

#### turn\_for

```python
def turn_for(direction,
             angle,
             units=RotationUnits.DEG,
             velocity=None,
             units_v: VelocityPercentUnits = VelocityUnits.RPM,
             wait=True)
```

### turn the smartdrive using the provided arguments

The turn_for command is similar to the motor spin_for command,\
however, the smartdrive is commanded to turn a specified angle.

#### Arguments:
direction : The direction to turn, LEFT or RIGHT
angle : The angle to turn
units (optional) : The units for the provided angle, the default is DEGREES
velocity (optional) : drive using this velocity, the default velocity set by set_drive_velocity will be used if not provided.
units_v (optional) : The units of the provided velocity, default is RPM
wait (optional) : This indicates if the function should wait for the command to complete or return immediately, default is True.

#### Returns:
None or if wait is True then completion success or failure

#### Examples:
# turn right 90 degrees\
smart1.turn_for(RIGHT, 90, DEGREES)

# turn left 180 degrees with motors at 50 rpm\
smart1.turn_for(LEFT, 180, DEGREES, 50, RPM)

<a id="vex.SmartDrive.is_turning"></a>

#### is\_turning

```python
def is_turning()
```

### Returns the current status of the turn_to_heading, turn_to_rotation or turn_for command
This function is used when False has been passed as the wait parameter to turn_to_heading or turn_for\
It will return True if the drivetrain is still moving or False if it has completed the move or a timeout occurred.

#### Arguments:
None

#### Returns:
The current turn_to_heading, turn_to_rotation or turn_for status

<a id="vex.SmartDrive.is_moving"></a>

#### is\_moving

```python
def is_moving()
```

### Returns the current status of the drive_for command
This function is used when False has been passed as the wait parameter to drive_for\
It will return True if the drivetrain is still moving or False if it has completed the move or a timeout occurred.

#### Arguments:
None

#### Returns:
The current drive_for status

