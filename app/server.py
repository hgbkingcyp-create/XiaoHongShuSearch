"""
测试产品服务器（零依赖，Python 标准库 http.server）。

运行：python3 server.py  →  http://localhost:8000

接口：
  GET  /api/tests                 列出所有测试
  GET  /api/test/<id>             返回题库（不含结果）；记录 start 事件
  POST /api/test/<id>/result      提交答案 → 返回免费结果(type/tagline/hook)；记录 complete 事件
  POST /api/test/<id>/report      提交答案 → 返回完整报告；记录 unlock 事件
  GET  /api/stats                 返回漏斗统计（start/complete/unlock + 转化率）

免费/付费拆分：
  /result 只返回免费的 type/tagline/hook；完整报告（portrait/strengths/blindspot/advice）
  在 /report。未来接入微信虚拟支付时，在 /report 处加支付鉴权即可。
"""
import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

import engine

ROOT = Path(__file__).parent
STATIC = ROOT / "static"
EVENTS = ROOT / "data" / "events.jsonl"

FREE_FIELDS = ("key", "type", "tagline", "hook")


def log_event(event: str, **data):
    """追加一条事件到 events.jsonl（漏斗埋点）。"""
    line = {"ts": datetime.now().isoformat(timespec="seconds"), "event": event, **data}
    with open(EVENTS, "a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")


def funnel_stats() -> dict:
    """读 events.jsonl，返回漏斗统计 + 转化率。"""
    counts = {"start": 0, "complete": 0, "unlock": 0}
    by_test = {}
    if EVENTS.exists():
        with open(EVENTS, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ev = e.get("event", "")
                counts[ev] = counts.get(ev, 0) + 1
                tid = e.get("test_id")
                if tid:
                    d = by_test.setdefault(tid, {"start": 0, "complete": 0, "unlock": 0})
                    d[ev] = d.get(ev, 0) + 1
    rates = {
        "complete_rate": round(counts["complete"] / counts["start"], 4) if counts["start"] else 0,
        "unlock_rate": round(counts["unlock"] / counts["complete"], 4) if counts["complete"] else 0,
    }
    return {"totals": counts, "rates": rates, "by_test": by_test}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if not isinstance(body, bytes):
            body = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            return json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return {}

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/tests":
            return self._send(200, engine.list_tests())
        if path == "/api/stats":
            return self._send(200, funnel_stats())
        if path.startswith("/api/test/"):
            test_id = path.rsplit("/", 1)[-1]
            try:
                test = engine.load_test(test_id)
            except FileNotFoundError:
                return self._send(404, {"error": f"测试不存在: {test_id}"})
            log_event("start", test_id=test_id)
            return self._send(200, {k: v for k, v in test.items() if k != "results"})
        return self._serve_static(path)

    def do_POST(self):
        path = urlparse(self.path).path
        body = self._read_json()

        if path.startswith("/api/test/") and path.endswith("/result"):
            return self._result(path, body, full=False)
        if path.startswith("/api/test/") and path.endswith("/report"):
            return self._result(path, body, full=True)
        return self._send(404, {"error": "not found"})

    def _result(self, path, body, full):
        test_id = path.split("/")[3]
        try:
            result = engine.get_result(test_id, body.get("answers", []))
        except FileNotFoundError:
            return self._send(404, {"error": f"测试不存在: {test_id}"})
        except ValueError as e:
            return self._send(400, {"error": str(e)})

        if full:
            log_event("unlock", test_id=test_id, result=result["key"])
            return self._send(200, result)
        log_event("complete", test_id=test_id, result=result["key"])
        return self._send(200, {k: result[k] for k in FREE_FIELDS})

    def _serve_static(self, path):
        if path in ("/", "/index.html"):
            path = "/index.html"
        file = STATIC / path.lstrip("/")
        if file.is_file() and file.suffix == ".html":
            return self._send(200, file.read_bytes(), "text/html; charset=utf-8")
        if file.is_file() and file.suffix in (".css", ".js"):
            ctype = "text/css" if file.suffix == ".css" else "application/javascript"
            return self._send(200, file.read_bytes(), ctype)
        return self._send(404, {"error": "not found"})

    def log_message(self, *args):
        pass  # 静默日志，避免刷屏


if __name__ == "__main__":
    port = 8000
    print(f"测试产品已启动: http://localhost:{port}")
    print("  API: /api/tests  /api/test/<id>  /api/test/<id>/result  /api/test/<id>/report  /api/stats")
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
