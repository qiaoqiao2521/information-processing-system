# Findings

- 2026-11-07: Daily Chrome is connected through the installed browser plugin; the selected information account is confirmed on both Google services.
- Initial Scholar inventory contained one alert for `"action chunking" OR "visuomotor policy" manipulation`.
- Google Alerts currently contains three broad queries (robotics/simulation, navigation/3D, coding agents). None is an exact match for the supplied 18 engineering queries.
- Repository is clean on `codex/horizon-sources-20261020` before this task.
- Existing AIHOT native RSS collection and `tools/aihot/subscriptions.py` are the preferred extension points. The 436 application is documented at `/opt/intelligence-hub/aihot/app`; live state requires readback.
- Source list: user attachment `5f5b9c7e-60f1-4776-8450-b7365b64e6c6/已粘贴的文本.txt`, sections 2, 3 and 4. Its parser-limit claims are not treated as verified product guarantees.
- Latest user correction selects 436 as the processing host. The desktop's missing OpenCode credentials are not a reason to ask for desktop login.
- 436 `agent436` already has MiniMax Token Plan and GLM credentials; official OpenCode 1.18.34 lists `minimax-cn-coding-plan/MiniMax-M3.1-Flash`. Root's OpenCode wrapper deliberately refuses model execution.
- `agent436` has no Docker socket access. Keep that boundary: use a root-owned workflow runner for Docker orchestration, demote each OpenCode subprocess to `agent436`, and keep its existing account in place. Do not execute root workflow code from a task-user-writable project path.
