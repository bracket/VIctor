import collections
import pyglet
import pyglet.window.key as pkey
import re, sys


import victor.mode as vmode
from victor.command_area import CommandArea
from victor.cursor import Cursor
from victor.keystroke import Keystrokes
from victor.command import run_ex_command;
from victor.normal_command import run_normal_command;

from victor.command import CommandException, register_ex_command, run_ex_command;

class VIctorApp(pyglet.window.Window):

    def __init__(self, *args, **kwargs):
        super(VIctorApp, self).__init__(640, 400, caption="VI-llustrator")

        self.mode = vmode.COMMAND

        self.batch = pyglet.graphics.Batch()
        self.command_area = CommandArea(0, 0, 550, self.batch)
        self.keystrokes = Keystrokes(550, 0, 70, self.batch)
        self.cursor = Cursor(320, 200, self.batch)

        self.marks = dict()

        self.is_movement_scheduled = False
        self.frame = 0

        self.set_ex_commands()

    def set_ex_commands(self):
        register_ex_command('line', self.draw_line);
        register_ex_command('marks', self.show_marks);

    def set_mode(self, mode):
        if self.is_ex_mode():
            self.command_area.unfocus()

        self.mode = mode

        if mode == vmode.EX:
            self.command_area.focus()

    def run_command(self):
        try: run_ex_command(self.command_area.text);
        except CommandException as e: sys.stderr.write('%s\n' % str(e));
        self.set_mode(vmode.COMMAND)

    def on_key_press(self, symbol, modifiers):
        is_mod_key = lambda key, mod: symbol == key and modifiers & mod

        if self.is_ex_mode() and symbol == pkey.ENTER:
            self.run_command()

        elif self.is_command_mode() and is_mod_key(pkey.SEMICOLON, pkey.MOD_SHIFT):
            self.set_mode(vmode.EX)

        elif symbol == pkey.ESCAPE or is_mod_key(pkey.BRACKETLEFT, pkey.MOD_CTRL):
            if not self.is_command_mode(): self.set_mode(vmode.COMMAND)
            self.keystrokes.push_text("^[")
            pyglet.clock.schedule_once(self.keystrokes.clear_text, 1.0)

            # don't close window
            return pyglet.event.EVENT_HANDLED

        elif self.is_command_mode():
            run_normal_command(self)


    def on_text(self, text):
        if self.is_ex_mode():
            self.command_area.on_text(text)
        elif self.is_command_mode():
            self.keystrokes.push_text(text)

    def on_text_motion(self, motion):
        if self.is_ex_mode():
            self.command_area.on_text_motion(motion)

    def current_position(self):
        return (self.cursor.x, self.cursor.y)

    def draw_line(self, *args):
        if len(args) != 2:
            self.error("line requires two arguments", args)
        else:
            start = self.marks[args[0]]
            end = self.marks[args[1]]

            self.batch.add(2, pyglet.gl.GL_LINES, None,
                ('v2i', (start[0], start[1], end[0], end[1])),
                ('c4B', (255, 0, 0, 255, 255, 0, 0, 255)))

    def show_marks(self, *args):
        for key, value in self.marks.iteritems():
            print key, value

    def error(self, *args):
        print args

    def on_draw(self):
#        self.frame += 1
#        sys.stdout.write(" frame: %i\r" % self.frame)
#        sys.stdout.flush()

        pyglet.gl.glClearColor(1, 1, 1, 1)
        self.clear()
        self.batch.draw()

    def is_command_mode(self):
        return self.mode == vmode.COMMAND

    def is_ex_mode(self):
        return self.mode == vmode.EX
