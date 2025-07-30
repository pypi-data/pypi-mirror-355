"""
imantodes: light-weight python code for interactive scivis
Copyright © 2025. University of Chicago
SPDX-License-Identifier: LGPL-3.0-only

event.py:
Minimalist way of working with events for interactive applications.
"""

from enum import Enum
import math

# import PySide6.QtConcurrent # HEY why was this here?


class EventType(Enum):
    """The minimal set of events we currently know and care about."""

    UNKNOWN = 1
    MOUSE_DOWN = 2
    MOUSE_MOVE = 3
    MOUSE_UP = 4
    KEY = 5  # just key press (and its repetition if held down) but that's it


# keyboard modifiers of keys and mouse events: only two!
KMOD_SHIFT = 1 << 0   # shift key was held down
KMOD_SUPER = 1 << 1   # some other modifier key was down (command, control, option, whatever)
# "super" = h/t to Lisp super key https://en.wikipedia.org/wiki/Super_key_(keyboard_button)
# also visible in https://www.reddit.com/r/lisp/comments/9qk83h/lmicadr_lisp_machine_keyboard/


class Event:
    """Minimalist event representation"""

    def __init__(self):
        self.etyp = EventType.UNKNOWN
        # not integers because PySide (at least on Macs) can generate sub-pixel info
        self.x: float = math.nan
        self.y: float = math.nan
        self.char: str = ''   # for keyboard events
        self.kmods: int = 0   # bit field made of KMOD_SHIFT and/or KMOD_OTHER

    @staticmethod
    def isnum(vv):
        """dumb helper function to see if value is a finite number"""
        return isinstance(vv, int) or (isinstance(vv, float) and math.isfinite(vv))

    @classmethod
    def mouse(cls, etyp, x, y, kmods=0):
        """Create a mouse event with Event.mouse()"""
        metypes = [
            EventType.MOUSE_DOWN,
            EventType.MOUSE_MOVE,
            EventType.MOUSE_UP,
        ]
        if etyp not in metypes:
            raise ValueError(f'event type {etyp} not in {metypes}')
        if not (Event.isnum(x) and Event.isnum(y)):
            raise ValueError(f'cursor coords (x,y)=({x},{y}) not both finite')
        if not isinstance(kmods, int):
            raise ValueError(f'keyboard modifer bitflag {kmods} not int')
        ret = cls()
        ret.etyp = etyp
        ret.x = x
        ret.y = y
        ret.kmods = int(kmods) % 4   # map to valid set of modifiers
        return ret

    @classmethod
    def key(cls, etyp, char, kmods=0):
        """Create a key event with Event.key()"""
        if etyp != EventType.KEY:
            raise ValueError(f'event type {etyp} not == {EventType.KEY}')
        if not isinstance(char, str):
            raise ValueError(f'keyboard entry {char} not string')
        if not isinstance(kmods, int):
            raise ValueError(f'keyboard modifer bitflag {kmods} not int')
        ret = cls()
        ret.etyp = etyp
        # should be a single character except for arrow keys: 'up', 'down', 'left', 'right'
        ret.char = char
        ret.kmods = int(kmods) % 4   # map to valid set of modifiers
        return ret

    @staticmethod
    def kmods_str(kmods):
        """Concise string showing modifier keys"""
        kmods = kmods % 4
        return ('super-' if kmods & KMOD_SUPER else '') + ('shift-' if kmods & KMOD_SHIFT else '')

    def __str__(self):
        match self.etyp:
            case EventType.UNKNOWN:
                ret = 'event_unknown!'
            case EventType.KEY:
                ret = f'{Event.kmods_str(self.kmods)}key({self.char})'
            case EventType.MOUSE_DOWN | EventType.MOUSE_MOVE | EventType.MOUSE_UP:
                wut = {
                    EventType.MOUSE_DOWN: 'down',
                    EventType.MOUSE_MOVE: 'move',
                    EventType.MOUSE_UP: 'up',
                }[self.etyp]
                ret = f'{Event.kmods_str(self.kmods)}mouse{wut}({self.x},{self.y})'
        return ret


# -------- QT-specific stuff is below here; should be moved to a separate file ----------
# (ChatGPT helped write this)

# pylint: disable=no-name-in-module
import PySide6
from PySide6.QtCore import Qt
from PySide6.QtCore import QEvent

# pylint: enable=no-name-in-module

# from code import InteractiveConsole
# InteractiveConsole(locals=locals()).interact('Debugging ...')


