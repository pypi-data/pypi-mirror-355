import os
import sys
import msgpack

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

import pygame as pg

from pathlib import Path
from io import BytesIO
from cryptography.fernet import Fernet

def is_valid_file_path(path_str):
    path = Path(path_str)
    return path.is_file()

