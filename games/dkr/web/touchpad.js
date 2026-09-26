// Touch controls for phones and tablets: a floating analog stick on the left,
// A / B / Z / R (+ L, Start) on the right, sliding between buttons allowed.
// Portrait: the game sits at the top and the controls fill the space below.
// Landscape: the game fills the height and the controls flank it.
// Feeds the game through Module._web_touch_input(buttons, stickX, stickY).
(function () {
  var Q = new URLSearchParams(location.search);
  var touchy = Q.has('touch') || matchMedia('(pointer: coarse)').matches || ('ontouchstart' in window);
  if (!touchy || Q.has('notouch')) return;

  var BTN = { A: 0x8000, B: 0x4000, Z: 0x2000, START: 0x1000, L: 0x0020, R: 0x0010 };
  var STICK_MAX = 80;

  // ---- runtime hookup (never call into wasm before it is initialised) ----
  var ready = false;
  var prev = Module.onRuntimeInitialized;
  Module.onRuntimeInitialized = function () { if (prev) prev(); ready = true; send(); };

  var css = document.createElement('style');
  css.textContent = [
    'html,body{overscroll-behavior:none;touch-action:none;-webkit-user-select:none;user-select:none;-webkit-touch-callout:none}',
    '#tc{position:fixed;inset:0;pointer-events:none;z-index:5;font:600 15px/1 system-ui,-apple-system,sans-serif}',
    '#tc .zone{position:absolute;pointer-events:auto;touch-action:none}',
    '#tc .btn{position:absolute;border-radius:50%;display:flex;align-items:center;justify-content:center;',
    '  flex-direction:column;color:#fff;background:rgba(20,22,30,.42);border:2px solid var(--c);box-shadow:0 0 0 1px rgba(0,0,0,.35) inset;',
    '  transform:translate(-50%,-50%);transition:background .05s,transform .05s;text-shadow:0 1px 2px #000}',
    '#tc .btn.on{background:var(--c);transform:translate(-50%,-50%) scale(.92)}',
    '#tc .pill{border-radius:999px}',
    '#tc .btn small{font-size:10px;opacity:.8;display:block;margin-top:2px;font-weight:500}',
    '#tc .base{position:absolute;border-radius:50%;border:2px solid rgba(255,255,255,.35);background:rgba(20,22,30,.30);',
    '  transform:translate(-50%,-50%);pointer-events:none}',
    '#tc .knob{position:absolute;border-radius:50%;background:rgba(255,255,255,.55);border:2px solid rgba(255,255,255,.8);',
    '  transform:translate(-50%,-50%);pointer-events:none}',
    '#tc .hint{position:absolute;color:rgba(255,255,255,.45);font-size:12px;font-weight:500;pointer-events:none;transform:translate(-50%,-50%)}',
    '#tc .tog{position:absolute;pointer-events:auto;touch-action:none;padding:7px 11px;border-radius:999px;font-size:12px;',
    '  color:#fff;background:rgba(20,22,30,.55);border:1px solid rgba(255,255,255,.35)}',
    '#tc .tog.on{background:#2e9e4f;border-color:#7be39a}',
    // portrait: game on top, controls below
    '@media (orientation:portrait){#wrap{align-items:flex-start!important;padding-top:env(safe-area-inset-top)}',
    '  canvas{width:100vw!important;height:75vw!important}}',
    '#status{display:none}'
  ].join('\n');
  document.head.appendChild(css);

  var root = document.createElement('div');
  root.id = 'tc';
  root.style.display = 'none';                 // shown once the game has started
  document.body.appendChild(root);
  var shown = setInterval(function () {
    if (!document.getElementById('start')) { root.style.display = ''; clearInterval(shown); layout(); }
  }, 100);

  function el(cls, parent, text) {
    var e = document.createElement('div');
    e.className = cls;
    if (text) e.innerHTML = text;
    (parent || root).appendChild(e);
    return e;
  }

  // ---- stick (floating: it centres where the thumb lands) ----
  var stickZone = el('zone');
  var base = el('base'), knob = el('knob'), hint = el('hint', root, 'drag to steer');
  var stick = { id: null, ox: 0, oy: 0, x: 0, y: 0, r: 60 };

  // ---- buttons ----
  var defs = [
    { k: 'A', label: 'A<small>gas</small>', c: '#2fb35a', bit: BTN.A },
    { k: 'B', label: 'B<small>brake</small>', c: '#d9433b', bit: BTN.B },
    { k: 'Z', label: 'Z<small>item</small>', c: '#8a5ad6', bit: BTN.Z },
    { k: 'R', label: 'R<small>hop</small>', c: '#2f7de0', bit: BTN.R },
    { k: 'L', label: 'L', c: '#8a8f99', bit: BTN.L, pill: true },
    { k: 'S', label: 'START', c: '#e0a72f', bit: BTN.START, pill: true }
  ];
  var btnZone = el('zone');
  var btns = {};
  defs.forEach(function (d) {
    var b = el('btn' + (d.pill ? ' pill' : ''), root, d.label);
    b.style.setProperty('--c', d.c);
    btns[d.k] = { el: b, bit: d.bit, x: 0, y: 0, r: 30 };
  });

  // ---- toggles ----
  var autoGas = false;
  try { autoGas = localStorage.getItem('dkr_autogas') === '1'; } catch (e) {}
  var gasTog = el('tog' + (autoGas ? ' on' : ''), root, 'Auto-gas');
  var fsTog = el('tog', root, 'Fullscreen');
  var canFs = !!(document.documentElement.requestFullscreen || document.documentElement.webkitRequestFullscreen);
  if (!canFs) fsTog.style.display = 'none';

  function tap(elm, fn) {
    elm.addEventListener('pointerdown', function (e) { e.preventDefault(); e.stopPropagation(); fn(); });
  }
  tap(gasTog, function () {
    autoGas = !autoGas;
    gasTog.classList.toggle('on', autoGas);
    try { localStorage.setItem('dkr_autogas', autoGas ? '1' : '0'); } catch (e) {}
    send();
  });
  tap(fsTog, function () {
    var d = document.documentElement;
    if (document.fullscreenElement || document.webkitFullscreenElement) {
      (document.exitFullscreen || document.webkitExitFullscreen).call(document);
    } else {
      var p = (d.requestFullscreen || d.webkitRequestFullscreen).call(d);
      if (p && p.then) p.then(function () {
        try { screen.orientation.lock('landscape').catch(function () {}); } catch (e) {}
      }).catch(function () {});
    }
  });

  // ---- layout ----
  function place(e, x, y, w, h) {
    e.style.left = x + 'px'; e.style.top = y + 'px';
    if (w != null) { e.style.width = w + 'px'; e.style.height = (h == null ? w : h) + 'px'; }
  }
  function box(e, x, y, w, h) { e.style.left = x + 'px'; e.style.top = y + 'px'; e.style.width = w + 'px'; e.style.height = h + 'px'; }

  function layout() {
    var W = innerWidth, H = innerHeight, portrait = H > W;
    var s, top, bottom = H - 12;
    if (portrait) {
      top = Math.min(H * 0.62, W * 0.75 + 8);        // just below the game
      s = Math.min(W / 5.2, (H - top) / 3.4, 96);   // button diameter
      box(stickZone, 0, top, W * 0.5, H - top);
      box(btnZone, W * 0.42, top, W * 0.58, H - top);
      var cy = top + (H - top) * 0.58, cx = W * 0.25;
      stick.r = Math.min(W * 0.17, (H - top) * 0.3);
      stick.homeX = cx; stick.homeY = cy;
      var ax = W - s * 0.85, ay = cy + s * 0.35;
      set('A', ax, ay, s * 1.15);
      set('B', ax - s * 1.2, ay + s * 0.45, s * 0.9);
      set('R', ax - s * 0.25, ay - s * 1.15, s * 0.9);
      set('Z', ax - s * 1.35, ay - s * 0.7, s * 0.85);
      set('L', W * 0.5 - s * 0.95, top + s * 0.45, s * 1.1, s * 0.5);
      set('S', W * 0.5 + s * 0.95, top + s * 0.45, s * 1.3, s * 0.5);
      place(gasTog, 10, H - 44); place(fsTog, W - 104, H - 44);
    } else {
      s = Math.min(H / 4.2, W / 9, 104);
      box(stickZone, 0, 0, W * 0.4, H);
      box(btnZone, W * 0.6, 0, W * 0.4, H);
      stick.r = Math.min(H * 0.17, 80);
      stick.homeX = s * 1.25 + 10; stick.homeY = H - s * 1.35;
      var bx = W - s * 0.85, by = H - s * 0.95;
      set('A', bx, by, s * 1.15);
      set('B', bx - s * 1.2, by + s * 0.35, s * 0.9);
      set('R', bx - s * 0.2, by - s * 1.2, s * 0.9);
      set('Z', bx - s * 1.35, by - s * 0.8, s * 0.85);
      set('L', s * 0.9 + 10, s * 0.45 + 8, s * 1.1, s * 0.5);
      set('S', W / 2, H - s * 0.32, s * 1.3, s * 0.5);
      place(gasTog, 10, s * 0.75 + 16); place(fsTog, W - 104, 10);
    }
    if (stick.id == null) { stick.ox = stick.homeX; stick.oy = stick.homeY; stick.x = 0; stick.y = 0; }
    drawStick();
    place(hint, stick.homeX, stick.homeY + stick.r + 18);
  }
  function set(k, x, y, w, h) {
    var b = btns[k];
    b.x = x; b.y = y; b.w = w; b.h = h == null ? w : h; b.r = Math.max(b.w, b.h) / 2;
    place(b.el, x, y, w, h);
  }
  function drawStick() {
    place(base, stick.ox, stick.oy, stick.r * 2);
    place(knob, stick.ox + stick.x * stick.r, stick.oy - stick.y * stick.r, stick.r * 0.8);
  }

  // ---- input state ----
  var held = {};               // pointerId -> button key
  function send() {
    var mask = 0, k;
    for (var id in held) if (held[id]) mask |= btns[held[id]].bit;
    if (autoGas && !(mask & BTN.B)) mask |= BTN.A;
    for (k in btns) btns[k].el.classList.toggle('on', !!(mask & btns[k].bit) && (k !== 'A' || !autoGas || Object.values(held).indexOf('A') >= 0));
    var sx = 0, sy = 0;
    var m = Math.hypot(stick.x, stick.y);
    if (m > 0.12) {
      var k2 = Math.min(1, (m - 0.12) / 0.88) / m;
      sx = Math.round(stick.x * k2 * STICK_MAX);
      sy = Math.round(stick.y * k2 * STICK_MAX);
    }
    if (ready && Module._web_touch_input) Module._web_touch_input(mask, sx, sy);
    window.__dkrTouch = [mask, sx, sy, ready];
    if (sx || sy) window.__dkrStick = [sx, sy];
  }

  // nearest button within reach of the finger (generous: 1.25x its radius)
  function hit(x, y) {
    var best = null, bd = 1e9;
    for (var k in btns) {
      var b = btns[k];
      var dx = (x - b.x) / (b.w / 2), dy = (y - b.y) / (b.h / 2);
      var d = Math.hypot(dx, dy);
      if (d < 1.25 && d < bd) { bd = d; best = k; }
    }
    return best;
  }
  function buzz() { try { navigator.vibrate && navigator.vibrate(8); } catch (e) {} }

  btnZone.addEventListener('pointerdown', function (e) {
    e.preventDefault();
    btnZone.setPointerCapture(e.pointerId);
    var k = hit(e.clientX, e.clientY);
    held[e.pointerId] = k;
    if (k) buzz();
    send();
  });
  btnZone.addEventListener('pointermove', function (e) {
    if (!(e.pointerId in held)) return;
    var k = hit(e.clientX, e.clientY);          // slide from A to R and back
    if (k !== held[e.pointerId]) { held[e.pointerId] = k; if (k) buzz(); send(); }
  });
  function release(e) { if (e.pointerId in held) { delete held[e.pointerId]; send(); } }
  btnZone.addEventListener('pointerup', release);
  btnZone.addEventListener('pointercancel', release);

  // small buttons outside the button zone (L, START in portrait/landscape corners)
  ['L', 'S'].forEach(function (k) {
    var b = btns[k].el;
    b.style.pointerEvents = 'auto';
    b.style.touchAction = 'none';
    b.addEventListener('pointerdown', function (e) {
      e.preventDefault(); e.stopPropagation();
      b.setPointerCapture(e.pointerId); held[e.pointerId] = k; buzz(); send();
    });
    b.addEventListener('pointerup', release);
    b.addEventListener('pointercancel', release);
  });

  stickZone.addEventListener('pointerdown', function (e) {
    if (stick.id != null) return;
    e.preventDefault();
    stickZone.setPointerCapture(e.pointerId);
    stick.id = e.pointerId;
    stick.ox = e.clientX; stick.oy = e.clientY; stick.x = 0; stick.y = 0;
    hint.style.display = 'none';
    drawStick(); send();
  });
  stickZone.addEventListener('pointermove', function (e) {
    if (e.pointerId !== stick.id) return;
    var dx = (e.clientX - stick.ox) / stick.r, dy = (stick.oy - e.clientY) / stick.r;
    var m = Math.hypot(dx, dy);
    if (m > 1) {
      // let the base follow the thumb so steering never gets stuck at the edge
      stick.ox += (dx / m) * (m - 1) * stick.r;
      stick.oy -= (dy / m) * (m - 1) * stick.r;
      dx /= m; dy /= m;
    }
    stick.x = dx; stick.y = dy;
    drawStick(); send();
  });
  function stickUp(e) {
    if (e.pointerId !== stick.id) return;
    stick.id = null; stick.ox = stick.homeX; stick.oy = stick.homeY; stick.x = 0; stick.y = 0;
    drawStick(); send();
  }
  stickZone.addEventListener('pointerup', stickUp);
  stickZone.addEventListener('pointercancel', stickUp);

  // no page scrolling, pinch zoom or long-press menus while playing
  ['touchstart', 'touchmove', 'gesturestart', 'contextmenu'].forEach(function (t) {
    document.addEventListener(t, function (e) { if (e.target.closest && e.target.closest('#tc')) e.preventDefault(); }, { passive: false });
  });
  // drop everything if the page loses focus mid-press
  window.addEventListener('blur', function () { held = {}; stick.id = null; stick.x = stick.y = 0; send(); });

  // a connected gamepad hides the overlay; touching the screen brings it back
  var padHidden = false;
  addEventListener('gamepadconnected', function () { padHidden = true; root.style.visibility = 'hidden'; });
  document.addEventListener('pointerdown', function (e) {
    if (padHidden && e.pointerType === 'touch') { padHidden = false; root.style.visibility = ''; }
  }, true);

  addEventListener('resize', layout);
  addEventListener('orientationchange', function () { setTimeout(layout, 200); });
  layout();

  // the start screen: say "tap"
  var st = document.querySelector('#start .go');
  if (st) st.textContent = 'Tap to play';
})();
