from typing import Reversible
import moderngl_window as mglw
from moderngl_window.geometry import quad_fs
import moderngl as mgl
import numpy as np
from pyrr import Matrix44 as m44
from cam import OrbitCameraWindow

class Window(mglw.WindowConfig):

    window_size = (800, 600)
    gl_version = (4, 6)
    resource_dir = "resources"
    aspect_ratio = window_size[0]/window_size[1]

    def update_view(self):
        x = self.r*np.sin(self.phi)*np.cos(self.theta)
        y = self.r*np.sin(self.phi)*np.sin(self.theta)
        z = self.r*np.cos(self.phi)
        self.eye = np.array([x, y, z], dtype='f4')
        target = np.array([0, 0, 0], dtype='f4')
        up = np.array([0, 0, 1], dtype='f4')
        # vreate look at
        forward = np.array(target - self.eye)/np.linalg.norm(target - self.eye)
        side = np.cross(forward, up)/np.linalg.norm(np.cross(forward, up))
        up = np.cross(side, forward)/np.linalg.norm(np.cross(side, forward))

        self.view = np.array((
                (side[0], up[0], -forward[0], 0.),
                (side[1], up[1], -forward[1], 0.),
                (side[2], up[2], -forward[2], 0.),
                (-np.dot(side, self.eye), -np.dot(up, self.eye), np.dot(forward, self.eye), 1.0)
            ), dtype='f4')
        
        self.ocean_prog['view'].write(self.view)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # --------------------- PARAMETERS
        self.wind_speed = 20
        self.wind_dir = np.array([1, 1])
        self.patch_size = 500
        self.choppy = 3
        self.surf_size = 10
        self.wave_scale = 1.5


        # ----------------------------- CAMERA
        self.theta = np.radians(20)
        self.phi = np.radians(70)
        self.r = 4.

        self.eye = None
        self.proj = m44.perspective_projection(70, self.aspect_ratio, 0.1, 100, 'f4')
        self.view = None
        self.model = m44.identity()
        self.scale_model = m44.from_scale([self.surf_size/2., self.surf_size/2., self.surf_size/2.])
        

        # -------------------- SETTINGS
        self.N = 256
        self.log2N = int(np.log2(self.N))
        gs = 16
        self.nxyz = [int(self.N/gs),int(self.N/gs), 1]


        # -------------- PROGRAMS
        self.spec_prog = self.load_program("shader/spectrum.glsl")
        self.spec_prog['L'].value = self.patch_size
        self.spec_prog['w_speed'].value = self.wind_speed
        


        self.debug_prog = self.load_program("shader/debug.glsl")
        self.fft_comp = self.load_compute_shader("compute/FFT.comp")
        self.inv_comp = self.load_compute_shader("compute/inversion.comp")
        self.normal_comp = self.load_compute_shader("compute/normal.comp")

        self.quad = quad_fs()
        self.surf = self.load_scene('objects/surface.obj').meshes[0].vao


        self.norm_tex = self.ctx.texture((self.N, self.N), components=4, dtype='f4')
        # self.norm_tex.filter = mgl.NEAREST, mgl.NEAREST

        # Z displamcement
        self.hktz_tex = self.ctx.texture((self.N, self.N), components=4, dtype='f4')
        self.hktz_tex.filter = mgl.NEAREST, mgl.NEAREST
        self.hktz_tex.repeat_x = True; self.hktz_tex.repeat_y = True
        # XY displacement
        self.dktxy_tex = self.ctx.texture((self.N, self.N), components=4, dtype='f4')
        self.dktxy_tex.filter = mgl.NEAREST, mgl.NEAREST
        self.dktxy_tex.repeat_x = True; self.dktxy_tex.repeat_y = True

        # butterfly texture
        self.twid_tex = self.ctx.texture((self.log2N, self.N), components=4, data=np.array(self.gen_twiddle()).tobytes(), dtype='f4')
        self.twid_tex.filter = mgl.NEAREST, mgl.NEAREST

        # noise textures
        gauss_norm = np.random.normal(0.0, 1.0, (self.N, self.N, 4)).astype('f4')
        self.noise_tex = self.ctx.texture((self.N, self.N), components=4, data=gauss_norm.tobytes(), dtype='f4')
        
        # spectrum framebuffer
        self.spec_fb = self.ctx.framebuffer(color_attachments=(self.hktz_tex, self.dktxy_tex))

        # ping pong for fft
        self.pingpong0 = self.ctx.texture((self.N, self.N), 4, dtype='f4')
        self.pingpong0.filter = mgl.NEAREST, mgl.NEAREST
        self.pingpong1 = self.ctx.texture((self.N, self.N), 4, dtype='f4')
        self.pingpong1.filter = mgl.NEAREST, mgl.NEAREST

        # Ocean Surface
        
        self.ocean_prog = self.load_program("shader/ocean.glsl")

        self.ocean_prog['proj'].write(self.proj.astype('f4'))
        self.ocean_prog['scale_model'].write(self.scale_model.astype('f4'))
        self.ocean_prog['model'].write(self.model.astype('f4'))
        self.ocean_prog['wave_scale'].value = self.wave_scale

        self.update_view()

    def FFT(self, in_tex:mgl.Texture, out_tex:mgl.Texture):  
        self.twid_tex.bind_to_image(0)
        self.fft_comp['Vertical'].value = 0

        n = self.log2N
        for i in range(n):
            self.fft_comp['stage'] = i
            if i==0:
                in_tex.bind_to_image(1)
                self.pingpong1.bind_to_image(2)
            else:
                self.pingpong0.bind_to_image(1 if i%2==0 else 2)
                self.pingpong1.bind_to_image(2 if i%2==0 else 1)
            self.fft_comp.run(*self.nxyz)
        
        if (n-1)%2==0:
            self.pingpong0, self.pingpong1 = self.pingpong1, self.pingpong0

        self.fft_comp['Vertical'].value = 1
        for i in range(self.log2N):
            self.fft_comp['stage'] = i
            self.pingpong0.bind_to_image(1 if i%2==0 else 2)
            self.pingpong1.bind_to_image(2 if i%2==0 else 1)
            self.fft_comp.run(*self.nxyz)

        if (n-1)%2==0:
            self.pingpong0, self.pingpong1 = self.pingpong1, self.pingpong0

        self.inv_comp['N'].value = self.N
        self.pingpong0.bind_to_image(0)
        out_tex.bind_to_image(1)
        self.inv_comp.run(*self.nxyz)

    def gen_twiddle(self):

        W = np.zeros((self.N, self.log2N, 4), dtype='f4')
        bit_rev = np.array([self.rev_bit(i, self.log2N) for i in range(self.N)]) # reversed bits
        
        for stage in range(self.log2N):
            span = int(np.power(2, stage+1))
            h_span = int(span/2) # half span
            for k in range(self.N):
                twi = np.exp(1j * 2 * np.pi * k / span)
                top = k % span < h_span

                if stage == 0:
                    if top:
                        W[k, stage] = [twi.real, twi.imag, bit_rev[k], bit_rev[k+h_span]]
                    else:
                        W[k, stage] = [twi.real, twi.imag, bit_rev[k-h_span], bit_rev[k]]
                else:
                    if top:
                        W[k, stage] = [twi.real, twi.imag, k, (k+h_span)]
                    else:
                        W[k, stage] = [twi.real, twi.imag, (k-h_span), k]
        return W

    def rev_bit(self, n, N):
        bits = f'{n:b}'
        bits = '0'*(N-len(bits))+bits
        rev_bits = bits[::-1]
        res_int = int(rev_bits, 2)
        return res_int
    
    def render(self, t, dt):
        
        self.spec_fb.use()
        self.ctx.clear()
        self.noise_tex.use(0)
        self.spec_prog['N'] = self.N
        self.spec_prog['t'].value = 2*t
        self.quad.render(self.spec_prog)

        self.FFT(self.hktz_tex, self.hktz_tex)
        self.FFT(self.dktxy_tex, self.dktxy_tex) 

        self.hktz_tex.bind_to_image(0)
        self.dktxy_tex.bind_to_image(1)
        self.norm_tex.bind_to_image(2)
        self.normal_comp['N'].value = self.N

        self.normal_comp['scale'].value = self.surf_size
        self.normal_comp['choppy'].value = self.choppy
        self.normal_comp['wave_scale'].value = self.wave_scale
        self.normal_comp.run(*self.nxyz)

        ############# surf render
        self.ctx.enable(mgl.DEPTH_TEST)

        self.wnd.fbo.use()

        self.ctx.clear(0.2, 0.2, 0.2)
        self.wnd.fbo.viewport = (0, 0, *self.window_size)       
        
        self.hktz_tex.use(0)
        self.dktxy_tex.use(1)
        self.norm_tex.use(2)
        self.ocean_prog['choppy'].value = self.choppy
        self.ocean_prog['view'].write(self.view.astype('f4'))
        try:
            self.ocean_prog['eye'].write(self.eye.astype('f4'))
        except:
            pass
        self.surf.render(self.ocean_prog)

        # self.ctx.disable(mgl.DEPTH_TEST)
        # self.wnd.fbo.viewport = (0, 0, 256, 256)
        # self.norm_tex.use(0)
        # self.quad.render(self.debug_prog)

    
    def mouse_drag_event(self, x: int, y: int, dx: int, dy: int):
        
        self.theta -= np.radians(dx*0.4)
        self.phi-=np.radians(dy*0.3)
        self.phi = np.clip(self.phi, np.radians(10), np.radians(170))
        
        self.update_view()
    
    def mouse_scroll_event(self, x_offset: float, y_offset: float):
        
        self.r -= y_offset*0.1
        self.r = np.clip(self.r, 1, 10)
        
        self.update_view()

Window.run()