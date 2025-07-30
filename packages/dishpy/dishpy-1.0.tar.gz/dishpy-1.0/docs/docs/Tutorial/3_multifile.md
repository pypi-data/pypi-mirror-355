# 3. Using multi-file capabilities in DishPy

As your robot programs grow, organizing code into multiple files makes development easier. DishPy automatically combines all your files into a single program for the V5 brain.

## Example: Simple Multi-File Robot

Let's split our robot code into logical modules:

### Project Structure

```
my-robot/
├── dishpy.toml
├── src/
│   ├── main.py
│   ├── motors.py
│   └── vex/
└── .out/
```

### Motor Module (`src/motors.py`)

```python
import vex

left_motor = vex.Motor(vex.Ports.PORT1)
right_motor = vex.Motor(vex.Ports.PORT2, True)

def drive_forward():
    left_motor.spin(vex.FORWARD, 50, vex.PERCENT)
    right_motor.spin(vex.FORWARD, 50, vex.PERCENT)

def stop():
    left_motor.stop()
    right_motor.stop()
```

### Main Program (`src/main.py`)

```python
import vex
from motors import drive_forward, stop

brain = vex.Brain()

brain.screen.print("Multi-file robot!")
drive_forward()
vex.wait(2, vex.SECONDS)
stop()
brain.screen.print("Done!")
```

## Building

```bash
uvx dishpy mu
```

DishPy will combine both files into `.out/main.py` and upload to your brain.

## Benefits

- **Organization**: Related code stays together
- **Reusability**: Share motor functions across projects
- **Team work**: Multiple people can work on different files
- **Single deployment**: V5 brain still gets one optimized file

The amalgamation process handles all imports and ensures your multi-file project works exactly the same as a single file would.
