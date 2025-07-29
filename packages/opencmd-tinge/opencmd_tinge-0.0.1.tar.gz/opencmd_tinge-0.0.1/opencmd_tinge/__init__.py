from .styled import StyledText, StyledTextBuilder
from .styles import *

def styled():
    return StyledText()

__all__ = ["styled", "StyledText", "StyledTextBuilder"]