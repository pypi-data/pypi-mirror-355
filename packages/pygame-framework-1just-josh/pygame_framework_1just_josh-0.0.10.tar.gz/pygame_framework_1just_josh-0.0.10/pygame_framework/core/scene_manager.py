from ..config import *


class SceneManager:
    def __init__(self, game):
        self.game = game

        self.scenes = {}
        self.selected_scene = None

    def add_scene(self, name, scene):
        if len(self.scenes) == 0:
            self.selected_scene = name

        scene.game = self.game
        scene.name = name
        scene.display_surface = pg.display.get_surface()
        scene.on_create()

        self.scenes[name] = scene

    def event_handler(self,event):
        if self.selected_scene is not None:
            self.scenes[self.selected_scene].on_event(event)

    def render(self):
        if self.selected_scene is not None:
            self.scenes[self.selected_scene].on_render()

    def update(self):
        if self.selected_scene is not None:
            self.scenes[self.selected_scene].on_update()

    def close(self):
        if self.selected_scene is not None:
            self.scenes[self.selected_scene].on_close()