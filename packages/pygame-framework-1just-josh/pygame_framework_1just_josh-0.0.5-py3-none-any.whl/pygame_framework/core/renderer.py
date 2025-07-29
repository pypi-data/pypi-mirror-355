from ..components.base_component import ComponentType
from ..components.renderer_component import RendererComponent
from ..config import *

class Renderer:
    def __init__(self,render_target=None):
        self.game = None
        self.scene = None

        self.render_target = render_target

        self.render_objects = []

    def check_dirty(self):
        if self.scene.dirty:
            self.render_objects = []
            for object in self.scene.game_objects:
                if render_comp := object.get_component(ComponentType.RenderComponent):
                    self.render_objects.append(render_comp)

            self.scene.dirty = False

    def create(self):
        self.render_target = self.render_target if not self.render_target is None else self.scene.display_surface
        self.check_dirty()

    def update(self):
        self.check_dirty()

    def render(self):
        for render_comp in self.render_objects:
            self.render_target.blit(render_comp.image,render_comp.transform.rect)