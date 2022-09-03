import moderngl_window as mglw
from moderngl_window.scene.camera import OrbitCamera


class OrbitCameraWindow(mglw.WindowConfig):
    """Base class with built in 3D orbit camera support"""

    def render(self, time: float, frame_time: float):
        pass

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.camera = OrbitCamera(aspect_ratio=self.wnd.aspect_ratio, radius=10.0, near=0.1)
        self.camera_enabled = True

    def key_event(self, key, action, modifiers):
        keys = self.wnd.keys

        if action == keys.ACTION_PRESS:
            if key == keys.C:
                self.camera_enabled = not self.camera_enabled
                self.wnd.mouse_exclusivity = self.camera_enabled
                self.wnd.cursor = not self.camera_enabled
            if key == keys.SPACE:
                self.timer.toggle_pause()

    def mouse_position_event(self, x: int, y: int, dx, dy):
        if self.camera_enabled:
            self.camera.rot_state(dx, dy)

    def mouse_scroll_event(self, x_offset: float, y_offset: float):
        if self.camera_enabled:
            self.camera.zoom_state(y_offset)

    def resize(self, width: int, height: int):
        self.camera.projection.update(aspect_ratio=self.wnd.aspect_ratio)
