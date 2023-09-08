import moderngl as mgl
import moderngl_window as mglw
from camera import OrbitCamera
from moderngl_window.geometry import cube


class MainWin(OrbitCamera):
    resource_dir = "resources/"
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.sph = cube()
        self.debug3d_prog = self.load_program("shader/debug3d.glsl")
        self.ctx.enable(mgl.DEPTH_TEST)

        self.debug3d_prog["Proj"].write(self.proj_mat.astype('f4'))
        

    def render_cam(self, t, dt):
        self.wnd.clear(0.1)
        self.debug3d_prog["View"].write(self.view_mat.astype('f4'))
        self.sph.render(self.debug3d_prog)
        

MainWin.run()