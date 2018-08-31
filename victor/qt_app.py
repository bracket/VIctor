import sys
import numpy as np
import array

from math import sqrt

from PyQt5.QtCore import QEvent

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
    # QGuiApplication,
    # QLabel,
    QMatrix4x4,
    QOpenGLContext,
    QOpenGLShader,
    QOpenGLShaderProgram,
    QSurfaceFormat,
    QWindow,
)


class QTVictorApplication(QApplication):
    def __init__(self):
        super().__init__(sys.argv)

        window = self.window = QWidget()

        window.setGeometry(300, 300, 512 + 150, 512)
        window.setWindowTitle('victor')

        size_policy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        canvas = QLabel('Canvas', window)

        canvas_policy = QSizePolicy(    
            QSizePolicy.MinimumExpanding,
            QSizePolicy.MinimumExpanding,
        )

        canvas.setSizePolicy(canvas_policy)
        canvas.setFrameStyle(QFrame.Box | QFrame.Plain)
        canvas.setLineWidth(1)
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
        hbox.addWidget(info)

        window.show()

    def run(self):
        self.window.show()
        return self.exec_()


class QTVictorGLWindow(QWindow):
    def __init__(self, app, parent=None):
        super().__init__(parent)

        self.app = app

        self.gl_context = None
        self.gl = None

        self.animating = False
        self.update_pending = False

        self.setSurfaceType(QWindow.OpenGLSurface)


    def initialize(self):
        pass


    def render_later(self):
        if self.update_pending:
            return

        self.update_pending = True
        self.app.postEvent(self, QEvent(QEvent.UpdateRequest))


    def render_now(self):
        if not self.isExposed():
            return

        self.update_pending = False

        if self.gl_context is None:
            self.gl_context = QOpenGLContext(self)
            self.gl_context.setFormat(self.requestedFormat())
            self.gl_context.create()

        self.gl_context.makeCurrent(self)

        if self.gl is None:
            self.gl = self.gl_context.versionFunctions()
            self.gl.initializeOpenGLFunctions()

            self.initialize()

        self.render(self.gl)
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
        self.render_now()


    def render(self, gl):
        pass


class TestWindow(QTVictorGLWindow):
    def __init__(self, app, parent=None):
        super().__init__(app, parent)

        self.frame_no = 0

        self.program = None

        self.posAttr = None
        self.colAttr = None
        self.matrixUniform = None


    def initialize(self):
        if self.program:
            return

        self.program = QOpenGLShaderProgram(self)

        self.program.addShaderFromSourceCode(
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

        self.program.addShaderFromSourceCode(
            QOpenGLShader.Fragment,
            r'''
                varying lowp vec4 col;

                void main() {
                    gl_FragColor = col;
                }
            '''
        )

        self.program.link()

        self.posAttr = self.program.attributeLocation('posAttr')
        self.colAttr = self.program.attributeLocation('colAttr')
        self.matrixUniform = self.program.uniformLocation('matrix')


    def render(self, gl):
        gl.glViewport(0, 0, self.width(), self.height())

        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        self.program.bind()

        matrix = QMatrix4x4()
        matrix.perspective(60, 4/3, .1, 100.)
        matrix.translate(0, 0, -2)

        matrix.rotate(
            100 * self.frame_no / self.screen().refreshRate(),
            0, 1, 0
        )

        self.program.setUniformValue(self.matrixUniform, matrix)

        vertices = np.array([
            [ 0,   sqrt(2)/2 ],
            [ -.5, -.5 ],
            [ 0.5, -.5 ],
        ], dtype=np.float32)

        v = array.array('f')
        v.frombytes(vertices.tobytes())

        colors = np.array([
            [ 1, 0, 0 ],
            [ 0, 1, 0 ],
            [ 0, 0, 1 ],
        ], dtype=np.float32)

        c = array.array('f')
        c.frombytes(colors.tobytes())

        gl.glVertexAttribPointer(self.posAttr, 2, gl.GL_FLOAT, False, 0, v)
        gl.glEnableVertexAttribArray(self.posAttr)

        gl.glVertexAttribPointer(self.colAttr, 3, gl.GL_FLOAT, False, 0, c)
        gl.glEnableVertexAttribArray(self.colAttr)

        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 3)

        self.program.release()

        self.frame_no += 1
