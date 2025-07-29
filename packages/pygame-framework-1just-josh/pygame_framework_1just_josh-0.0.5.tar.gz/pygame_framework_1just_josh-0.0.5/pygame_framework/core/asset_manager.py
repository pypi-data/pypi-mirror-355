import os
import msgpack
import pygame as pg
from io import BytesIO

class AssetManager:
    def __init__(self, game):
        self.game = game
        self.root = os.path.join(self.game.build_dir, "assets.aab")
        self.scene_assets = {}

        self.load_aab_file()

    @property
    def selected_scene(self):
        return self.game.scene_manager.selected_scene or "all-scenes"

    def load_aab_file(self):
        if not os.path.exists(self.root):
            with open(self.root, "wb") as file:
                file.write(msgpack.packb({}))

        # print(f"[LOAD_AAB] Scene Assets After Loading: {self.scene_assets}")

    def load_image(self, scene_name, path):
        try:
            with open(self.root, "rb") as file:
                assets = msgpack.unpackb(file.read())

            if scene_name in assets and path in assets[scene_name]:
                image_data = assets[scene_name][path]
                # print(f"[LOAD] Loaded {path} from `.aab` for scene {scene_name}")

                # Convert raw bytes back into Pygame Surface
                image_surface = pg.image.load(BytesIO(image_data["raw-data"]))
                # print("loading image from `.aab`")

                # print("saving in memory")
                self.scene_assets[scene_name][path] = image_surface
                return image_surface  # Now returning a proper Surface class

        except Exception as e:
            print(f"[ERROR] Failed to load from `.aab`: {e}")  # Catch errors

        return self.save_image(scene_name, path)

    def load_sound(self,scene_name,path):
        try:
            with open(self.root, "rb") as file:
                assets = msgpack.unpackb(file.read())

            if scene_name in assets and path in assets[scene_name]:
                sound_data = assets[scene_name][path]

                mixer_sound = pg.mixer.Sound(file=BytesIO(sound_data["raw-data"]))

                self.scene_assets[scene_name][path] = mixer_sound
                return mixer_sound

        except Exception:
            pass

        return self.save_sound(scene_name,path)

    def save_image(self, scene_name, path):
        print(f"[SAVING] {scene_name} | {path}")
        image = pg.image.load(path)  # Load image from disk
        self.scene_assets.setdefault(scene_name, {})[path] = image  # Store in scene_assets

        # Prepare image data for `.aab`
        image_data = {
            "size": image.get_size(),
            "raw-data": self._surface_to_png_bytes(image)
        }

        # Read existing assets from `.aab`
        if os.path.exists(self.root):
            with open(self.root, "rb") as file:
                assets = msgpack.unpackb(file.read())
        else:
            assets = {}

        # Ensure scene exists in assets before adding the path
        assets.setdefault(scene_name, {})[path] = image_data

        # **Write updated assets to `.aab`**
        with open(self.root, "wb") as file:
            file.write(msgpack.packb(assets, use_bin_type=True))

        # print(f"[SAVE] Asset {path} stored in `.aab` under scene {scene_name}")
        return image

    def save_sound(self, scene_name, path):
        print(f"[SAVING] {scene_name} | {path}")

        # Load the sound file as a pygame Sound object
        sound = pg.mixer.Sound(path)
        self.scene_assets.setdefault(scene_name, {})[path] = sound

        # Read the file's raw bytes
        with open(path, "rb") as file:
            raw_data = file.read()

        # Structure to store in .aab
        sound_data = {
            "raw-data": raw_data
        }

        # Load current .aab contents
        if os.path.exists(self.root):
            with open(self.root, "rb") as file:
                assets = msgpack.unpackb(file.read())
        else:
            assets = {}

        # Insert sound data under scene and path
        assets.setdefault(scene_name, {})[path] = sound_data

        # Write back the updated assets
        with open(self.root, "wb") as file:
            file.write(msgpack.packb(assets, use_bin_type=True))

        print(f"[SAVE] Sound {path} stored in `.aab` under scene {scene_name}")
        return sound

    def get_image(self,scene_name,path):
        # get image from memory
        if scene_name in self.scene_assets:
            if path in self.scene_assets[scene_name]:
                return self.scene_assets[scene_name][path]

        if scene_name not in self.scene_assets:
            self.scene_assets[scene_name] = {}

        # load in aab file
        return self.load_image(scene_name,path)

    def get_sound(self,scene_name,path):
        if scene_name in self.scene_assets:
            if path in self.scene_assets[scene_name]:
                return self.scene_assets[scene_name][path]

        if scene_name not in self.scene_assets:
            self.scene_assets[scene_name] = {}

        # load in aab file
        return self.load_sound(scene_name, path)

