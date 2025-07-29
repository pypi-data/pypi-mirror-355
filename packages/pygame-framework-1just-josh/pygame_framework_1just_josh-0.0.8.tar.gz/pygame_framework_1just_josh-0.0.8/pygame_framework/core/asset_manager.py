import os
import msgpack
import pygame as pg
from io import BytesIO

class AssetManager:
    def __init__(self, game):
        self.game = game
        self.root = os.path.join(self.game.build_dir, "assets.aab")
        self.scene_assets = {}

        self._init_aab_file()

    @property
    def selected_scene(self):
        return self.game.scene_manager.selected_scene or "all-scenes"

    def _init_aab_file(self):
        if not os.path.exists(self.root):
            with open(self.root, "wb") as f:
                f.write(self._encode(msgpack.packb({})))

    def _encode(self, data: bytes) -> bytes:
        return self.game.cipher.encrypt(data) if self.game.cipher else data

    def _decode(self, data: bytes) -> dict:
        decrypted = self.game.cipher.decrypt(data) if self.game.cipher else data
        return msgpack.unpackb(decrypted)

    def _load_assets(self) -> dict:
        with open(self.root, "rb") as file:
            return self._decode(file.read())

    def _save_assets(self, assets: dict):
        packed = msgpack.packb(assets, use_bin_type=True)
        with open(self.root, "wb") as file:
            file.write(self._encode(packed))

    def _surface_to_png_bytes(self, surface):
        buffer = BytesIO()
        pg.image.save(surface, buffer, "PNG")
        return buffer.getvalue()

    def save_image(self, scene_name, path):
        image = pg.image.load(path)
        self.scene_assets.setdefault(scene_name, {})[path] = image

        image_data = {
            "size": image.get_size(),
            "raw-data": self._surface_to_png_bytes(image)
        }

        assets = self._load_assets()
        assets.setdefault(scene_name, {})[path] = image_data
        self._save_assets(assets)

        return image

    def load_image(self, scene_name, path):
        try:
            assets = self._load_assets()
            if scene_name in assets and path in assets[scene_name]:
                image_data = assets[scene_name][path]
                surface = pg.image.load(BytesIO(image_data["raw-data"]))
                self.scene_assets.setdefault(scene_name, {})[path] = surface
                return surface
        except Exception as e:
            print(f"[IMAGE-LOAD] Error loading from `.aab`: {e}")

        return self.save_image(scene_name, path)

    def get_image(self, scene_name, path):
        if scene_name in self.scene_assets and path in self.scene_assets[scene_name]:
            return self.scene_assets[scene_name][path]

        self.scene_assets.setdefault(scene_name, {})
        return self.load_image(scene_name, path)

    def save_sound(self, scene_name, path):
        sound = pg.mixer.Sound(path)
        self.scene_assets.setdefault(scene_name, {})[path] = sound

        with open(path, "rb") as file:
            raw_data = file.read()

        sound_data = {
            "raw-data": raw_data
        }

        assets = self._load_assets()
        assets.setdefault(scene_name, {})[path] = sound_data
        self._save_assets(assets)

        return sound

    def load_sound(self, scene_name, path):
        try:
            assets = self._load_assets()
            if scene_name in assets and path in assets[scene_name]:
                raw = assets[scene_name][path]["raw-data"]
                sound = pg.mixer.Sound(file=BytesIO(raw))
                self.scene_assets.setdefault(scene_name, {})[path] = sound
                return sound
        except Exception as e:
            print(f"[SOUND-LOAD] Error loading from `.aab`: {e}")

        return self.save_sound(scene_name, path)

    def get_sound(self, scene_name, path):
        if scene_name in self.scene_assets and path in self.scene_assets[scene_name]:
            return self.scene_assets[scene_name][path]

        self.scene_assets.setdefault(scene_name, {})
        return self.load_sound(scene_name, path)
