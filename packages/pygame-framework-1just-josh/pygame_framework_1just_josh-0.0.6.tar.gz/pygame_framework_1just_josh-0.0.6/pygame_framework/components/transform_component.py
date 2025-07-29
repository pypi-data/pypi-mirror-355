from ..config import *
from .base_component import BaseComponent,ComponentType

class TransformComponent(BaseComponent):
    def __init__(self,position:type[int,int]=(0,0),
                 rotation:int=0,
                 size:type[int,int]=(100,100)):
        super().__init__()

        self.type = ComponentType.TransformComponent

        self.position = position
        self.rotation = rotation
        self.size = size

        self.rect = pg.Rect(self.position,self.size)