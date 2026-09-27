#!/usr/bin/env python3
"""
信息收集系统 Web 控制台服务 (Information Processing Hub)
- 零外部依赖 (纯 Python 3 标准库)
- 聚合 output_to_user 下的所有最新多源情报 (融合简报、GitHub Trending、机会雷达、AI Builders 日报)
- 紧密对接自媒体工作站 API (http://localhost:3000/api/media/jobs)，支持一键直通投产
- 完整包含要素提取与本地原文快照支持
"""
from __future__ import annotations

import json
import mimetypes
import os
import re
import sys
import urllib.error
import urllib.request
from http import HTTPStatus
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = REPO_ROOT.parent
OUTPUT_DIR = Path(os.environ.get("HUB_OUTPUT_DIR", str(WORKSPACE_ROOT / "output_to_user")))
DATA_DIR = Path(__file__).parent / "data"
ASSETS_FILE = DATA_DIR / "media_assets.json"
ENRICHED_TRENDING_FILE = DATA_DIR / "enriched_trending.json"
ENRICHED_DIGEST_FILE = DATA_DIR / "enriched_digest.json"
PUBLIC_DIR = Path(__file__).parent / "public"

MEDIA_STUDIO_API_URL = os.environ.get("MEDIA_STUDIO_API_URL", "http://127.0.0.1:3000/api/media")
PUBLIC_READONLY = os.environ.get("HUB_PUBLIC_READONLY", "0") == "1"


def read_json_safely(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[warning] Failed to read {path}: {e}", file=sys.stderr)
        return None


def check_media_studio_status() -> dict:
    try:
        req = urllib.request.Request(f"{MEDIA_STUDIO_API_URL}/presets", method="GET")
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode())
                return {"online": True, "presetsCount": len(data.get("presets", []))}
    except Exception:
        pass
    return {"online": False, "presetsCount": 0}


class IntelligenceHubHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        url_path = self.path.split("?")[0]

        if url_path == "/api/status":
            self.handle_api_status()
        elif url_path == "/api/topics":
            self.handle_api_topics()
        elif url_path == "/api/trending":
            self.handle_api_trending()
        elif url_path == "/api/radar":
            self.handle_api_radar()
        elif url_path == "/api/digest":
            self.handle_api_digest()
        elif url_path == "/api/assets":
            self.handle_api_assets()
        else:
            self.handle_static(url_path)

    def do_POST(self):
        if PUBLIC_READONLY:
            self.send_json({"error": "Public site is read-only"}, status=HTTPStatus.FORBIDDEN)
            return
        url_path = self.path.split("?")[0]
        if url_path == "/api/studio/dispatch":
            self.handle_studio_dispatch()
        else:
            self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not found")

    def send_json(self, data: any, status: int = HTTPStatus.OK):
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def handle_api_status(self):
        studio_status = {"online": False, "presetsCount": 0} if PUBLIC_READONLY else check_media_studio_status()
        brief_data = read_json_safely(OUTPUT_DIR / "consolidated_daily_brief.json")
        trending_data = read_json_safely(ENRICHED_TRENDING_FILE) or read_json_safely(OUTPUT_DIR / "github_trending_latest.json")
        radar_data = read_json_safely(OUTPUT_DIR / "builderpulse_opportunity_radar_sources_latest.json")
        assets_data = read_json_safely(ASSETS_FILE) or []

        trending_count = len(trending_data.get("repos", [])) if trending_data else 0

        self.send_json({
            "status": "operational",
            "date": brief_data.get("date") if brief_data else None,
            "mediaStudio": studio_status,
            "publicReadOnly": PUBLIC_READONLY,
            "counts": {
                "topics": brief_data.get("total_topics", 0) if brief_data else 0,
                "trendingRepos": trending_count,
                "opportunities": radar_data.get("selected_opportunity_count", 0) if radar_data else 0,
                "curatedAssets": len(assets_data),
            },
            "compressionRatio": brief_data.get("compression_ratio", "0%") if brief_data else "0%",
        })

    def handle_api_topics(self):
        data = read_json_safely(OUTPUT_DIR / "consolidated_daily_brief.json")
        if data:
            self.send_json(data)
        else:
            self.send_json({"error": "Topics data not generated yet"}, status=HTTPStatus.NOT_FOUND)

    def handle_api_trending(self):
        # 优先读取包含要素提取和本地快照的 enriched 数据
        data = read_json_safely(ENRICHED_TRENDING_FILE) or read_json_safely(OUTPUT_DIR / "github_trending_latest.json")
        if data:
            self.send_json(data)
        else:
            self.send_json({"error": "Trending data not found"}, status=HTTPStatus.NOT_FOUND)

    def handle_api_radar(self):
        data = read_json_safely(OUTPUT_DIR / "builderpulse_opportunity_radar_sources_latest.json")
        if data:
            self.send_json(data)
        else:
            self.send_json({"error": "Opportunity radar data not found"}, status=HTTPStatus.NOT_FOUND)

    def handle_api_digest(self):
        # 优先读取包含要素提取与本地正文的 enriched 数据
        data = read_json_safely(ENRICHED_DIGEST_FILE) or read_json_safely(OUTPUT_DIR / "ai_builders_digest_sources_latest.json")
        if data:
            self.send_json(data)
        else:
            self.send_json({"error": "AI Builders Digest data not found"}, status=HTTPStatus.NOT_FOUND)

    def handle_api_assets(self):
        data = read_json_safely(ASSETS_FILE)
        self.send_json({"assets": data or []})

    def handle_studio_dispatch(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            content_length = 0
        if content_length <= 0 or content_length > 65536:
            self.send_json({"error": "Payload must be between 1 and 65536 bytes"}, status=HTTPStatus.BAD_REQUEST)
            return

        body = self.rfile.read(content_length).decode("utf-8")
        try:
            req_data = json.loads(body)
        except Exception:
            self.send_json({"error": "Invalid JSON"}, status=HTTPStatus.BAD_REQUEST)
            return

        if not isinstance(req_data, dict):
            self.send_json({"error": "Expected a JSON object"}, status=HTTPStatus.BAD_REQUEST)
            return
        prompt = req_data.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            self.send_json({"error": "Prompt is required"}, status=HTTPStatus.BAD_REQUEST)
            return
        provider = req_data.get("provider", "stub")
        kind = req_data.get("kind", "image")
        model = req_data.get("model") or (f"default-{kind}" if provider == "stub" else "")
        idempotency_key = req_data.get("idempotencyKey")
        if provider not in ("stub", "muapi") or kind not in ("image", "video") or not isinstance(model, str) or not model.strip():
            self.send_json({"error": "Provider, kind or model is invalid"}, status=HTTPStatus.BAD_REQUEST)
            return
        if not isinstance(idempotency_key, str) or not re.fullmatch(r"[A-Za-z0-9_-]{8,128}", idempotency_key):
            self.send_json({"error": "A stable idempotencyKey is required"}, status=HTTPStatus.BAD_REQUEST)
            return

        job_payload = {
            "provider": provider,
            "model": model.strip(),
            "kind": kind,
            "prompt": prompt.strip(),
            "idempotencyKey": idempotency_key,
            "input": {
                "origin": "information-processing-hub",
                "asset_id": req_data.get("asset_id"),
                "title": req_data.get("title", ""),
                "viral_title": req_data.get("viral_title", ""),
            },
        }

        try:
            forward_req = urllib.request.Request(
                f"{MEDIA_STUDIO_API_URL}/jobs",
                data=json.dumps(job_payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(forward_req, timeout=5) as forward_resp:
                res_body = json.loads(forward_resp.read().decode("utf-8"))
                self.send_json({
                    "success": True,
                    "message": "Successfully dispatched to Muqiao Media Studio",
                    "studioResponse": res_body
                })
        except urllib.error.HTTPError as e:
            err_text = e.read(2048).decode("utf-8", errors="replace")
            self.send_json({
                "success": False,
                "error": f"Media Studio rejected request ({e.code}): {err_text}"
            }, status=HTTPStatus.BAD_GATEWAY)
        except Exception as e:
            self.send_json({
                "success": False,
                "uncertain": True,
                "error": "Media Studio did not confirm the result. Retry this same request to check using its idempotency key."
            }, status=HTTPStatus.SERVICE_UNAVAILABLE)

    def handle_static(self, url_path: str):
        if url_path in ("", "/"):
            file_path = PUBLIC_DIR / "index.html"
        else:
            rel = url_path.lstrip("/")
            file_path = PUBLIC_DIR / rel

        try:
            resolved = file_path.resolve()
            if not resolved.is_relative_to(PUBLIC_DIR.resolve()):
                self.send_error(HTTPStatus.FORBIDDEN, "Access denied")
                return
        except Exception:
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return

        if not resolved.exists() or not resolved.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return

        mime_type, _ = mimetypes.guess_type(str(resolved))
        if not mime_type:
            mime_type = "application/octet-stream"

        content = resolved.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{mime_type}; charset=utf-8" if "text" in mime_type else mime_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def run_server(port: int = 8080):
    host = os.environ.get("HUB_HOST", "127.0.0.1")
    server_address = (host, port)
    httpd = ThreadingHTTPServer(server_address, IntelligenceHubHandler)
    print(f"[intelligence-hub] Server running on http://{host}:{port}")
    print(f"[intelligence-hub] Media Studio API linked: {MEDIA_STUDIO_API_URL}")
    httpd.serve_forever()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port)
