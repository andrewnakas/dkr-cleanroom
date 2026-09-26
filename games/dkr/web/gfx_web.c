// WebGL 2 (GLES 3.0) backend for the DKR PC port's host GL layer (linux/gfx.h).
// Same interface and semantics as linux/gfx.c, but the fixed-function state that
// file relies on (texenv modulate/blend, alpha test, fog coordinate) is done in
// one small shader instead. Vertices arrive already projected; positions are
// multiplied back by w so the rasteriser interpolates perspective-correctly.
#include "../linux/gfx.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <SDL2/SDL.h>
#include <GLES3/gl3.h>
#include <emscripten.h>

static SDL_Window *sWindow;
static SDL_GLContext sContext;
static int sFbWidth = 320;
static int sFbHeight = 240;
static int sScale = 1;

static GLuint sProg, sVbo, sVao;
static GLint uUseTex, uBlend, uEnvColor, uFogOn, uFogColor, uAlphaRef, uProj;

// Shader-side copies of the fixed-function state.
static int sTexOn = 0;
static int sBlendMode = 0;
static float sEnv[4];
static int sFogOn = 0;
static float sFogCol[4];
static float sAlphaRef = 0.0f;
static GLuint sBound = 0;

static const char *kVs =
    "#version 300 es\n"
    "in vec4 aPos; in vec4 aCol; in vec2 aUv; in float aFog;\n"
    "uniform mat4 uProj;\n"
    "out vec4 vCol; out vec2 vUv; out float vFog;\n"
    "void main(){ gl_Position = uProj * aPos; vCol = aCol; vUv = aUv; vFog = aFog; }\n";

static const char *kFs =
    "#version 300 es\n"
    "precision mediump float;\n"
    "in vec4 vCol; in vec2 vUv; in float vFog;\n"
    "uniform sampler2D uTex; uniform int uUseTex; uniform int uBlend; uniform vec4 uEnvColor;\n"
    "uniform int uFogOn; uniform vec4 uFogColor; uniform float uAlphaRef;\n"
    "out vec4 oCol;\n"
    "void main(){\n"
    "  vec4 c = vCol;\n"
    "  if (uUseTex != 0) {\n"
    "    vec4 t = texture(uTex, vUv);\n"
    "    if (uBlend != 0) c = vec4(mix(vCol.rgb, uEnvColor.rgb, t.rgb), vCol.a * t.a);\n"
    "    else c = vCol * t;\n"
    "  }\n"
    "  if (!(c.a > uAlphaRef)) discard;\n"
    "  if (uFogOn != 0) { float f = clamp(1.0 - vFog, 0.0, 1.0); c.rgb = mix(uFogColor.rgb, c.rgb, f); }\n"
    "  oCol = c;\n"
    "}\n";

static GLuint compile(GLenum type, const char *src) {
    GLuint s = glCreateShader(type);
    GLint ok = 0;
    glShaderSource(s, 1, &src, NULL);
    glCompileShader(s);
    glGetShaderiv(s, GL_COMPILE_STATUS, &ok);
    if (!ok) {
        char log[1024];
        glGetShaderInfoLog(s, sizeof(log), NULL, log);
        fprintf(stderr, "GFX: shader error: %s\n", log);
    }
    return s;
}

