from ..config import *
from enum import Enum,auto

class ComponentType(Enum):
    RenderComponent = auto()
    TransformComponent = auto()

class BaseComponent:
    def __init__(self):
        self.game = None
        self.scene = None
        self.game_object = None

        self.type = None

    def on_update(self): ...

    def on_close(self): ...