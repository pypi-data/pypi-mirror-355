[![Upload Python Package](https://github.com/isaac1000000/turtlebyte/actions/workflows/python-publish.yml/badge.svg)](https://github.com/isaac1000000/turtlebyte/actions/workflows/python-publish.yml)
# turtlebyte.py

Turtlebyte is a thing I did for fun. It uses Python's turtle module to store memory by drawing it on your screen. I plan to use it for some silly things in the future.

## Installation

`pip install turtlebyte --upgrade`

## Usage

First, instantiate a Turtlebyte object:

``` Python
from turtlebyte import Turtlebyte
tb = Turtlebyte()
```

There are two main operations you'll use in turtlebyte:

`write_bytes(address: bytes, data: bytes) -> bool`

- Writes the bytes of data at the given address

- Args:
    - address (bytes): The address to write at
    - data (bytes): The data to write
- Returns: 
    - bool: True if write operation is successful 

`read_bytes(address: bytes, num_bytes: int) -> bytes`
    
- Reads the data at given address

- Args:
    - address(bytes): The address to start reading from
    - num_bytes(int): The number of bytes to read
- Returns:
    - bytes: The bytes found at the address

## Configuration

All configuration is passed to the initial `Turtlebyte` object. Optional settings (which you will most likely have to experiment with) and their defaults are:

- `turtle_pen_size: 10`
- `turtle_speed: 1000` (turtle has a maximum speed)
- `turtle_screensize_x: 600`
- `turtle_screensize_y: 600`
- `turtle_window_buffer: 2`
    - This is the automatic border that comes with the `tkinter` canvas. On my device it's 2 pixels
- `show_animation: False`
    - If this is enabled, the turtle will move across your screen as it writes or reads. It's slow, so I prefer to leave this off and just set a low refresh interval
- `refresh_interval: 10`
    - This is the number of bytes between screen updates in `write_bytes` and `read_bytes`
- `grid_width: 2`
    - The number of columns in the grid of data blocks
- `grid_height`
    - The number of rows in the grid of data blocks


## Example Usage

``` Python
from turtlebyte import Turtlebyte

tb = Turtlebyte(
    show_animation = True,
    turtle_pen_size = 15,
    turtle_speed = 20,
    grid_width = 2,
    grid_height = 2
)

msg = b'Hello world!'

tb.write_bytes(b'\x00', msg)

print(tb.read_bytes(b'\x00', len(msg)))

input()
```

Note that the program does not stay open automatically after it has reached the end of its lifespan, thus the `input()` call.

## Random Notes, for Those Interested

The default block size is 32 by 16 bytes for 512 bytes.  I have yet to experiment with other block sizes. You are welcome to, but no promises.

The blocks do not affect the way data is processed, it's entirely for effect.

Each cell is one byte. If you don't feel like slowing down the animation to see what's going on, the byte is 4 bits wide and 2 bits tall. The 8 bits are written top left to top right, down, then bottom right to bottom left.

Cells are written top left to bottom left in the block, then top to bottom on the next column until the block is full.

Blocks are written top left to bottom left, then top to bottom on the next column until the grid is full.