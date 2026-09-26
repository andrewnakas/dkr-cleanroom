// Dev hooks for headless tests: the page's ?script= sequencer waits on the
// game's current menu before pressing keys (menu ids: src/menu.h MENU_ID).
#include <emscripten.h>

extern int gCurrentMenuId;

EMSCRIPTEN_KEEPALIVE int dev_menu_id(void) {
    return gCurrentMenuId;
}