void gfx_window_init(int width, int height, int scale) {
    float proj[16];
    GLuint vs, fs;

    sFbWidth = width;
    sFbHeight = height;
    sScale = scale;

    if (SDL_Init(SDL_INIT_VIDEO) != 0) {
        fprintf(stderr, "SDL_Init failed: %s\n", SDL_GetError());
        return;
    }
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_PROFILE_MASK, SDL_GL_CONTEXT_PROFILE_ES);
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 3);
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 0);
    SDL_GL_SetAttribute(SDL_GL_DEPTH_SIZE, 24);
    sWindow = SDL_CreateWindow("Diddy Kong Racing", 0, 0, width * scale, height * scale, SDL_WINDOW_OPENGL);
    if (sWindow == NULL) {
        fprintf(stderr, "SDL_CreateWindow failed: %s\n", SDL_GetError());
        return;
    }
    sContext = SDL_GL_CreateContext(sWindow);
    if (sContext == NULL) {
        fprintf(stderr, "SDL_GL_CreateContext failed: %s\n", SDL_GetError());
        sWindow = NULL;
        return;
    }

    vs = compile(GL_VERTEX_SHADER, kVs);
    fs = compile(GL_FRAGMENT_SHADER, kFs);
    sProg = glCreateProgram();
    glAttachShader(sProg, vs);
    glAttachShader(sProg, fs);
    glBindAttribLocation(sProg, 0, "aPos");
    glBindAttribLocation(sProg, 1, "aCol");
    glBindAttribLocation(sProg, 2, "aUv");
    glBindAttribLocation(sProg, 3, "aFog");
    glLinkProgram(sProg);
    glUseProgram(sProg);
    uUseTex = glGetUniformLocation(sProg, "uUseTex");
    uBlend = glGetUniformLocation(sProg, "uBlend");
    uEnvColor = glGetUniformLocation(sProg, "uEnvColor");
    uFogOn = glGetUniformLocation(sProg, "uFogOn");
    uFogColor = glGetUniformLocation(sProg, "uFogColor");
    uAlphaRef = glGetUniformLocation(sProg, "uAlphaRef");
    uProj = glGetUniformLocation(sProg, "uProj");
    glUniform1i(glGetUniformLocation(sProg, "uTex"), 0);

    // glOrtho(0, w, h, 0, -1, 1): N64 screen coordinates, origin top-left.
    memset(proj, 0, sizeof(proj));
    proj[0] = 2.0f / width;
    proj[5] = -2.0f / height;
    proj[10] = -1.0f;
    proj[12] = -1.0f;
    proj[13] = 1.0f;
    proj[15] = 1.0f;
    glUniformMatrix4fv(uProj, 1, GL_FALSE, proj);

    glGenVertexArrays(1, &sVao);
    glBindVertexArray(sVao);
    glGenBuffers(1, &sVbo);
    glBindBuffer(GL_ARRAY_BUFFER, sVbo);
    glEnableVertexAttribArray(0);
    glEnableVertexAttribArray(1);
    glEnableVertexAttribArray(2);
    glEnableVertexAttribArray(3);
    glVertexAttribPointer(0, 4, GL_FLOAT, GL_FALSE, sizeof(GfxTriVert), (void *) offsetof(GfxTriVert, x));
    glVertexAttribPointer(1, 4, GL_UNSIGNED_BYTE, GL_TRUE, sizeof(GfxTriVert), (void *) offsetof(GfxTriVert, r));
    glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, sizeof(GfxTriVert), (void *) offsetof(GfxTriVert, u));
    glVertexAttribPointer(3, 1, GL_FLOAT, GL_FALSE, sizeof(GfxTriVert), (void *) offsetof(GfxTriVert, fog));

    glViewport(0, 0, width * scale, height * scale);
    glEnable(GL_DEPTH_TEST);
    glDepthFunc(GL_LESS);
    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    glPolygonOffset(-1.0f, -1.0f);
    glActiveTexture(GL_TEXTURE0);
}

static GLint wrap_mode(int cm) {
    if (cm & 0x2) {
        return GL_CLAMP_TO_EDGE;
    }
    if (cm & 0x1) {
        return GL_MIRRORED_REPEAT;
    }
    return GL_REPEAT;
}

unsigned int gfx_create_texture(const void *rgba, int width, int height, int cmS, int cmT) {
    GLuint id = 0;

    if (sWindow == NULL) {
        return 0;
    }
    glGenTextures(1, &id);
    glBindTexture(GL_TEXTURE_2D, id);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, rgba);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, wrap_mode(cmS));
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, wrap_mode(cmT));
    sBound = id;
    return id;
}

void gfx_set_texenv_blend(const unsigned char color[4]) {
    sBlendMode = 1;
    sEnv[0] = color[0] / 255.0f;
    sEnv[1] = color[1] / 255.0f;
    sEnv[2] = color[2] / 255.0f;
    sEnv[3] = color[3] / 255.0f;
}

void gfx_set_texenv_modulate(void) {
    sBlendMode = 0;
}

