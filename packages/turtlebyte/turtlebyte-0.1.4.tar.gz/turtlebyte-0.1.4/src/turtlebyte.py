"""
A silly little program that illustrates (literally!) the basic outline of a
computer memory.

This is not reliable, fast, or really much of anything other than a fun
little project. Enjoy!

author: isaac1000000
"""

import turtle as t
from utils import normalize, detection

class Turtlebyte():

    # HIGHLY experimental. Don't change these unless you've got some big ideas...
    BLOCK_SIZE = (16, 32) # (width, height) in bytes
    BLOCK_GAP = 4 # number of pen size units to leave between blocks in the grid
    CELL_GAP = 0 # number of pen size units between cells in a block
    BYTE_ORDER = 'little'

    def read_bytes(self, address:bytes, num_bytes: int) -> bytes:
        """
        Reads a specific number of bytes at a given address

        Args:
            address (bytes): the address to begin reading
            num_bytes (int): the number of bytes to read
        Returns:
            bytes: the bytes found at the given address
        """

        normalized_address = self.normalizer.address_to_pos(address)
        t.setpos(normalized_address)
        t.seth(0)

        result = b''
        for cell in range(num_bytes):
            new_address = int.from_bytes(address, self.BYTE_ORDER) + cell
            if new_address % self.BLOCK_SIZE[1] == 0:
                normalized_address = self.normalizer.address_to_pos(new_address.to_bytes(self.address_length, self.BYTE_ORDER))
                t.setpos(normalized_address)
                t.seth(0)
            result += self.read_byte()

            if cell % self.refresh_interval == 0:
                self.screen.update()

            self._l()
            self._f(self.CELL_GAP + 1)
            t.seth(0)

        self.screen.update()

        return result



    def read_byte(self) -> bytes:
        """
        Reads a byte at the current address in memory

        Returns:
            bytes: the byte found at the current address.
        """

        byte = self._read_nibble()
        byte = byte << 4
        self._r()
        self._f()
        self._r()
        byte += self._read_nibble()

        return byte.to_bytes(1, self.BYTE_ORDER)


    def _read_nibble(self) -> int:
        """
        An internal function that returns an int from the current nibble

        Returns:
            int: the int found at the current nibble
        """

        result = 0
        for i in range(3):
            result = result << 1
            if self.detector.marked():
                result += 1
            self._f()
        result = result << 1
        if self.detector.marked():
            result += 1
        return result

    def write_bytes(self, address: bytes, data: bytes) -> bool:
        """
        Writes bytes at a specific address in the memory.

        WARNING: This is not secure! It can very easily overwrite
        old memory.
        
        Args:
            address (bytes): the address to write the bytes at
            data (bytes): the byte-format data to be written

        Returns:
            bool: True if write is successful
        """

        normalized_address = self.normalizer.address_to_pos(address)
        t.setpos(normalized_address)
        t.seth(0)
        
        for cell, byte in enumerate(data):
            new_address = int.from_bytes(address, self.BYTE_ORDER) + cell
            if new_address % self.BLOCK_SIZE[1] == 0:
                normalized_address = self.normalizer.address_to_pos(new_address.to_bytes(self.address_length, self.BYTE_ORDER))
                t.setpos(normalized_address)
                t.seth(0)

            if self.write_byte(byte.to_bytes(1, self.BYTE_ORDER)) == False:
                return False
            
            if cell % self.refresh_interval == 0:
                self.screen.update()

            self._l()
            self._f(self.CELL_GAP + 1)
            self._l()
        
        self.screen.update()

        return True

    def write_byte(self, data: bytes) -> bool:
        """
        Writes a byte at the current address in memory

        Args:
            data (bytes): the byte to write at address.

        Returns:
            bool: True if write is successful, otherwise False.
        """
        assert isinstance(data, bytes), "Invalid operation: attempt to write non-bytes object"
        assert len(data) == 1, "Invalid operation: attempt to write more or less than one byte"

        bit_array = [int.from_bytes(data, self.BYTE_ORDER) & 2**i != 0 for i in range(7, -1, -1)] # endian-ness does not matter here b/c one byte

        try:
            self._write_nibble_at_current(bit_array[:4])
        except Exception:
            return False
        
        # Move down a row to continue writing the byte
        self._r()
        self._f()
        self._r()

        try:
            self._write_nibble_at_current(bit_array[4:])
        except Exception:
            return False

        return True


    def _write_nibble_at_current(self, nib: list[bool]) -> None:
        """
        An internal function for writing 4 bits' worth of information

        Args:
            nib (list[bool]): A length-4 list of boolean values
        """

        assert len(nib) == 4, "Invalid operation: attempt to write nibble of improper length"

        # Only first 3 need moves after them, so split the nibble to save a step
        for bit_value in nib[:3]:
            assert isinstance(bit_value, bool), "Invalid operation: attempt to write non-bool elememt to nibble"
            if bit_value:
                self._m()
            else:
                self._u()
            self._f()
        if nib[3]:
            self._m()
        else:
            self._u()

    def _r(self, degrees: float=90) -> None:
        """
        An internal shorthand function that turns turtle to the right, defaults to 90 degrees

        Args:
            degrees(float)=90: The degrees to turn turtle
        """
        t.rt(degrees)

    def _l(self, degrees: float=90) -> None:
        """
        An internal shorthand function that turns turtle to the left, defaults to 90 degrees

        Args:
            degrees(float)=90: The degrees to turn turtle
        """
        t.lt(degrees)

    def _f(self, distance: float=1) -> None:
        """
        An internal shorthand function that moves turtle forward, defaults to 1 square

        Args:
            distance(float): The distance to move turtle, defaults to turtle_pen_size
        """
        t.fd(distance * self.turtle_pen_size)

    def _b(self, distance: float=1) -> None:
        """
        An internal shorthand function that moves turtle backwards, defaults to 1 square

        Args:
            distance(float): The distance to move turtle, defaults to turtle_pen_size
        """
        t.bk(distance * self.turtle_pen_size)

    def _m(self) -> None:
        """
        An internal shorthand function to mark the current space with turtle
        """
        t.dot(self.turtle_pen_size)

    def _u(self) -> None:
        """
        An internal shorthand function to unmark the current space with turtle
        """
        t.dot(self.turtle_pen_size, 'white')

    def _reset_turtle(self) -> None:
        """
        An internal function that resets turtle to the origin
        """
        t.setpos(self.turtle_origin)
        t.seth(0)

    def __init__(self, turtle_pen_size: int=10,
                 turtle_speed: int=1000,
                 turtle_screensize_x: int=600,
                 turtle_screensize_y: int=600,
                 turtle_window_buffer: int=2,
                 show_animation: bool=False,
                 refresh_interval: int=10,
                 grid_width: int=2,
                 grid_height: int=2):

        self.turtle_pen_size = turtle_pen_size
        self.turtle_speed = turtle_speed
        self.turtle_screensize_x = turtle_screensize_x
        self.turtle_screensize_y = turtle_screensize_y

        """
        The turtle window often has a border that can hide information behind it.
        On my device, for example, this border is 2 pixels, so I leave a 2 pixel buffer.
        """
        self.turtle_window_buffer = turtle_window_buffer       

        self.show_animation = show_animation
        self.refresh_interval = refresh_interval

        self.grid_width = grid_width
        self.grid_height = grid_height


        self.turtle_origin = ((-self.turtle_screensize_x+self.turtle_pen_size)//2+self.turtle_window_buffer,
                              (self.turtle_screensize_y-self.turtle_pen_size)//2-self.turtle_window_buffer)
        self.mem_size = self.grid_width * self.grid_height * self.BLOCK_SIZE[0] * self.BLOCK_SIZE[1]
        self.address_length = self.mem_size.bit_length() // 8 + 1

        self.normalizer = normalize.Normalizer(self.turtle_origin, self.turtle_pen_size, self.BLOCK_SIZE, self.grid_width, self.grid_height, self.BLOCK_GAP, self.CELL_GAP, self.BYTE_ORDER)
        self.detector = detection.Detector(t)
        self.screen = t.Screen()

        self.screen.setup(width=self.turtle_screensize_x, height=self.turtle_screensize_y)
        if not self.show_animation:
            self.screen.tracer(0)

        t.pensize(self.turtle_pen_size)
        t.speed(self.turtle_speed)
        t.pu()
        t.setposition(self.turtle_origin)