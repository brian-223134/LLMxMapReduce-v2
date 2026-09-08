"""KISTI same-corpus 실험용 공용 헬퍼 — scripts/*.py 와 tests/ 가 공유한다. 외부 의존성 없음.

- id 규칙 B (kisti_data/docs/asg/README.md §1.3): KISTI DOI `10.48550/arxiv.<id>` → arXiv base id,
  그 외 DOI → 소문자 DOI 문자열. adapter/common/ids.py 와 같은 규칙을 의존성 없이 다시 적는다.
- Stage 3 로그 파서: `<ts> [LEVEL] [module:line]` 헤더 줄 다음에 메시지 줄이 온다.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ARXIV_DOI_PREFIX = "10.48550/arxiv."
_VERSION = re.compile(r"v\d+$")
_NEW_STYLE = re.compile(r"^\d{4}\.\d{4,5}$")
_OLD_STYLE = re.compile(r"^[a-z\-]+(\.[a-z]{2})?/\d{7}$", re.IGNORECASE)
LOG_HEADER = re.compile(r"^(\d{4}-\d{2}-\d{2}-\d{2}:\d{2}:\d{2}\.\d+) \[(\w+)\] \[([^\]]+)\]\s*$")
_CITE = re.compile(r"\[([\d,\s]+)\]")
_NON_ALNUM = re.compile(r"[^0-9a-z]+")


def arxiv_base(aid: str) -> str:
    return _VERSION.sub("", aid.strip())


def is_arxiv_id(s) -> bool:
    if not s:
        return False
    s = arxiv_base(str(s))
    return bool(_NEW_STYLE.match(s) or _OLD_STYLE.match(s))


def doi_to_id(doi: str) -> str:
    d = doi.strip().lower()
    if d.startswith(ARXIV_DOI_PREFIX):
        return arxiv_base(d[len(ARXIV_DOI_PREFIX):])
    return d


def norm_title(s: str) -> str:
    """소문자·영숫자만 남기고 공백 하나로 접는다 (제목 매칭용)."""
    return _NON_ALNUM.sub(" ", (s or "").lower()).strip()


def iter_jsonl(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def sha256_file(path, chunk=1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def parse_log_records(lines) -> list[dict]:
    """헤더 줄로 레코드를 나눈다. 반환: [{ts, level, module, message}] (message 는 줄바꿈 유지)."""
    records = []
    cur = None
    for raw in lines:
        line = raw.rstrip("\n")
        m = LOG_HEADER.match(line)
        if m:
            cur = {"ts": m.group(1), "level": m.group(2), "module": m.group(3), "message": ""}
            records.append(cur)
        elif cur is not None:
            cur["message"] = line if not cur["message"] else cur["message"] + "\n" + line
    return records


def parse_env_file(path, redact: bool = True) -> dict:
    """`export K=V  # comment` 줄만 읽는다. redact 면 `_`로 나눈 세그먼트에 KEY/SECRET/TOKEN/PASSWORD 가 있는 키의 값을 가린다 (MAX_TOKENS 는 해당 없음)."""
    out = {}
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line.startswith("export ") or "=" not in line:
            continue
        k, v = line[len("export "):].split("=", 1)
        v = v.split("#", 1)[0].strip().strip('"').strip("'")
        k = k.strip()
        if redact and any(seg in ("KEY", "SECRET", "TOKEN", "PASSWORD") for seg in k.upper().split("_")):
            v = "<redacted>" if v else ""
        out[k] = v
    return out


def split_references(content: str):
    """본문과 참고문헌 블록을 나눈다 (LLM×MR·AutoSurvey 모두 `## References` 헤딩)."""
    if not content:
        return "", ""
    parts = re.split(r"\n#+\s*References?\s*\n", "\n" + content, maxsplit=1, flags=re.IGNORECASE)
    body = parts[0]
    refs = parts[1] if len(parts) > 1 else ""
    return body, refs


def cited_indices(content: str) -> set[int]:
    body, _ = split_references(content)
    out = set()
    for grp in _CITE.findall(body):
        for tok in grp.split(","):
            tok = tok.strip()
            if tok.isdigit():
                out.add(int(tok))
    return out


def content_words(content: str) -> int:
    body, _ = split_references(content)
    return len(body.split())


def count_headings(content: str) -> int:
    body, _ = split_references(content)
    return sum(1 for l in body.splitlines() if l.lstrip().startswith("#"))


def percentile(sorted_vals, q: float):
    if not sorted_vals:
        return None
    idx = min(len(sorted_vals) - 1, max(0, int(round(q * (len(sorted_vals) - 1)))))
    return sorted_vals[idx]
