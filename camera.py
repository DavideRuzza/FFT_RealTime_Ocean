import os
from moderngl_window.context.base.window import BaseWindow
from moderngl_window.timers.base import BaseTimer
import numpy as np
import moderngl_window as mglw
from pyrr import Matrix44 as m44



class OrbitCamera(mglw.WindowConfig):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.phi = np.pi/3
        self.theta = 0
        self.r = 5
        
        # velocity
        self.phi_v = 0.0
        self.theta_v = 0.0
        self.r_v = 0.0

        # damping
        self.phi_damp = 3
        self.theta_damp = 3
        self.r_damp = 2.5

        # acceleration
        self.phi_a = 0.0
        self.theta_a = 0.0

        self.proj_mat = m44.perspective_projection(35, self.aspect_ratio, 0.1, 100, dtype="f4")
        self.eye = self.calc_eye_pos()
        self.target = np.array([0,0,0])

        self.view_mat = m44.look_at(self.eye, self.target, np.array([0,0,1]))

        self.mouse_dx = 0
        self.mouse_dy = 0

    def calc_eye_pos(self):
        x = np.sin(self.phi)*np.cos(self.theta)*self.r
        y = np.sin(self.phi)*np.sin(self.theta)*self.r
        z = np.cos(self.phi)*self.r
        return np.array([x, y, z])

    def update_view(self):
        
        self.eye = self.calc_eye_pos()
        self.view_mat = m44.look_at(self.eye, self.target, np.array([0,0,1]))

    def integrate(self, dt):
        self.phi_v += (self.phi_a-self.phi_v*self.phi_damp)*dt
        self.theta_v += (self.theta_a-self.theta_v*self.theta_damp)*dt
        self.r_v -= self.r_v*self.r_damp*dt

        self.phi += self.phi_v*dt
        if self.phi<=0.01:
            self.phi=0.01
        if self.phi>=np.pi:
            self.phi=np.pi
        self.theta += self.theta_v*dt
        self.r+=self.r_v*dt
        if self.r<1:
            self.r=1


    def render_cam(self, t, dt):
        ''' Implement this Function'''
        raise("Implement me")
        
    def render(self, t, dt):
        self.integrate(dt)
        self.update_view()
        self.render_cam(t, dt)
    
    def mouse_drag_event(self, x: int, y: int, dx: int, dy: int):
        self.theta_a=-dx*1.2*np.power(self.r, 0.8)/2.
        self.phi_a=-dy*1.2*np.power(self.r, 0.8)/2.
    
    def mouse_scroll_event(self, x_offset: float, y_offset: float):
        # self.r-=y_offset*0.3
        self.r_v=-y_offset*2*np.power(self.r, 1.5)/5.

    def mouse_release_event(self, x: int, y: int, button: int):
        self.theta_a=0
        self.phi_a=0