def _kmods(qevent):
    """Map from the .modifiers() of a given `qevent` to our simple modifiers int"""
    ret = 0
    qmods = qevent.modifiers()
    if qmods & Qt.KeypadModifier:
        # arrow keys seem to always come with keypad modifier; don't care; remove it
        qmods = qmods ^ Qt.KeypadModifier
    if qmods & Qt.ShiftModifier:
        # in given bitflag, 'shift' was on, return that and turn it off
        qmods = qmods ^ Qt.ShiftModifier
        ret = ret | KMOD_SHIFT
    if qmods:
        # Some/any other modifier was on, so turn on 'super'
        ret = ret | KMOD_SUPER
    return ret


def _kchar(qevent):
    """Convert a QT key event to the key pressed.
    If a length-1 string is returned, that is the key that was pressed (though shifted printable
    keys are returned with the shifting: 'e' --> 'E' and '4' --> '$').
    If a length>1 string is returned:
        if it starts with '\' :'\t' for tab, '\r' for return, '\b' for delete or backspace
            (shift-tab for backtab is also mapped to '\t')
        else it describes the arrow key pressed: 'up', 'down', 'left', or 'right'
    If the empty string is returned, we don't understand or care what the key pressed was
    (e.g. the key press event for a modifier key itself)"""
    text = qevent.text()
    # print(f'_kchar: {text=} {text.isprintable()=} {len(text)=}')
    if text:
        if text.isprintable() and len(text) == 1:
            return text  # Good simple result
        if text == '\t':   # tab
            return '\\t'
        if text == '\r':   # return
            return '\\r'
    # else things are more annoying
    key = qevent.key()
    # print(f'_kchar: {key=}')
    ret = ''
    if key in [Qt.Key_Delete, Qt.Key_Backspace]:
        ret = '\\b'   # map both delete backspace to same thing
    elif key == Qt.Key_Backtab and qevent.modifiers() & Qt.ShiftModifier:
        # user pressed shift-tab, record that instead of backtab
        # (caller will already know that shift was pressed)
        ret = '\\t'
    # for the arrow keys, we return length > 1 strings
    elif key == Qt.Key_Left:
        ret = 'left'
    elif key == Qt.Key_Right:
        ret = 'right'
    elif key == Qt.Key_Up:
        ret = 'up'
    elif key == Qt.Key_Down:
        ret = 'down'
    # Handle letter keys (Qt.Key_A to Qt.Key_Z)
    elif Qt.Key_A <= key <= Qt.Key_Z:
        # without the .lower(); (on mac) Option-e is key 'E'
        ret = chr(key).lower()
    # Handle number keys (Qt.Key_0 to Qt.Key_9)
    elif Qt.Key_0 <= key <= Qt.Key_9:
        ret = chr(key)
    # Handle space (very likely redundant with isprintable test above)
    elif key == Qt.Key_Space:
        ret = ' '
    # else we don't know how to interpret this, so we return empty string
    # print(f'_kchar: {ret=}')
    return ret


# the TKinter-specific version of this function could define `convert(tkevent)`
# (but with same `convert` name so that our code can be agnostic to toolkit)
def convert(qevent):
    """Create simple event representation from QEvent craziness"""
    # print(f'convert: incoming QEvent = {qevent}')
    kmods = _kmods(qevent)
    ret = None
    # pylint: disable-next=c-extension-no-member
    if isinstance(qevent, PySide6.QtGui.QMouseEvent):
        etyp = {  # mapping from QT mouse event type to our event type
            QEvent.MouseButtonPress: EventType.MOUSE_DOWN,
            # this is where handling double-clicking could start
            QEvent.MouseButtonDblClick: EventType.MOUSE_DOWN,
            QEvent.MouseMove: EventType.MOUSE_MOVE,
            QEvent.MouseButtonRelease: EventType.MOUSE_UP,
        }[qevent.type()]
        pos = qevent.position()
        ret = Event.mouse(etyp, pos.x(), pos.y(), kmods)
    elif qevent.type() == QEvent.KeyPress:
        char = _kchar(qevent)
        # print(f'convert: {char=}')
        if char:
            # only care if recovered char != '' (it is '' if e.g. modifier key pressed)
            # print(f'key press {char=}')
            ret = Event.key(EventType.KEY, char, kmods)
    # else not an event we know about or care about
    # print(f'convert: returning {str(ret)}')
    return ret
