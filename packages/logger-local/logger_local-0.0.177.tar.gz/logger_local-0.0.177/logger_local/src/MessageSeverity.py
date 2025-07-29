from enum import Enum


class MessageSeverity(Enum):
    Debug = 100
    Verbose = 200
    Init = 300
    Start = 400
    End = 402
    Information = 500
    Warning = 600
    Error = 700
    Critical = 800
    Exception = 900
