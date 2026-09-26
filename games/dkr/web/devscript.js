// Dev hook for headless tests: ?script=m19,ArrowDown:0.3,w1,KeyX:0.2 ...
//   mN      wait until the game's menu id is N (Module._dev_menu_id; ids in src/menu.h)
//   wS      wait S seconds
//   Code:d  press a key code for d seconds
//   uN:Code press Code every 1.2 s until the menu id is N
(function () {
  var q = new URLSearchParams(location.search).get('script');
  if (!q) return;
  var steps = q.split(','), i = 0;
  function key(t, code) { window.dispatchEvent(new KeyboardEvent(t, { code: code, key: code, bubbles: true })); }
  function menu() { return (typeof Module !== 'undefined' && Module._dev_menu_id) ? Module._dev_menu_id() : -1; }
  function next() {
    if (i >= steps.length) return;
    var s = steps[i];
    if (/^m\d+$/.test(s)) {
      if (menu() === +s.slice(1)) { i++; setTimeout(next, 700); } else setTimeout(next, 100);
      return;
    }
    var u = /^u(\d+):(\w+)$/.exec(s);       // uN:Code  press Code every 1.2 s until menu N
    if (u) {
      if (menu() === +u[1]) { i++; setTimeout(next, 700); return; }
      key('keydown', u[2]);
      setTimeout(function () { key('keyup', u[2]); setTimeout(next, 1000); }, 200);
      return;
    }
    i++;
    if (/^w[\d.]+$/.test(s)) { setTimeout(next, +s.slice(1) * 1000); return; }
    var p = s.split(':'), d = +(p[1] || 0.2);
    console.log('script ' + s + ' at menu ' + menu());
    key('keydown', p[0]);
    setTimeout(function () { key('keyup', p[0]); setTimeout(next, 250); }, d * 1000);
  }
  var t = setInterval(function () { if (menu() >= 0) { clearInterval(t); next(); } }, 200);
})();
