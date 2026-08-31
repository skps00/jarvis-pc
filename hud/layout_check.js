// Layout overlap checker — measures all content rects, flags overlaps
const { app, BrowserWindow } = require('electron');
const path = require('path');
const fs = require('fs');

app.whenReady().then(() => {
  const w = new BrowserWindow({ show: false, width: 2560, height: 1440, webPreferences: { offscreen: true } });
  w.loadFile(path.join(__dirname, 'renderer/index.html'));
  w.webContents.on('did-finish-load', () => {
    setTimeout(() => {
      w.webContents.executeJavaScript(`(() => {
        const els = [...document.querySelectorAll('.panel.left, .panel.right, .stats, .levels, .weather, .clockblock, #greeting')];
        const rects = els.map(el => {
          const r = el.getBoundingClientRect();
          const c = (el.className || el.id || '').toString().slice(0, 18);
          return { c, x: r.x, y: r.y, w: r.width, h: r.height };
        });
        const ov = [];
        for (let i = 0; i < rects.length; i++) for (let j = i + 1; j < rects.length; j++) {
          const a = rects[i], b = rects[j];
          if (a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y) ov.push(a.c + ' × ' + b.c);
        }
        return JSON.stringify({ rects, overlaps: ov });
      })()`).then(s => {
        fs.writeFileSync(path.join(__dirname, 'layout_check.json'), s);
        console.log(s);
        app.quit();
      });
    }, 2800);
  });
});
