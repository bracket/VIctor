import pyglet

from .app import VIctorApp

pyglet.resource.path = [ 'resource' ]
window = VIctorApp()
pyglet.app.run()
