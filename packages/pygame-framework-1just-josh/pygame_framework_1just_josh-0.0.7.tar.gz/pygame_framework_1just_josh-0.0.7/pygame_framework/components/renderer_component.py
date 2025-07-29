
from ..config import *
from .base_component import BaseComponent,ComponentType


class RendererComponent(BaseComponent):
    def __init__(self, transform_component, image: pg.Surface):

        super().__init__()
        self.type = ComponentType.RenderComponent

        self.transform = transform_component
        self.image = image


