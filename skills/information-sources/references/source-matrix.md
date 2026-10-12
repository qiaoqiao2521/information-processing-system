# Source Matrix

PROJECT.md owns the source allowlist, paused searches and shared budgets.

| Task | Preferred tool | Fallback / evidence boundary |
| --- | --- | --- |
| GitHub metadata / README | `gh` | Official API or direct raw content |
| Video metadata / subtitles | Installed `yt-dlp` | Official subtitles; preserve unavailable language and timestamps |
| RSS / Atom | `feedparser` | Direct feed URL check; preserve original URLs and dates |
| Configured MCP source | `mcporter` | Direct official source; skip unconfigured MCP |
| Public web page | Official/direct retrieval | Approved Firecrawl only, within existing budget |
| Existing X post body | Budgeted `Jina Reader` | Preserve summary on failure; no new X/Google search |
| PDF | Original download + document extractor | Record selected pages, incomplete extraction and body hash |
| Image | Original image + available OCR | Preserve image identity and OCR uncertainty |

A readable summary is not full text. Jina is not a generic fallback in this project.
See [evidence-report-contract.md](evidence-report-contract.md) before writing from source packets.
