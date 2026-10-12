# Fallback Matrix

Keep the source of truth stable. Change the access path, not its authority.

| Preferred tool | When unavailable | Boundary |
| --- | --- | --- |
| `gh` | Official API or raw README | No generic Jina fallback |
| `mcporter` | Skip unconfigured MCP; direct source retrieval | Configuration is not proof of callable access |
| `yt-dlp` | Official subtitles or direct public page | Do not invent transcript or timestamps |
| `feedparser` | Check the direct feed URL | Do not treat search snippets as feed entries |
| Official/direct web retrieval | Existing approved Firecrawl source | Preserve failure; do not expand budgets/allowlist |
| Budgeted `Jina Reader` | Preserve existing X summary and reading gap | 50 attempts/24h, 1/min, 10/h; respect risk cooldown |
| PDF/image extraction | Retain attachment, selected pages and extraction gap | No Jina fallback; no raw binary as body |

Do not use legacy preprocessing to bypass Jina budgets or restart paused X/Google searches.
