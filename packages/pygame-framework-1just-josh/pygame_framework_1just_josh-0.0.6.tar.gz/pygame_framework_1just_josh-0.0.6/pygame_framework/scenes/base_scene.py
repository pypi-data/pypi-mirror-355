from ..config import *
from ..core.renderer import Renderer

class BaseScene:
    def __init__(self):
        self.game = None
        self.name = None
        self.display_surface = None

        self.dirty = False

        self.renderer = Renderer()


        self.game_objects = []

    def get_image(self,path,*args,**kwargs):
        if not self.game:
            raise RuntimeError("\n\nDo not call 'get_image()' in '__init__'. Wait until the scene is fully initialized (e.g., in 'on_create()').")

        return self.game.asset_manager.get_image(kwargs.get("all-scenes",self.name), path)

    def get_sound(self,path,*args,**kwargs):
        if not self.game:
            raise RuntimeError(
                "\n\nDo not call 'get_sound()' in '__init__'. Wait until the scene is fully initialized (e.g., in 'on_create()').")

        return self.game.asset_manager.get_sound(kwargs.get("all-scenes", self.name), path)

    def add_game_object(self,obj):
        obj.id = len(self.game_objects)
        obj.scene = self
        obj.game = self.game

        self.dirty = True

        self.game_objects.append(obj)

    def remove_game_object(self, obj):
        if obj in self.game_objects and obj.id != -1:
            self.game_objects.remove(obj)
            obj.id = -1
            obj.on_close()
            self.dirty = True
            # Recalculate IDs
            for index, game_obj in enumerate(self.game_objects):
                game_obj.id = index

    def on_create(self):
        self.renderer.game = self.game
        self.renderer.scene = self
        self.renderer.create()

    def on_event(self,event):
        pass

    def on_update(self):
        for game_obj in self.game_objects:
            game_obj.on_update()
        self.renderer.update()

    def on_render(self):
        self.renderer.render()

    def on_close(self):
        pass