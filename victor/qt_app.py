import sys
import numpy as np
import array

from math import cos, sin, sqrt, pi

from .util import method_cache

from PyQt5.QtCore import (
    QEvent,
    QRect,
)

from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QSizePolicy,
    QSpacerItem,
    QWidget,
)

from PyQt5.QtGui import (
    QMatrix4x4,
    QOpenGLContext,
    QOpenGLShader,
    QOpenGLShaderProgram,
    QOpenGLVersionProfile,
    QSurfaceFormat,
    QWindow,
)


class QTVictorApplication(QApplication):
    def __init__(self):
        super().__init__(sys.argv)

        window = self.window = QWidget()

        window.setGeometry(300, 300, 512 + 150, 512)
        window.setWindowTitle('victor')

        gl_window = QTVictorGLWindow(self)

        canvas = QWidget.createWindowContainer(gl_window)

        canvas_policy = QSizePolicy(
            QSizePolicy.MinimumExpanding,
            QSizePolicy.MinimumExpanding,
        )

        canvas.setSizePolicy(canvas_policy)
        canvas.setMinimumWidth(512)
        canvas.setMinimumHeight(512)

        info_policy = QSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.MinimumExpanding,
        )

        info = QLabel('Info')
        info.setSizePolicy(info_policy)
        info.setMinimumWidth(150)
        info.setMinimumHeight(512)
        info.setFrameStyle(QFrame.Box | QFrame.Plain)
        info.setLineWidth(1)

        hbox = QHBoxLayout(window)
        hbox.addWidget(canvas)
        # hbox.addWidget(info)

        window.show()


    def run(self):
        self.window.show()
        return self.exec_()


class QTVictorGLWindow(QWindow):
    memoize = method_cache()

    def __init__(self, app, parent=None):
        super().__init__(parent)

        self.app = app

        self.animating = False
        self.update_pending = False

        self.setSurfaceType(QWindow.OpenGLSurface)

        self.height_scale = 1.
        self.width_scale = 1.
        self.zoom = 1/3.

        self.frame_no = 0


    @property
    @memoize
    def program(self):
        print('hi')
        program = QOpenGLShaderProgram(self)

        program.addShaderFromSourceCode(
            QOpenGLShader.Vertex,
            r'''
                attribute highp vec4 posAttr;
                attribute lowp  vec4 colAttr;
                varying   lowp  vec4 col;
                uniform   highp mat4 matrix;

                void main() {
                    col = colAttr;
                    gl_Position = matrix * posAttr;
                }
            '''
        )

        program.addShaderFromSourceCode(
            QOpenGLShader.Fragment,
            r'''
                varying lowp vec4 col;

                void main() {
                    gl_FragColor = col;
                }
            '''
        )

        program.link()

        return program


    def render_later(self):
        if self.update_pending:
            return

        self.update_pending = True
        self.app.postEvent(self, QEvent(QEvent.UpdateRequest))


    @property
    @memoize
    def gl_context(self):
        gl_context = QOpenGLContext(self)
        gl_context.setFormat(self.requestedFormat())
        gl_context.create()

        return gl_context


    @property
    @memoize
    def gl(self):
        gl = self.gl_context.versionFunctions()
        gl.initializeOpenGLFunctions()

        return gl


    def render_now(self):
        if not self.isExposed():
            return

        self.update_pending = False

        self.gl_context.makeCurrent(self)

        self.render()
        self.gl_context.swapBuffers(self)

        self.render_later()


    def event(self, event):
        if event.type() == QEvent.UpdateRequest:
            self.render_now()
            return True

        return super().event(event)


    def exposeEvent(self, event):
        self.render_now()


    def resizeEvent(self, event):
        size = event.size()
        width, height = size.width(), size.height()

        self.height_scale = height / 512
        self.width_scale =  width / 512

        self.render_now()


    def render(self):
        self.gl.glClearColor(1., 1., 1., 1.)
        self.gl.glClear(self.gl.GL_COLOR_BUFFER_BIT)

        self.program.bind()

        matrix = QMatrix4x4()

        height = self.height_scale / 2 / self.zoom
        width  = self.width_scale / 2 / self.zoom

        matrix.ortho(-width, width, -height, height, .1, 100.)
        matrix.translate(0, 0, -3)

        matrix.rotate(
            100 * self.frame_no / self.screen().refreshRate(),
            0, 0, 1
        )

        matrix.translate(-.5, -.5, 0)

        matrixUniform = self.program.uniformLocation('matrix')
        self.program.setUniformValue(matrixUniform, matrix)

        half_pi = pi / 2
        delta = 2 * pi / 3

        vertices = np.array([
            [ 0, 0, ],
            [ 0, 1, ],
            [ 1, 1, ],
            [ 1, 0, ],
        ], dtype=np.float32)

        v = array.array('f')
        v.frombytes(vertices.tobytes())

        colors = np.array([
            [ 1, 0, 0 ],
            [ 0, 1, 0 ],
            [ 1, 0, 0 ],
            [ 0, 0, 1 ],
        ], dtype=np.float32)

        c = array.array('f')
        c.frombytes(colors.tobytes())

        posAttr = self.program.attributeLocation('posAttr')
        self.gl.glVertexAttribPointer(posAttr, 2, self.gl.GL_FLOAT, False, 0, v)
        self.gl.glEnableVertexAttribArray(posAttr)

        colAttr = self.program.attributeLocation('colAttr')
        self.gl.glVertexAttribPointer(colAttr, 3, self.gl.GL_FLOAT, False, 0, c)
        self.gl.glEnableVertexAttribArray(colAttr)

        self.gl.glDrawArrays(self.gl.GL_TRIANGLES, 0, 3)
        self.gl.glDrawArrays(self.gl.GL_LINE_LOOP, 0, 4)

        self.program.release()

        self.frame_no += 1
