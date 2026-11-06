# Progress

## Current

Google subscriptions, RSS ingestion, 436 processing acceptance and Git delivery are complete. Three real outputs are public. Temporary transfer copies have been removed.

## Done

- Confirmed target account and existing counts: Scholar 1, Google Alerts 3.
- Read repository and upstream instructions, deployment documentation and SpecMesh convention.
- Created and read back all 22 Scholar queries, retaining all-results delivery. The narrow original was replaced without leaving a duplicate.
- Created all 18 engineering Alerts. Existing three broad alerts remain, total 21. Each new alert uses daily frequency and all results; the first two hardware searches accept any language, the other sixteen use English. Global daily single-email digest was saved and reopened to confirm.
- Browser screenshots are local artifacts under `/tmp/google-radar-20261107/`; no CAPTCHA or unusual-traffic page was encountered. One transient browser read timed out and was reconciled against the saved list before continuing. No duplicate submission was made.
- External AGY attempt timed out after 180 seconds. One targeted check found no matching remaining process and no RSS edits; handed the unchanged RSS scope to an internal worker.
- Reviewed the internal worker's generator, six source seeds, focused tests and upstream patch note. Four focused unit tests pass. An attempted unrelated test-module name did not exist; it was removed from the verification command, without changing production code.
- 436 native RSS probe returned HTTP 200 and 22 Rockchip items. Origin health is HTTP 200; ordinary public API probes receive Cloudflare error 1010.
- Merged only the six new sources into host/API/worker seed files, preserving all 138 existing seeds. Existing `createSource` created each source once with duplicate checks and audit. Collection stays enabled, resident model calls stay disabled. Rollback seed copies: `/opt/intelligence-hub/aihot/google-radar-20261107/`.
- Native worker collected all six sources successfully: 22 Rockchip articles and 30 from each of the other five, total 172. All source health states are `ok`; next collection is scheduled by the existing worker in two hours.
- One historical local OpenCode trial failed with exit 1 after one attempted call; no automatic replay or alternate provider was used. Local CLI reported zero stored credentials. The user then corrected the execution location to 436; do not ask for desktop authentication.
- Daily Chrome can access the public site normally. A guessed `/api/site/sources` route was 404, not a production availability failure; public QA uses the actual source-filtered list.
- Confirmed server `agent436` already holds the intended MiniMax Token Plan authentication and its model catalog includes 3.1 Flash. No new account login is required.
- Desktop workflow timer was enabled but its service had failed and had no running process. Disabled the desktop timer after the user selected server processing; no in-flight work was stopped.
- Server task user lacks Docker access. The server workflow patch keeps container orchestration in a root-owned service while demoting only model CLI execution to `agent436`; no Docker group grant or credential copy.
- Reviewed and installed server-local Docker transport and demoted OpenCode execution. Combined focused RSS/CLI suite passes 16 tests. Root-owned runner is `/opt/intelligence-hub-workflow`; `/opt/intelligence-hub` has a task-user-owned ancestor and was deliberately left unchanged. Global systemd units pass verification; a pre-existing unrelated service warning was not changed.
- Server-only explicit RSS sample `viuwumdzvf3jo1kjkwk72iedo` completed analysis 767 and event grouping, with nine actual OpenCode calls. It is public in the coding-agent RSS source filter, with original source time retained; both origin API and daily Chrome show the new article. Its Google RSS text remains a short summary and body is `unconfirmed`, not verified fulltext.
- Enabled the 436 system `intelligence-hub-workflow.timer`. Its first service run completed with exit 0, status `completed`, 14 real model calls, two native articles completed/public, zero upstream candidates and zero held. Readback confirms model `minimax-cn-coding-plan/MiniMax-M3.1-Flash` and actual OpenCode process owner `agent436`; desktop timer remains stopped. Existing 8/min, 60/hour and 300/24h budget is unchanged.
- Combined acceptance is one explicit new RSS article plus two ordinary workflow articles. First-import RSS history is not bulk rescored; fresh arrivals enter the existing native selection workflow. The explicit failed desktop receipt and older unknown receipts were retained, not replayed.
- Code commit `ae84084` was pushed to `origin/codex/google-radar-server-workflow-20261107` in `qiaoqiao2521/information-processing-system`. The installed runner version records this commit. No merge, force push or visibility change was performed.
- Final runtime readback confirms the 436 timer is enabled/active, the last service result is `success`, and the desktop timer is disabled/inactive. Resident API/worker model calls remain disabled; the server workflow enables processing only for its controlled CLI session.
- Removed both temporary `server-workflow.tgz` transfer copies, locally and under `/root/google-radar-20261107/`. Both paths are absent on readback. Their original sizes were not retained, so reclaimed bytes are not quantified. Rollback seed copies, the server workflow backup location, installed scripts and local browser acceptance screenshots are retained; no source material was removed.

## Remaining

- None for this task. RSS summaries with unconfirmed fulltext and first-import backfill retain their existing behavior; this acceptance does not claim that all 172 imported articles were model-processed.

## Knowledge

no_reusable_delta: source subscriptions and the selected execution host are project-specific state, recorded here and in PROJECT/deployment documentation. No shared knowledge or global memory was changed.
