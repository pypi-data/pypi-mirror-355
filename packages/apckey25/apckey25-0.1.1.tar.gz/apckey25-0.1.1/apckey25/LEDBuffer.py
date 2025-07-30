from .enums import LEDMode
from .consts import FONT

from typing import Callable


class LEDBuffer:
    def __init__(self, layout: list[list[int]]):
        """
        Initialize the LED buffer with a given layout.

        Args:
            layout (list[list[int]]): A 2D list representing the LED layout.
                                      Each sublist contains channel numbers for each LED.
        """
        self.layout = layout
        self.buffer = [
            [
                {
                    "channel": 0,
                    "velocity": 0,
                }
            ]
            * len(row)
            for row in layout
        ]

    def set_led(
        self, row: int, col: int, color: int, mode: LEDMode = LEDMode.BRIGHTNESS_100
    ):
        """
        Set the color and mode of a specific LED.

        Args:
            row (int): The row index of the LED.
            col (int): The column index of the LED.
            color (int): The velocity index for the color. (see colors.py)
            mode (LEDMode): The mode for the LED.
        """
        if 0 <= row < len(self.layout) and 0 <= col < len(self.layout[row]):
            self.buffer[row][col] = {"channel": mode.value, "velocity": color}
        else:
            raise IndexError("LED position out of bounds.")

    def clear(self):
        """
        Clear the LED buffer by setting all LEDs to off.
        """
        for row in range(len(self.buffer)):
            for col in range(len(self.buffer[row])):
                self.buffer[row][col] = {"channel": 0, "velocity": 0}

    def render_text(
        self,
        start_col: int,
        content: str,
        color: int,
        mode: LEDMode = LEDMode.BRIGHTNESS_100,
    ):
        """
        Draw text on the LED buffer starting from a specific column.
        """

        for char in content:
            if char not in FONT:
                raise ValueError(f"Char '{char}' is not supported.")
            font = FONT[char]
            for row in range(len(font)):
                for col in range(len(font[row])):
                    if font[row][col]:
                        self.set_led(row, start_col + col, color, mode)
                    else:
                        self.set_led(row, start_col + col, 0, LEDMode.BRIGHTNESS_100)
            start_col += len(font[0]) + 1

    def _render(self, send_midi: Callable[[int, int, int], None]):
        """
        Render the LED buffer by sending MIDI messages for each LED.
        Only for internal use.

        Args:
            send_midi (Callable[[int, int, int], None]): A function to send MIDI messages.
                                                          It should accept channel, note, and velocity as arguments.
        """
        for row in range(len(self.buffer)):
            for col in range(len(self.buffer[row])):
                led = self.buffer[row][col]
                send_midi(led["channel"], self.layout[row][col], led["velocity"])