void gfx_set_fog(int enable, const unsigned char color[4]) {
    sFogOn = enable;
    if (enable) {
        sFogCol[0] = color[0] / 255.0f;
        sFogCol[1] = color[1] / 255.0f;
        sFogCol[2] = color[2] / 255.0f;
        sFogCol[3] = color[3] / 255.0f;
    }
}

void gfx_set_texture_filter(int point) {
    GLint filter;

    if (sWindow == NULL || !sTexOn) {
        return;
    }
    filter = point ? GL_NEAREST : GL_LINEAR;
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, filter);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, filter);
}

void gfx_bind_texture(unsigned int handle) {
    if (sWindow == NULL) {
        return;
    }
    if (handle == 0) {
        sTexOn = 0;
    } else {
        sTexOn = 1;
        if (handle != sBound) {
            glBindTexture(GL_TEXTURE_2D, handle);
            sBound = handle;
        }
    }
}

void gfx_set_scissor(float x0, float y0, float x1, float y1) {
    int w, h, gx, gy;

    if (sWindow == NULL) {
        return;
    }
    gx = (int) (x0 * sScale);
    gy = (int) ((sFbHeight - y1) * sScale);
    w = (int) ((x1 - x0) * sScale);
    h = (int) ((y1 - y0) * sScale);
    if (w < 0 || h < 0) {
        w = 0;
        h = 0;
    }
    glEnable(GL_SCISSOR_TEST);
    glScissor(gx, gy, w, h);
}

void gfx_disable_scissor(void) {
    if (sWindow == NULL) {
        return;
    }
    glDisable(GL_SCISSOR_TEST);
}

void gfx_frame_begin(void) {
    if (sWindow == NULL) {
        return;
    }
    glDepthMask(GL_TRUE);
    glDisable(GL_SCISSOR_TEST);
    glClearColor(0.0f, 0.0f, 0.0f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
}

#define MAX_BATCH 8192
static GfxTriVert sBatch[MAX_BATCH];

void gfx_draw_tris(const GfxTriVert *verts, int count) {
    int i;

    if (sWindow == NULL || count <= 0) {
        return;
    }
    if (count > MAX_BATCH) {
        count = MAX_BATCH;
    }
    for (i = 0; i < count; i++) {
        float w = verts[i].w;
        sBatch[i] = verts[i];
        sBatch[i].x *= w;
        sBatch[i].y *= w;
        sBatch[i].z *= w;
    }
    glUniform1i(uUseTex, sTexOn);
    glUniform1i(uBlend, sBlendMode);
    glUniform4fv(uEnvColor, 1, sEnv);
    glUniform1i(uFogOn, sFogOn);
    glUniform4fv(uFogColor, 1, sFogCol);
    glUniform1f(uAlphaRef, sAlphaRef);
    glBufferData(GL_ARRAY_BUFFER, count * sizeof(GfxTriVert), sBatch, GL_STREAM_DRAW);
    glDrawArrays(GL_TRIANGLES, 0, count);
}

void gfx_delete_texture(unsigned int handle) {
    GLuint id = handle;

    if (sWindow == NULL || handle == 0) {
        return;
    }
    if (handle == sBound) {
        sBound = 0;
    }
    glDeleteTextures(1, &id);
}

void gfx_set_depth_test(int enable) {
    if (sWindow == NULL) {
        return;
    }
    if (enable) {
        glEnable(GL_DEPTH_TEST);
    } else {
        glDisable(GL_DEPTH_TEST);
    }
}

void gfx_set_depth_write(int enable) {
    if (sWindow == NULL) {
        return;
    }
    glDepthMask(enable ? GL_TRUE : GL_FALSE);
}

void gfx_set_depth_offset(int enable) {
    if (sWindow == NULL) {
        return;
    }
    if (enable) {
        glEnable(GL_POLYGON_OFFSET_FILL);
    } else {
        glDisable(GL_POLYGON_OFFSET_FILL);
    }
}

void gfx_set_alpha_test(float ref) {
    sAlphaRef = ref;
}

void gfx_frame_end(void) {
    SDL_Event event;

    if (sWindow == NULL) {
        return;
    }
    // The browser presents when we yield (pc_retrace_wait sleeps); just drain
    // SDL events so the keyboard state stays current.
    while (SDL_PollEvent(&event)) {
    }
}
