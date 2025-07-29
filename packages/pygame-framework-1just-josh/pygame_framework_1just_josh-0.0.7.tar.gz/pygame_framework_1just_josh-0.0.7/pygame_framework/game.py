import os.path

from .config import *
from .core.window import Window
from .core.scene_manager import SceneManager
from .core.asset_manager import AssetManager

GAME_FPS_LOCk = "game-fps-lock"
GAME_BUILD_LOCATION = "game-build-location"
GAME_FILE_ENCRYPTION_KEY = "game-file-encryption-key"

game_config = {
    GAME_FPS_LOCk: 0,
    GAME_BUILD_LOCATION: os.getcwd(),
    GAME_FILE_ENCRYPTION_KEY: None,
}

class Game:
    def __init__(self,extra_info=False):
        pg.init()

        self.extra_info = extra_info

        self.build_dir = game_config[GAME_BUILD_LOCATION]
        self.encrypt_key = game_config[GAME_FILE_ENCRYPTION_KEY]
        self.cipher = Fernet(self.encrypt_key) if self.encrypt_key else None

        self.root = os.path.abspath(os.path.dirname(__file__))
        print(self.root)

        self.asset_manager = AssetManager(self)
        self.window = Window(self)

        self.scene_manager = SceneManager(self)

        self.clock = pg.time.Clock()

        self.dt = 1

        self.running = True

    def event_handler(self):
        for event in pg.event.get():
            self.window.event_handler(event)

            self.scene_manager.event_handler(event)

    def render(self):
        self.window.render()

        self.scene_manager.render()

        pg.display.flip()

    def update(self):
        self.dt = self.clock.tick(game_config[GAME_FPS_LOCk]) / 1000

        self.scene_manager.update()

        self.window.update()

    def close(self):
        self.scene_manager.close()
        self.window.close()
        pg.quit()
        sys.exit()

    def run(self):
        while self.running:
            self.event_handler()
            self.update()
            self.render()

        self.close()