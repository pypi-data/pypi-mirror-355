from ..config import *

WINDOW_SIZE = "window-size"
WINDOW_POS = "window-pos"
WINDOW_TITLE = "window-title"
WINDOW_BG_COLOUR = "window-bg-colour"
WINDOW_ICON = "window-icon"

window_config = {
    WINDOW_SIZE: (1080, 720),
    WINDOW_POS: (-1, -1),
    WINDOW_TITLE: "========== Default Title ==========",
    WINDOW_BG_COLOUR: (10,40,80),
    WINDOW_ICON: None,
}

class Window:
    def __init__(self,game):
        self.game = game

        icon_path = window_config[WINDOW_ICON] if window_config[WINDOW_ICON] else os.path.join(self.game.root,"assets", "Icon.png")

        self.icon = self.game.asset_manager.get_image("all-scenes",icon_path)
        pg.display.set_icon(self.icon)

        self.win = pg.display.set_mode(window_config[WINDOW_SIZE])
        pg.display.set_caption(window_config[WINDOW_TITLE])

        screen_w, screen_h = pg.display.get_desktop_sizes()[0]
        win_w, win_h = self.win.get_size()

        # Calculate centered position
        center_x = (screen_w - win_w) // 2
        center_y = (screen_h - win_h) // 2

        pos = [ window_config[WINDOW_POS][0], window_config[WINDOW_POS][1]]

        if window_config[WINDOW_POS][0] == -1:
            pos[0] = center_x

        if window_config[WINDOW_POS][1] == -1:
            pos[1] = center_y

        self.width,self.height = self.win.get_size()

        pg.display.set_window_position(pos)

    def event_handler(self,event):
        if event.type == pg.QUIT:
            self.game.close()

    def render(self):
        self.win.fill(window_config[WINDOW_BG_COLOUR])

    def update(self):
        if self.game.extra_info:
            pg.display.set_caption(f"{window_config[WINDOW_TITLE]} | FPS: {self.game.clock.get_fps() :.0f}")

    def close(self):
        pass

