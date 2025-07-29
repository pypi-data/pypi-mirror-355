from ..components.base_component import ComponentType
from ..config import *

class BaseGameObject:
    def __init__(self):
        self.game = None
        self.scene = None
        self.id = None

        self.dirty = False

        self.components = {}

    def add_component(self,component):
        if component.type is None:
            raise ValueError(f"Component {component} is missing a valid 'type'. Cannot add to GameObject.")

        component.game = self.game
        component.scene = self.scene
        component.game_object = self

        self.dirty = True

        self.components[component.type] = component

    def get_component(self,component_type:ComponentType):
        if component_type in self.components:
            return self.components[component_type]
        return None

    def on_create(self): ...

    def on_update(self):
        for component in self.components.values():
            component.on_update()

    def on_close(self):
        for component in self.components.values():
            component.on_close()

            self.game = None
            self.scene = None
            self.components = []