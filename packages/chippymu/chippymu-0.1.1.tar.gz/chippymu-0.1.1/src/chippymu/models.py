"""
定义一些基础类型
"""

from enum import Enum


class WaveType(str, Enum):
    """
    几种波形
    """

    SINE = "sine"
    SQUARE = "square"
    TRIANGLE = "triangle"
    SAWTOOTH = "sawtooth"
    NOISE = "noise"


class DrumType(str, Enum):
    """
    几种鼓声
    """

    KICK = "kick"
    SNARE = "snare"
    HIHAT = "hihat"
