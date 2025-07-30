import mido

from .LEDBuffer import LEDBuffer
from .consts import APC_KEY_25_LAYOUT, APC_KEY_25_LAYOUT_FLATTENED
from .enums import UIButton, Encoder, ButtonEventType, UIButtonLEDMode

from typing import Callable


class APCKey25:
    """
    APCKey25 class for handling APC Key 25 MIDI controller.
    """

    def __init__(self, device_name: str):
        self.device_name = device_name
        self.is_connected = False
        self.midi_input = None
        self.midi_output = None

        self.matrix_callbacks = []
        self.button_callbacks = []
        self.encoder_callbacks = []

        self.led_buffers = {}
        self.current_buffer = None

        self.ui_button_led_buffer = {}

        # Populate the UI button LED buffer with default OFF state
        for button in UIButton:
            if button != UIButton.STOP_CLIPS:
                self.ui_button_led_buffer[button] = UIButtonLEDMode.OFF

    def connect(self):
        """
        Connect to the APC Key 25 MIDI device.
        """
        if self.is_connected:
            raise RuntimeError("Already connected to the device.")

        mido.set_backend("mido.backends.portmidi")

        self.midi_input = mido.open_input(self.device_name)
        self.midi_output = mido.open_output(self.device_name)

        self.is_connected = True

    def disconnect(self):
        """
        Disconnect from the APC Key 25 MIDI device.
        """
        if not self.is_connected:
            raise RuntimeError("Not connected to the device.")

        self.midi_input.close()
        self.midi_output.close()

        self.is_connected = False

    def register_matrix_callback(
        self,
        callback: Callable[
            [int, int, ButtonEventType],
            None,
        ],
    ):
        """
        Register a callback for button events on the button matrix.

        Args:
            callback (Callable[[int, int], None]): The function to call when a matrix event occurs. (Args: row, col, event type; indexed from 0 in top-left corner)
        """
        self.matrix_callbacks.append(callback)

    def register_button_callback(
        self, callback: Callable[[UIButton, ButtonEventType], None]
    ):
        """
        Register a callback for button events on ui buttons.

        Args:
            callback (Callable[[UIButton], None]): The function to call when a button event occurs. (Args: UIButton enum value, event type)
        """
        self.button_callbacks.append(callback)

    def register_encoder_callback(self, callback: Callable[[Encoder, int], None]):
        """
        Register a callback for encoder events.

        Args:
            callback (Callable[[Encoder, int]): The function to call when an encoder event occurs. (Args: Encoder enum value, delta value)
        """
        self.encoder_callbacks.append(callback)

    def new_led_buffer(self, id: str, select: bool = True) -> LEDBuffer:
        """
        Create a new LED buffer.

        Args:
            id (str): A unique identifier for the buffer.
            select (bool, optional): Whether to also automatically switch to the new buffer. Defaults to True.

        Returns:
            LedBuffer: A new LedBuffer instance initialized

        Raises:
            ValueError: If a buffer with the given ID already exists.
        """
        if id in self.led_buffers:
            raise ValueError(f"Buffer with id {id} already exists.")

        buf = LEDBuffer(APC_KEY_25_LAYOUT)
        self.led_buffers[id] = buf

        if select:
            self.set_led_buffer(id)

        return buf

    def set_led_buffer(self, id: str):
        """
        Select an existing LED buffer by its ID.

        Args:
            id (str): The unique identifier of the buffer to select.

        Raises:
            ValueError: If the buffer with the given ID does not exist.
        """
        if id not in self.led_buffers:
            raise ValueError(f"Buffer with id {id} does not exist.")

        self.current_buffer = self.led_buffers[id]

    def set_ui_button_led(self, button: UIButton, mode: UIButtonLEDMode):
        """
        Set the LED mode for a UI button. Please note that they only support a single LED mode.
        The STOP_CLIPS button DOES NOT have an LED.

        Args:
            button (UIButton): The UI button to set the LED mode for.
            mode (UIButtonLEDMode): The LED mode to set for the button.
        """
        if button == UIButton.STOP_CLIPS:
            raise ValueError("STOP_CLIPS button does not have an LED.")

        self.ui_button_led_buffer[button] = mode

    def loop(self):
        """
        Execute a single loop iteration to process incoming and outgoing MIDI messages.
        This method should be called repeatedly to handle MIDI events.
        """
        if not self.is_connected:
            raise RuntimeError("Not connected to the device.")

        self.__handle_incoming_midi()
        self.__handle_outgoing_midi()

    def clear_leds(self):
        """
        Clear all LEDs and unselect the current buffer.
        """

        # Matrix LEDs
        self.current_buffer = None

        # UI buttons
        for button in UIButton:
            if button != UIButton.STOP_CLIPS:
                self.set_ui_button_led(button, UIButtonLEDMode.OFF)

        # Send
        self.__handle_outgoing_midi()

    def __handle_incoming_midi(self):
        for msg in self.midi_input.iter_pending():
            if msg.type == "note_on" or msg.type == "note_off":
                event_type = (
                    ButtonEventType.PRESS
                    if msg.type == "note_on"
                    else ButtonEventType.RELEASE
                )

                if msg.note in APC_KEY_25_LAYOUT_FLATTENED:
                    row = (
                        APC_KEY_25_LAYOUT_FLATTENED.index(msg.note)
                        // APC_KEY_25_LAYOUT[0].__len__()
                    )
                    col = (
                        APC_KEY_25_LAYOUT_FLATTENED.index(msg.note)
                        % APC_KEY_25_LAYOUT[0].__len__()
                    )
                    for callback in self.matrix_callbacks:
                        callback(row, col, event_type)

                elif msg.note in UIButton._value2member_map_:
                    button = UIButton(msg.note)
                    for callback in self.button_callbacks:
                        callback(button, event_type)

            elif msg.type == "control_change":
                if msg.control in Encoder._value2member_map_:
                    encoder = Encoder(msg.control)

                    delta = 0
                    if msg.value < 64:
                        delta = msg.value
                    else:
                        delta = msg.value - 128

                    for callback in self.encoder_callbacks:
                        callback(encoder, delta)

    def __handle_outgoing_midi(self):
        if self.current_buffer:
            self.current_buffer._render(
                lambda channel, note, velocity: self.midi_output.send(
                    mido.Message(
                        "note_on", channel=channel, note=note, velocity=velocity
                    )
                )
            )

        else:
            for note in APC_KEY_25_LAYOUT_FLATTENED:
                self.midi_output.send(
                    mido.Message("note_on", channel=0, note=note, velocity=0)
                )

        # UI buttons
        for button, mode in self.ui_button_led_buffer.items():
            if button != UIButton.STOP_CLIPS:
                self.midi_output.send(
                    mido.Message(
                        "note_on",
                        channel=0,
                        note=button.value,
                        velocity=mode.value,
                    )
                )

    def __del__(self):
        """
        Destructor to ensure the device is disconnected when the instance is deleted.
        """
        if self.is_connected:
            self.clear_leds()
            self.disconnect()
