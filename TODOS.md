# TODOS

## Follow-up: screen/UIA “what did they say?”

- **What:** After a short alert ping, let the user ask Hermes what the message said; Hermes reads the visible chat UI via UIA/OCR (never auto-include body in the ping).
- **Why:** Approved design trajectory (office-hours A+C): butler ping now, conversational follow-up later.
- **Pros:** Feels like real Jarvis; keeps privacy default (no body in auto alerts).
- **Cons:** Fragile per-app UI; privacy-sensitive; large scope vs alerts MCP.
- **Context:** Premises in `~/.gstack/projects/jarvis-pc/skps9-main-design-20260809-094222.md`. Auto path must stay phrase-only. Platform API/bot pull is a separate later track (Hermes gateway).
- **Depends on / blocked by:** Alerts HTTP MCP + Hermes TTS path shipping and stable.
- **Status:** deferred

## Follow-up: remote Hermes → Windows alerts MCP

- **What:** Document and support reaching the Windows localhost HTTP alerts MCP from a Hermes instance on another machine via VPN or SSH tunnel (never raw public port-forward).
- **Why:** User may run Hermes 24/7 on a second PC; watcher/eyes must stay on the Discord/WhatsApp desktop.
- **Pros:** Matches long-term topology; keeps bind on 127.0.0.1.
- **Cons:** Ops complexity; auth token + tunnel must be maintained.
- **Context:** Eng review locked HTTP MCP on loopback + token. Design premise 6.
- **Depends on / blocked by:** Local alerts HTTP MCP working with Windows native Hermes.
- **Status:** deferred
