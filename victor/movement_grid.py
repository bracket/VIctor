from itertools import chain

import array
import numpy as np

from PyQt5.QtGui import (
    QMatrix4x4,
)

__all__ = [ 'MovementGrid' ]

scales = (1, 5, 10, 20, 40, 80)


class MovementGrid(object):
    def __init__(self, width, height, color = (127, 127, 127 , 127)):  
        self.width = width
        self.height = height

        self.scale = 3
        self.visible = True

        c = np.array(color, dtype=np.float32)
        self.color = array.array('f')
        c.frombytes(c.tobytes())

        self.program = None
        self.shader_indices = None


    def compile_program(self):
        if self.program:
            return

        self.program = program = QOpenGLShaderProgram(self)

        program.addShaderFromSourceCode(
            QOpenGLShader.Vertex,
            r'''
                uniform   highp mat4 xform;
                attribute highp vec4 position;

                void main() {
                    gl_Position = xform * position;
                }
            '''
        )

        program.addShaderFromSourceCode(
            QOpenGLShader.Fragment,
            r'''
                uniform lowp vec4 color;

                void main() {
                    gl_FragColor = color;
                }
            '''
        )

        program.link()

        self.shader_indices = indices = {  }

        indices['xform']    = program.uniformLocation('xform')
        indices['position'] = program.attributeLocation('position')
        indices['color']    = program.uniformLocation('color')

    
    def generate_vertices(self):
        if self.vertices:
            return

        scale = scales[self.scale]

        v = [ ]

        for i in range(scale, self.width, scale):
            v.append((i, -scale, 0, 1))
            v.append((i, self.height + scale, 0, 1))

        for j in range(scale, self.height, scale):
            v.append((-scale, j, 0, 1))
            v.append((self.width + scale, j, 0, 1))

        v = np.array(v, np.float32)

        self.vertices = vertices = array.array('f')
        vertices.frombytes(v.tobytes())


    def render(self, gl):
        if not self.visible:
            return

        self.generate_vertices()
        self.compile_program()

        self.program.bind()

        matrix = QMatrix4x4()

        matrix.ortho(-width, width, -height, height, .1, 100.)
        matrix.translate(0, 0, -3)

        indices = self.indices

        gl.setUniformValue(indices['matrix'], matrix)
        gl.setUniformValue(indices['color'], self.color)

        gl.glVertexAttribPointer(
            indices['position'], 4, gl.GL_FLOAT,
            False, 0, self.vertices
        )

        self.program.release()


    def toggle_visibility(self):
        if self.scale == 0:
            self.scale_up()
        elif self.scale == 1:
            self.scale_down()
        else:
            self.visible = not self.visible


    def scale_up(self):
        self.scale = min(self.scale + 1, len(scales) - 1)

        if self.scale >= 1 and not self.visible:
            self.visible = True

        self.vertices = None


    def scale_down(self):
        self.scale = max(self.scale - 1, 0)

        if self.scale < 1 and self.visible:
            self.visible = False

        self.vertices = None


    def clamp_left_down(self, pos):
        scale = scales[self.scale]
        return scale * (pos // scale)


    def up(self, pos, multiplier=1):
        scale = scales[self.scale]
        return self.clamp_left_down(pos + vec2f(0., scale * multiplier))


    def right(self, pos, multiplier=1):
        scale = scales[self.scale]
        return self.clamp_left_down(pos + vec2f(scale * multiplier, 0))


    def left(self, pos, multiplier=1):
        scale = scales[self.scale]
        return self.clamp_left_down(pos - vec2f(.01 + scale*(multiplier - 1), 0))


    def down(self, pos, multiplier=1):
        scale = scales[self.scale]
        return self.clamp_left_down(pos - vec2f(0, .01 + scale*(multiplier - 1)))
