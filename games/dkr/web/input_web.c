// Web input for the DKR PC port: keyboard (SDL) plus the browser Gamepad API
// (standard mapping). Replaces linux/input.c.
#include "../linux/input.h"

#include <math.h>
#include <SDL2/SDL.h>
#include <emscripten.h>
#include <emscripten/html5.h>

#define BTN_A 0x8000
#define BTN_B 0x4000
#define BTN_Z 0x2000
#define BTN_START 0x1000
#define BTN_UP 0x0800
#define BTN_DOWN 0x0400
#define BTN_LEFT 0x0200
#define BTN_RIGHT 0x0100
#define BTN_L 0x0020
#define BTN_R 0x0010
#define BTN_CUP 0x0008
#define BTN_CDOWN 0x0004
#define BTN_CLEFT 0x0002
#define BTN_CRIGHT 0x0001

#define STICK_MAX 80
#define STICK_DIAG 57

typedef struct {
    int scancode;
    unsigned short button;
} KeyBinding;

static const KeyBinding sKeyBindings[] = {
    { SDL_SCANCODE_X, BTN_A },      // accelerate
    { SDL_SCANCODE_C, BTN_B },      // brake / reverse
    { SDL_SCANCODE_Z, BTN_Z },      // fire weapon
    { SDL_SCANCODE_SPACE, BTN_R },  // hop / powerslide
    { SDL_SCANCODE_LSHIFT, BTN_R },
    { SDL_SCANCODE_Q, BTN_L },
    { SDL_SCANCODE_RETURN, BTN_START },
    { SDL_SCANCODE_I, BTN_CUP },
    { SDL_SCANCODE_K, BTN_CDOWN },
    { SDL_SCANCODE_J, BTN_CLEFT },
    { SDL_SCANCODE_L, BTN_CRIGHT },
};

#define NUM_KEY_BINDINGS (int) (sizeof(sKeyBindings) / sizeof(sKeyBindings[0]))

// Gamepad API "standard" layout -> N64 buttons.
static const unsigned short sPadButtons[17] = {
    BTN_A,      // 0  A / cross
    BTN_CDOWN,  // 1  B / circle
    BTN_B,      // 2  X / square
    BTN_CUP,    // 3  Y / triangle
    BTN_L,      // 4  LB
    BTN_R,      // 5  RB
    BTN_Z,      // 6  LT
    BTN_R,      // 7  RT
    0,          // 8  back
    BTN_START,  // 9  start
    0, 0,       // 10, 11 stick clicks
    BTN_UP, BTN_DOWN, BTN_LEFT, BTN_RIGHT, // 12-15 d-pad
    0,
};

static int axis_value(const unsigned char *keys, int negA, int negB, int posA, int posB) {
    int value = 0;

    if (keys[negA] || keys[negB]) {
        value -= 1;
    }
    if (keys[posA] || keys[posB]) {
        value += 1;
    }
    return value;
}

static int sPadInit = 0;

static void read_pad(unsigned short *buttons, int *sx, int *sy) {
    EmscriptenGamepadEvent st;
    int n, p, i;

    if (!sPadInit) {
        sPadInit = 1;
    }
    if (emscripten_sample_gamepad_data() != EMSCRIPTEN_RESULT_SUCCESS) {
        return;
    }
    n = emscripten_get_num_gamepads();
    for (p = 0; p < n; p++) {
        if (emscripten_get_gamepad_status(p, &st) != EMSCRIPTEN_RESULT_SUCCESS || !st.connected) {
            continue;
        }
        for (i = 0; i < st.numButtons && i < 17; i++) {
            if (st.digitalButton[i] || st.analogButton[i] > 0.5) {
                *buttons |= sPadButtons[i];
            }
        }
        if (st.numAxes >= 2) {
            double x = st.axis[0], y = -st.axis[1];
            double m = sqrt(x * x + y * y);
            if (m > 0.15) {
                double k = (m - 0.15) / 0.85 / m;
                if (k * m > 1.0) {
                    k = 1.0 / m;
                }
                *sx = (int) (x * k * STICK_MAX);
                *sy = (int) (y * k * STICK_MAX);
            }
        }
        if (st.numAxes >= 4) {
            if (st.axis[2] < -0.5) *buttons |= BTN_CLEFT;
            if (st.axis[2] > 0.5) *buttons |= BTN_CRIGHT;
            if (st.axis[3] < -0.5) *buttons |= BTN_CUP;
            if (st.axis[3] > 0.5) *buttons |= BTN_CDOWN;
        }
        break; // first connected pad drives player 1
    }
}

// Touch overlay (web/touchpad.js): N64 button mask and analog stick, set from JS.
static unsigned short sTouchButtons = 0;
static int sTouchX = 0, sTouchY = 0;

EMSCRIPTEN_KEEPALIVE void web_touch_input(int buttons, int x, int y) {
    sTouchButtons = (unsigned short) buttons;
    sTouchX = x < -STICK_MAX ? -STICK_MAX : (x > STICK_MAX ? STICK_MAX : x);
    sTouchY = y < -STICK_MAX ? -STICK_MAX : (y > STICK_MAX ? STICK_MAX : y);
}

void input_host_read(unsigned short *button, signed char *stickX, signed char *stickY) {
    const unsigned char *keys;
    unsigned short buttons = 0;
    int x, y, px = 0, py = 0;
    int magnitude;
    int i;

    *button = 0;
    *stickX = 0;
    *stickY = 0;

    if (!SDL_WasInit(SDL_INIT_VIDEO)) {
        return;
    }
    keys = SDL_GetKeyboardState(NULL);
    for (i = 0; i < NUM_KEY_BINDINGS; i++) {
        if (keys[sKeyBindings[i].scancode]) {
            buttons |= sKeyBindings[i].button;
        }
    }
    x = axis_value(keys, SDL_SCANCODE_LEFT, SDL_SCANCODE_A, SDL_SCANCODE_RIGHT, SDL_SCANCODE_D);
    y = axis_value(keys, SDL_SCANCODE_DOWN, SDL_SCANCODE_S, SDL_SCANCODE_UP, SDL_SCANCODE_W);
    magnitude = (x != 0 && y != 0) ? STICK_DIAG : STICK_MAX;
    x *= magnitude;
    y *= magnitude;

    read_pad(&buttons, &px, &py);
    if (x == 0 && y == 0) {
        x = px;
        y = py;
    }
    buttons |= sTouchButtons;
    if (x == 0 && y == 0) {
        x = sTouchX;
        y = sTouchY;
    }
    *button = buttons;
    *stickX = (signed char) x;
    *stickY = (signed char) y;
}
