class Normalizer:
    """
    A class to help normalize things like memory addresses
    such that turtle can properly use the output.
    """

    def __init__(self, turtle_origin: tuple[int], turtle_pen_size: int, block_size: tuple[int], grid_width: int, grid_height: int, block_gap: int, cell_gap: int, byte_order: str):
        self.turtle_origin = turtle_origin
        self.turtle_pen_size = turtle_pen_size
        self.block_size = block_size
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.block_gap = block_gap
        self.cell_gap = cell_gap
        self.byte_order = byte_order

        self.total_blocks = grid_width * grid_height
        self.cell_width = turtle_pen_size * (4 + cell_gap)
        self.cell_height = turtle_pen_size * (2 + cell_gap)
        self.block_width = block_size[0] * self.cell_width + block_gap * turtle_pen_size
        self.block_height = block_size[1] * self.cell_height + block_gap * turtle_pen_size

    def address_to_pos(self, address: bytes) -> tuple[int]:
        """
        Turns a byte-format address into a position that turtle
        can understand.

        Args:
            address (bytes): a byte-format memory address

        Returns:
            tuple[int]: the corresponding position on the canvas
        """

        address_literal = int.from_bytes(address, self.byte_order)

        block = address_literal // (self.block_size[0] * self.block_size[1])
        assert block < self.total_blocks

        cell = address_literal % (self.block_size[0] * self.block_size[1])
        assert cell < self.block_size[0] * self.block_size[1]

        x = self.turtle_origin[0] + ((block // self.grid_height) * self.block_width + (cell // self.block_size[1]) * self.cell_width)
        y = self.turtle_origin[1] - ((block % self.grid_height) * self.block_height + (cell % self.block_size[1]) * self.cell_height)

        return (x, y)
