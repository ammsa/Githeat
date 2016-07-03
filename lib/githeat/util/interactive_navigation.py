"""
Navigation functions for interactive githeat
"""
import collections


Cursor = collections.namedtuple('Cursor', ('y', 'x', 'term'))

above = lambda csr, n: (
    Cursor(y=max(0, csr.y - n),
           x=csr.x,
           term=csr.term))

below = lambda csr, n: (
    Cursor(y=min(csr.term.height - 1, csr.y + n),
           x=csr.x,
           term=csr.term))

right_of = lambda csr, n: (
    Cursor(y=csr.y,
           x=min(csr.term.width - 1, csr.x + n),
           term=csr.term))

left_of = lambda csr, n: (
    Cursor(y=csr.y,
           x=max(0, csr.x - n),
           term=csr.term))

home = lambda csr: (
    Cursor(y=csr.y,
           x=0,
           term=csr.term))

end = lambda csr: (
    Cursor(y=csr.y,
           x=csr.term.width - 1,
           term=csr.term))

bottom = lambda csr: (
    Cursor(y=csr.term.height - 1,
           x=csr.x,
           term=csr.term))

top = lambda csr: (
    Cursor(y=0,
           x=csr.x,
           term=csr.term))

center = lambda csr: Cursor(
        csr.term.height // 2,
        csr.term.width // 2,
        csr.term)

lookup_move = lambda inp_code, csr, term, githeat: {
    # arrows, including angled directionals
    csr.term.KEY_END: below(left_of(csr, 1), 1),
    csr.term.KEY_KP_1: below(left_of(csr, 1), 1),

    csr.term.KEY_DOWN: below(csr, 1),
    csr.term.KEY_KP_2: below(csr, 1),

    csr.term.KEY_PGDOWN: below(right_of(csr, 1), 1),
    csr.term.KEY_LR: below(right_of(csr, 1), 1),
    csr.term.KEY_KP_3: below(right_of(csr, 1), 1),

    csr.term.KEY_LEFT: left_of(csr, len(githeat.width)),
    csr.term.KEY_KP_4: left_of(csr, len(githeat.width)),

    csr.term.KEY_CENTER: center(csr),
    csr.term.KEY_KP_5: center(csr),

    csr.term.KEY_RIGHT: right_of(csr, len(githeat.width)),
    csr.term.KEY_KP_6: right_of(csr, len(githeat.width)),

    csr.term.KEY_HOME: above(left_of(csr, 1), 1),
    csr.term.KEY_KP_7: above(left_of(csr, 1), 1),

    csr.term.KEY_UP: above(csr, 1),
    csr.term.KEY_KP_8: above(csr, 1),

    csr.term.KEY_PGUP: above(right_of(csr, 1), 1),
    csr.term.KEY_KP_9: above(right_of(csr, 1), 1),

    # shift + arrows
    csr.term.KEY_SLEFT: left_of(csr, 9),
    csr.term.KEY_SRIGHT: right_of(csr, 9),
    csr.term.KEY_SDOWN: below(csr, 4),
    csr.term.KEY_SUP: above(csr, 4),

    # carriage return
    # csr.term.KEY_ENTER: home(below(csr, 1)),
}.get(inp_code, csr)

