"""DKR-specific stroke glyph designs (our own), patched into the shared stroke
font for this game's text: an 8 made of two stacked loops (the shared boxed 8
reads as B at HUD sizes) and a 0 as a narrow rounded loop without a slash."""
from cleanroom.gfx import strokefont

GLYPHS = {
    "8": [[(1, 0), (3, 0), (4, 0.8), (4, 2.2), (3, 3), (1, 3), (0, 2.2), (0, 0.8), (1, 0)],
          [(1, 3), (3, 3), (4, 3.8), (4, 5.2), (3, 6), (1, 6), (0, 5.2), (0, 3.8), (1, 3)]],
    "0": [[(1.2, 0), (2.8, 0), (4, 1.2), (4, 4.8), (2.8, 6), (1.2, 6), (0, 4.8), (0, 1.2), (1.2, 0)]],
}


def install():
    strokefont.G.update(GLYPHS)


install()
