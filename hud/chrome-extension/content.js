// JARVIS Media Bridge — content script (runs on YouTube pages)
// Polls the local bridge (127.0.0.1:8771), controls the video, and reports
// state back. Lives as long as the YouTube tab is open (no SW dependency).
const BRIDGE = 'http://127.0.0.1:8771';

function getVideo() {
  return document.querySelector('video');
}

function getTitle() {
  let t = (document.title || '').replace(/\s*-\s*YouTube\s*$/i, '').trim();
  if (!t || t.length > 60) {
    const h = document.querySelector('ytd-video-primary-info-renderer h1 yt-formatted-string');
    if (h) t = h.textContent.trim();
  }
  return t || '';
}

function controlVideo(cmd) {
  const v = getVideo();
  if (!v) return;
  if (cmd === 'playpause') {
    if (v.paused) v.play().catch(() => {}); else v.pause();
  } else if (cmd === 'prev') {
    v.currentTime = Math.max(0, v.currentTime - 10);
  } else if (cmd === 'next') {
    v.currentTime += 10;
  }
}

async function tick() {
  try {
    // 1) pull pending command
    const res = await fetch(`${BRIDGE}/next-cmd`, { cache: 'no-store' });
    if (res.ok) {
      const data = await res.json().catch(() => null);
      if (data && data.cmd) controlVideo(data.cmd);
    }
    // 2) report playback state
    const v = getVideo();
    if (v) {
      fetch(`${BRIDGE}/state`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ paused: v.paused, title: getTitle() }),
      }).catch(() => {});
    }
  } catch (e) { /* bridge not up yet */ }
}

setInterval(tick, 400);
