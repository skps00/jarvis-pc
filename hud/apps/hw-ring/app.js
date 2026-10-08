/**
 * hw-ring — sample HUD app (HoloMat H1).
 * Loaded via main executeJavaScript; entry = register(Jarvis).
 */
function register(Jarvis) {
  var els = {};
  Jarvis.register({
    id: 'hw-ring',
    mount: function (el) {
      el.innerHTML =
        '<div class="p-title" style="font-size:11px;letter-spacing:2px;color:#00aaf8;margin-bottom:6px">' +
        '◎ LOAD</div>' +
        '<div style="display:flex;gap:10px;align-items:center">' +
        '<div data-ring style="width:72px;height:72px;border-radius:50%;border:2px solid rgba(0,170,248,0.45);' +
        'display:flex;align-items:center;justify-content:center;font:700 14px Orbitron,sans-serif;' +
        'color:#eaf6ff;text-shadow:0 0 10px rgba(0,170,248,0.55)">--</div>' +
        '<div style="font:12px Rajdhani,Consolas,monospace;line-height:1.45;opacity:0.9">' +
        '<div>CPU <span data-cpu>--</span></div>' +
        '<div>GPU <span data-gpu>--</span></div>' +
        '<div>RAM <span data-ram>--</span></div>' +
        '<div>NET <span data-net>--</span></div>' +
        '</div></div>';
      els.ring = el.querySelector('[data-ring]');
      els.cpu = el.querySelector('[data-cpu]');
      els.gpu = el.querySelector('[data-gpu]');
      els.ram = el.querySelector('[data-ram]');
      els.net = el.querySelector('[data-net]');
    },
    unmount: function () {
      els = {};
    },
    tick: function () {
      return Jarvis.sensors().then(function (hw) {
        if (!hw || !els.ring) return;
        var cpu = hw.cpu != null ? Math.round(hw.cpu) : null;
        var gpu = hw.gpu && hw.gpu.util_pct != null ? Math.round(hw.gpu.util_pct) : null;
        var ram = hw.ram != null ? Math.round(hw.ram) : null;
        var load = cpu != null ? cpu : (gpu != null ? gpu : 0);
        els.ring.textContent = load + '%';
        els.ring.style.borderColor = load >= 85
          ? 'rgba(255,77,94,0.8)'
          : load >= 60
            ? 'rgba(255,179,0,0.7)'
            : 'rgba(0,170,248,0.55)';
        if (els.cpu) els.cpu.textContent = cpu != null ? cpu + '%' : '--';
        if (els.gpu) els.gpu.textContent = gpu != null ? gpu + '%' : '--';
        if (els.ram) els.ram.textContent = ram != null ? ram + '%' : '--';
        if (els.net && hw.net) {
          els.net.textContent = (hw.net.down_kbps || 0) + '↓ ' + (hw.net.up_kbps || 0) + '↑';
        }
      }).catch(function (e) {
        Jarvis.log('hw-ring tick: ' + (e && e.message ? e.message : e));
      });
    },
  });
}
