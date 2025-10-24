# tools/kroki_render.py
# Render a diagram source (PlantUML or DOT) to PNG via Kroki using stdlib only.

from __future__ import annotations
import sys
from pathlib import Path
import urllib.request
import urllib.error

# Map diagram type to Kroki endpoint path
ENDPOINTS = {
    "plantuml": "/plantuml/png",
    "dot": "/graphviz/png",
}

def render(src: Path, out: Path, dtype: str, server: str = "https://kroki.io") -> int:
    dtype = dtype.lower()
    if dtype not in ENDPOINTS:
        print(f"[kroki] unsupported type: {dtype}. Use 'plantuml' or 'dot'.", file=sys.stderr)
        return 2

    try:
        body = src.read_text(encoding="utf-8").encode("utf-8")
    except Exception as e:
        print(f"[kroki] failed to read {src}: {e}", file=sys.stderr)
        return 3

    url = server.rstrip("/") + ENDPOINTS[dtype]
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "text/plain")

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
    except urllib.error.HTTPError as e:
        print(f"[kroki] http {e.code}: {e.read()[:200]!r}", file=sys.stderr)
        return 4
    except Exception as e:
        print(f"[kroki] request failed: {e}", file=sys.stderr)
        return 5

    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
    except Exception as e:
        print(f"[kroki] write failed: {e}", file=sys.stderr)
        return 6

    print(f"[kroki] wrote {out}")
    return 0


def main() -> int:
    if len(sys.argv) not in (4, 5):
        print("Usage: python tools/kroki_render.py <src> <out.png> <plantuml|dot> [server]", file=sys.stderr)
        return 1
    src = Path(sys.argv[1])
    out = Path(sys.argv[2])
    dtype = sys.argv[3]
    server = sys.argv[4] if len(sys.argv) == 5 else "https://kroki.io"
    return render(src, out, dtype, server)

if __name__ == "__main__":
    sys.exit(main())
