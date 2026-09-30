# Information Processing System

木乔的信息工作台，以 [AIHOT](https://github.com/KKKKhazix/AIHOT) 开源框架为网站核心，接入自己的订阅与采集器。公网入口：[intel.muqiao.xyz](https://intel.muqiao.xyz/)。

## Website core

原生 RSS / 自定义采集 → 内容身份判重 → 预筛与两次独立评分 → 中文摘要及事实抽取 → 事件归组与热度 → 网页、RSS、API、MCP。自己的89个 AK RSS与当前乔木订阅已加入；X自动搜索继续暂停。模型调用受预算限制，存量迁移保留原日期并标明未重新评分。

- [运行、部署与回退](deploy/aihot/README.md)
- [项目上下文](PROJECT.md)
- [当前替换计划与验收](plans/aihot-core-migration/task_plan.md)
- [上游源码与版本](vendor/aihot/UPSTREAM.md)、[信息处理架构](vendor/aihot/docs/architecture.md)

AIHOT源码和MIT许可保留在 `vendor/aihot`；行业配置与采集适配是本项目定制。阅读工具仍按需准备技能任务。下面的 knowledge_pack、NotebookLM 与旧 Python工作台保留为既有加工能力。

This repository is the standalone code home for the pipeline that turns
heterogeneous information sources into a canonical `knowledge_pack`, then
drives NotebookLM report generation and artifact lifecycle steps.

The upstream acquisition path is now documented as an explicit local layer:

`source contract -> acquisition recipe -> tool adapters -> run ledger -> structured extraction -> knowledge_pack`

## Scope

- Source-oriented contracts and reference docs:
  `docs/信息源处理系统/`
- Project-owned skill sources and the skill registry:
  `skills/`
- Canonical knowledge-pack builder and preprocessing:
  `tools/knowledge_pipeline/`
- Cron task contracts and helper scripts used by the pipeline:
  `cron_tasks/`

## Reading Workbench

The current website uses the [AIHOT deployment](deploy/aihot/README.md).
The retained Python reader, local media bridge and former snapshot release are documented in
[`web/README.md`](web/README.md).

## Current Pipeline

1. Source collection
   - `daily-news-summary-7am`
   - `daily-github-trending-ai-watch`
   - `ai-builders-digest-5briefs`
   - `daily-builderpulse-opportunity-radar`
   - `daily-arxiv-llm-memory-discovery`
2. Acquisition orchestration
   - selects an acquisition recipe per source item or content type
   - runs local-first tool adapters
   - records attempts and outcomes in a run ledger
   - promotes stable structured results into `knowledge_pack`
3. Normalization
   - `daily-knowledge-pack-builder`
   - canonical `knowledge_pack`
   - phase-2 preprocessing for X / raw GitHub / arXiv inputs
4. Knowledge digestion
   - `daily-notebooklm-content-gen`
5. Artifact lifecycle
   - `daily-notebooklm-artifact-trigger`
   - `daily-notebooklm-artifact-harvest`

## External Upstreams

This repository is the control plane for the information pipeline, not a mirror
of every upstream content source.

- `daily-news-summary-7am`
  Mixed upstream pages, including GitHub releases for `anthropics/claude-code`
  and `openai/codex`, plus public article pages.
- `daily-github-trending-ai-watch`
  Scrapes the live GitHub Trending daily page.
- `ai-builders-digest-5briefs`
  Uses the repo-local mirror under
  `skills/follow-builders/data/public-feed-mirror/`, refreshed from the public
  upstream `zarazhangrui/follow-builders` via
  `skills/follow-builders/scripts/sync_public_feed_mirror.py`.
- `daily-builderpulse-opportunity-radar`
  Parses the external repository checkout at `vendor/BuilderPulse`, whose
  upstream is `BuilderPulse/BuilderPulse`.
- `daily-arxiv-llm-memory-discovery`
  Queries the arXiv API directly.

## Acquisition Layer Rules

- Active sources remain source collectors with stable outputs. The acquisition
  orchestrator is a local layer, not a new content source.
- Skill cleanup follows source-of-truth rules:
  - repo-local true source: `information-processing-system/skills/`
  - shared-global true source: `muqiao-private-sync-bundle/skills-selected/`
  - runtime-only views: `/root/.controlmesh/workspace/skills`, `/root/.agents/skills`,
    `/root/.codex/skills`
- For this repository, information-processing-dedicated skills may be promoted
  to repo-local even if they were previously distributed through the shared
  bundle, because they are not part of the general coding toolbox.
- Firecrawl and `firecrawl/web-agent` are optional adapter references only, not
  required default dependencies.
- Default public webpage and X handling uses no-extra-key paths first.
- NotebookLM-specific behavior remains downstream of `knowledge_pack`.

## Notes

- This repo intentionally excludes runtime outputs from `output_to_user/`.
- Browser/runtime-specific login state is not stored here.
- This repo is the source-of-truth for information-processing cron task content.
  Native ControlMesh runtime folders under `~/.controlmesh/workspace/cron_tasks/`
  should be populated from here after jobs are created with the official
  ControlMesh cron tools.
- Installer for the currently aligned native task set:
  `python3 repos/information-processing-system/tools/install_controlmesh_cron_tasks.py`
- Runtime execution still expects sibling workspace resources such as
  `output_to_user/`, `vendor/BuilderPulse/`, `vendor/newsnow/`, and a
  `notebooklm` CLI available on `PATH`.
- The Obsidian/ops-facing reference set is also synced from this repo shape into
  `ops-vault`.
- Current skill ownership and classification are tracked in
  `skills/skills.registry.json`.
