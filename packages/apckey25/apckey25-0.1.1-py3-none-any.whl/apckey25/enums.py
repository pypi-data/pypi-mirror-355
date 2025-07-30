from enum import Enum


class UIButton(Enum):
    """
    Enum for ui buttons.
    """

    TRACK_BUTTON_1 = 0x40
    TRACK_BUTTON_2 = 0x41
    TRACK_BUTTON_3 = 0x42
    TRACK_BUTTON_4 = 0x43
    TRACK_BUTTON_5 = 0x44
    TRACK_BUTTON_6 = 0x45
    TRACK_BUTTON_7 = 0x46
    TRACK_BUTTON_8 = 0x47

    SCENE_LAUNCH_1 = 0x52
    SCENE_LAUNCH_2 = 0x53
    SCENE_LAUNCH_3 = 0x54
    SCENE_LAUNCH_4 = 0x55
    SCENE_LAUNCH_5 = 0x56

    STOP_CLIPS = 0x51
    PLAY = 0x5B
    RECORD = 0x5D


class UIButtonLEDMode(Enum):
    """
    Enum for LED modes for UI buttons.
    """

    OFF = 0x00
    ON = 0x01
    BLINKING = 0x02


class LEDMode(Enum):
    """
    Enum for LED modes.
    """

    BRIGHTNESS_10 = 0
    BRIGHTNESS_25 = 1
    BRIGHTNESS_50 = 2
    BRIGHTNESS_65 = 3
    BRIGHTNESS_75 = 4
    BRIGHTNESS_90 = 5
    BRIGHTNESS_100 = 6

    PULSING_1_16 = 7
    PULSING_1_8 = 8
    PULSING_1_4 = 9
    PULSING_1_2 = 10

    BLINKING_1_24 = 11
    BLINKING_1_16 = 12
    BLINKING_1_8 = 13
    BLINKING_1_4 = 14
    BLINKING_1_2 = 15


class ButtonEventType(Enum):
    """
    Enum for button event types.
    """

    PRESS = 0x00
    RELEASE = 0x01


class Encoder(Enum):
    """
    Enum for encoders.
    """

    ENCODER_1 = 0x30
    ENCODER_2 = 0x31
    ENCODER_3 = 0x32
    ENCODER_4 = 0x33
    ENCODER_5 = 0x34
    ENCODER_6 = 0x35
    ENCODER_7 = 0x36
    ENCODER_8 = 0x37
