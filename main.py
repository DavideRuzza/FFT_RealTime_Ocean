import numpy as np
import moderngl as mgl
import moderngl_window as mglw
from camera import OrbitCamera
from moderngl_window.geometry import cube, quad_fs


def rev_bit(log2N):
    N = np.power(2, log2N)
    arr = []
    for i in range(N):
        bin_str = bin(i)[2:]
        bin_str = '0'*(log2N-len(bin_str))+bin_str

        arr.append(int(bin_str[::-1], 2))
    return np.array(arr, dtype=int)

def gen_twiddle(log2N):
    rev = rev_bit(log2N)
    N = int(np.power(2, log2N))
    twid_arr = np.zeros((N, log2N, 4), dtype='f4')
    for i in range(log2N):
        for n in range(N):
            top_wing = np.mod(n, np.power(2, i+1))<np.power(2, i)
            span = np.power(2, i)
            twi = np.exp(1j * 2 * np.pi * n / (2*span))
            if i == 0:
                if top_wing:
                    twid_arr[n, i] = [twi.real, twi.imag, rev[n], rev[n+span]]
                else:
                    twid_arr[n, i] = [twi.real, twi.imag, rev[n-span], rev[n]]
            else:
                if top_wing:
                    twid_arr[n, i] = [twi.real, twi.imag, n, n+span]
                else:
                    twid_arr[n, i] = [twi.real, twi.imag, n-span, n]
    return twid_arr

class MainWin(OrbitCamera):
    resource_dir = "resources/"
    window_size = (512, 512)
    aspect_ratio = 1
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


        self.N = 256
        self.log2N = int(np.log2(self.N))

        self.L = 100    # patch size

        self.U10 = 10.0     # wind speed
        self.wind_dir = np.array([1.0, 1.0])    # wind direction
        self.wind_dir/=np.linalg.norm(self.wind_dir)

        self.choppiness = 7.5   # choppiness of the waves

        self.sph = cube()
        self.quad = quad_fs()
        self.debug3d_prog = self.load_program("shader/debug3d.glsl")
        self.debug_prog = self.load_program("shader/debug.glsl")

        self.debug3d_prog["Proj"].write(self.proj_mat.astype('f4'))
        self.debug3d_prog["View"].write(self.view_mat.astype('f4'))  
        
        self.spectrum_prog = self.load_program("shader/spectrum.glsl")
        
        self.spectrum_prog["N"] = self.N
        self.spectrum_prog["L"] = self.L
        # self.spectrum_prog["w_speed"]
        # noise texture
        self.noise_data = np.random.normal(size=(self.N, self.N, 4)).astype('f4')
        self.noise_tex = self.to_texture(self.noise_data)

        self.ctx.enable(mgl.DEPTH_TEST)

        self.fbo_tex = self.ctx.texture((self.N, self.N), components=4, dtype='f4')
        self.fbo_tex.filter = mgl.NEAREST, mgl.NEAREST
        self.fbo = self.ctx.framebuffer(color_attachments=(self.fbo_tex))

    def to_texture(self, data: np.ndarray, dtype='f4'):
        tex = self.ctx.texture((data.shape[0], data.shape[1]), components=data.shape[2], data=data.tobytes(), dtype=dtype)
        tex.filter = mgl.NEAREST, mgl.NEAREST
        return tex

    def render_cam(self, t, dt):

        # self.wnd.fbo.viewport = (0, 0, self.N, self.N)
        self.fbo.use()
        self.fbo.clear()
        self.noise_tex.use(0)
        self.quad.render(self.spectrum_prog)
        
        self.spectrum_prog["t"] = t
        self.wnd.fbo.use()
        self.wnd.clear(0.0)
        self.fbo_tex.use(0)
        self.quad.render(self.debug_prog)
        # self.sph.render(self.debug3d_prog)
        

MainWin.run()