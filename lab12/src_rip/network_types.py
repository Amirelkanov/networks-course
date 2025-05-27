from enum import Enum


class NetworkMessageType(Enum):
    DV = "DV"  # Distance Vector message
    STOP = "STOP"  # Stop message to terminate node threads


type IP = str
