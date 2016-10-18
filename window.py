import numpy as np

import pyglet
from pyglet import gl
from pyglet.window import key
from pyglet.window import mouse
from pyglet import graphics
from pyglet.window import key

# Disable error checking for increased performance
# pyglet.options['debug_gl'] = False

# http://stackoverflow.com/questions/9035712/numpy-array-is-shown-incorrect-with-pyglet
def tex_from_m(m, resize=4):
    #m = m.T
    shape = m.shape

    m = np.clip(m, -1, 1)
    m += 1
    m /= 2

    m *= 255

    # we need to flatten the array
    m.shape = -1

    # convert to GLubytes
    tex_data = (gl.GLubyte * m.size)( *m.astype('uint8') )

    # create an image
    # pitch is 'texture width * number of channels per element * per channel size in bytes'
    img = pyglet.image.ImageData(shape[1], shape[0], "I", tex_data, pitch = shape[1] * 1 * 1)

    texture = img.get_texture()   
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)   

    texture.width = shape[1] * resize                                                                                                                                                            
    texture.height = -shape[0] * resize                                                                                                                                                                                                                                                                                                                       
    return texture

# Some code from https://github.com/pybox2d/pybox2d framework
class Window(pyglet.window.Window):
    def __init__(self, *args, **kwargs):
        super(Window, self).__init__(*args, **kwargs)
        self.clock = pyglet.clock.get_default()
        self.reset_keys()
        self.mouse_pressed = False
        self.mouse = (0, 0)
        self.label = None
        self.texture_cache = None # used for rendering weight/grad matrices
        self.set_line_width(3.0)
        pyglet.gl.glPointSize(2.0)
	self.particle_batch = None

    def set_fps(self, fps=60):
        self.clock.set_fps_limit(fps)
    
    def set_line_width(self, width):
        pyglet.gl.glLineWidth(width)

    def pressed(self, key):
        if key in self.keys:
            return True
        return False

    def on_mouse_press(self, x, y, button, modifiers):
        if button & mouse.LEFT:
            self.mouse_pressed = True

    def on_mouse_release(self, x, y, button, modifiers):
        self.mouse_pressed = False

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.mouse = (x, y)
        self.dx = dx
        self.dy = dy

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse = (x, y)
        self.dx = dx
        self.dy = dy

    def on_key_press(self, symbol, modifiers):
        self.keys[symbol] = True

    def on_key_release(self, symbol, modifiers):
        pass

    def reset_keys(self):
        self.keys = {}

    def set_particles(self, particles):
        self.particles = []
        self.particle_batch = graphics.Batch()

        for p in particles:
            c = np.random.randint(126, 256)
            new_p = self.particle_batch.add(1, gl.GL_POINTS, None, 
                ('v2f/stream', p), ('c3B', (c, c, c)))
            self.particles += [new_p]

    def update_particles(self, particles):
        for i, p in enumerate(self.particles):
            v = p.vertices
            v[0] = particles[i][0]
            v[1] = particles[i][1]

    def line_loop(self, vertices):
        out = []
        for i in range(len(vertices) - 1):
            # 0,1  1,2  2,3 ... len-1,len  len,0
            out.extend(vertices[i])
            out.extend(vertices[i + 1])

        out.extend(vertices[len(vertices) - 1])
        out.extend(vertices[0])

        return len(out) // 2, out

    def triangle_fan(self, vertices):
        out = []
        for i in range(1, len(vertices) - 1):
            # 0,1,2   0,2,3  0,3,4 ..
            out.extend(vertices[0])
            out.extend(vertices[i])
            out.extend(vertices[i + 1])
        return len(out) // 2, out

    def draw_poly(self, vertices, color):
        ll_count, ll_vertices = self.line_loop(vertices)

        pyglet.graphics.draw(ll_count, gl.GL_LINES,
                        ('v2f', ll_vertices),
                        ('c4f', [color[0], color[1], color[2], 1] * (ll_count)))

    def draw_poly_fill(self, vertices, color):
        tf_count, tf_vertices = self.triangle_fan(vertices)
        if tf_count == 0:
            return

        pyglet.graphics.draw(tf_count, gl.GL_TRIANGLES,
                        ('v2f', tf_vertices),
                        ('c4f', [0.5 * color[0], 0.5 * color[1], 0.5 * color[2], 0.5] * (tf_count)))

        """ll_count, ll_vertices = self.line_loop(vertices)

        pyglet.graphics.draw(ll_count, gl.GL_LINES,
                        ('v2f', ll_vertices),
                        ('c4f', [color[0], color[1], color[2], 1.0] * ll_count))"""
    
    def draw_rect(self, x, y, w, h, color, thickness=1):
        verts = ((x, y), (x+w, y), (x+w, y+h), (x, y+h), (x, y))
        if thickness > 0:
            # edges only
            self.draw_poly(verts, color)
        else:
            # full
            self.draw_poly_fill(verts, color)

    def draw_point(self, point, color=(255, 255, 255)):
        pyglet.graphics.draw(1, pyglet.gl.GL_POINTS,
            ('v2f', point),
            ('c3B', color)
        )

    def draw_text(self, text, size=18, p=None):
        p = (10, 10) if not p else p
        self.label = pyglet.text.Label(text,
                          font_name='monospace',
                          font_size=size,
                          x=p[0], y=p[1],
                          anchor_x='left', anchor_y='bottom')
        
    def draw_matrices(self, M, x=10, y=710, recalc=True):
        if recalc:
            self.texture_cache = None

        if not self.texture_cache:
            self.texture_cache = [tex_from_m(m) for m in M]

        for t in self.texture_cache:
            t.blit(x, y)
            x += t.width + 10

    def update(self):
        if self.has_exit:
            self.close()
            return False

        if self.label:
            self.label.draw()

        if self.particle_batch:
            self.particle_batch.draw()

        self.dispatch_events()
        self.dispatch_event('on_draw')
        self.flip()

        return True
