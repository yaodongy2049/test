import feedparser
import re
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple

RSS_URLS = [
    "https://iopscience.iop.org/journal/rss/0964-1726",
    "https://ieeexplore.ieee.org/rss/TOC7361.XML",
    "https://advanced.onlinelibrary.wiley.com/feed/16163028/most-recent",
    "https://www.nature.com/ncomms.rss",
]

# ===== Bucket 1: STRICT ME =====
ME_STRICT = [
    r"magneto[-\s]?electric",
    r"multiferroic",
    r"\bME\s*(coupling|coefficient)\b",
    r"strain[-\s]?mediated\s+magneto[-\s]?electric",
    r"magnetostrictive[-\s]piezoelectric|piezoelectric[-\s]magnetostrictive",
]

# ===== Bucket 2: CANDIDATE (still relevant, but not requiring explicit "magnetoelectric") =====
# Must satisfy: (materials/coupling terms) AND (device terms)
CAND_MATERIAL = [
    r"magnetostrictive|magnetostriction",
    r"piezoelectric|\bpzt\b|\bpmn[-\s]?pt\b|\bmetglas\b|\bterfenol[-\s]?d\b",
    r"fegab|fe[-\s]?co[-\s]?sib|fe[-\s]?cob|metglas",
    r"\bAlN\b|\bScAlN\b|scandium[-\s]?doped\s+AlN",
    r"laminate|composite|heterostructure",
]
CAND_DEVICE = [
    r"sensor|sensing|magnetometer|gradiometer",
    r"antenna|wireless|communication|receiver|transmit|\btx\b|\brx\b",
    r"transducer|resonator|acoustic|fb ar|pmut|cmut|mems|nems",
    r"\bVLF\b|\bELF\b",
]

# ===== global excludes (kill obvious junk) =====
EXCLUDE = [
    # non-paper TOC items
    r"publication information|sensors council|editorial board|call for papers|about this journal",
    # generic sensor flood / unrelated areas
    r"soil moisture|salinity|image sensor|adc|tdc|cmos",
    r"molecular communication|bionanosensor",   # your IEEE hit
    # AFM magnetism-review & EMI/absorption flood
    r"electromagnetic interference|EMI shielding|microwave absorption|wave absorption|stealth",
    r"magnetic anisotropy|spin valve|all[-\s]?optical switching|skyrmion|spin transport|van der waals magnetic",
    r"antiferromagnetic materials exhibiting|reconfigurable 3d magnetic nanoarchitectures",
    r"unclonable functions|remanence|anhysteretic",
    # bio/medical
    r"wound healing|diabetic|cardiovascular|drug delivery|protein|gene|cancer|tumor",
    # energy materials
    r"battery|supercapacitor|electrode|lithium|sodium[-\s]?ion",
    r"photovoltaic|solar cell|perovskite",
    r"catalysis|electrocatal|photocatal|her|oer|orr|co2 reduction",
    # geoscience / planet / shock compression etc
    r"magma oceans|super-earth|shock compression|FeOOH",
    # tactile/tribo etc (your earlier AFM flood)
    r"triboelectric|iontronic|tactile|glove|pressure sensor|keyboard",
]

OUT_DIR = Path("./radar_out")
SEEN_JSON = OUT_DIR / "seen.json"
OUT_ME_CSV = OUT_DIR / "literature_radar_ME_new.csv"
OUT_CAND_CSV = OUT_DIR / "literature_radar_candidate_new.csv"
SEEN_TTL_DAYS = 365

def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def _safe(x) -> str:
    return (x or "").strip()

def _match(text: str, patterns) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)

def _load_seen(path: Path) -> Dict[str, float]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _save_seen(path: Path, seen: Dict[str, float]) -> None:
    path.write_text(json.dumps(seen, indent=2, sort_keys=True), encoding="utf-8")

def _prune_seen(seen: Dict[str, float], ttl_days: int) -> Dict[str, float]:
    if ttl_days <= 0:
        return seen
    cutoff = datetime.now().timestamp() - ttl_days * 86400
    return {k: v for k, v in seen.items() if v >= cutoff}

def _entry_id(e) -> str:
    for key in ("id", "guid"):
        if hasattr(e, key) and getattr(e, key):
            return str(getattr(e, key))
    link = getattr(e, "link", "") or ""
    title = getattr(e, "title", "") or ""
    return f"{link}||{title}"

def _published_str(e) -> str:
    return _safe(getattr(e, "published", "") or getattr(e, "updated", ""))

def _summary_text(e) -> str:
    return _safe(getattr(e, "summary", "") or getattr(e, "description", ""))

def _write_csv(path: Path, rows: List[Tuple[str, str, str, str, str, str]]):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["timestamp", "source", "published", "bucket", "title", "link"])
        for r in rows:
            w.writerow(list(r))

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    seen = _prune_seen(_load_seen(SEEN_JSON), SEEN_TTL_DAYS)

    ts = _now_str()
    me_rows = []
    cand_rows = []

    for url in RSS_URLS:
        feed = feedparser.parse(url)
        source_title = _safe(getattr(feed.feed, "title", "")) or url

        for e in feed.entries:
            title = _safe(getattr(e, "title", ""))
            link = _safe(getattr(e, "link", ""))
            published = _published_str(e)
            summary = _summary_text(e)
            text = f"{title}\n{summary}"

            if EXCLUDE and _match(text, EXCLUDE):
                continue

            eid = _entry_id(e)
            if eid in seen:
                continue

            is_me = _match(text, ME_STRICT)

            # Candidate must satisfy BOTH material/coupling and device terms
            is_cand = _match(text, CAND_MATERIAL) and _match(text, CAND_DEVICE)

            if not (is_me or is_cand):
                continue

            seen[eid] = datetime.now().timestamp()

            if is_me:
                me_rows.append((ts, source_title, published, "ME_STRICT", title, link))
            else:
                cand_rows.append((ts, source_title, published, "CANDIDATE", title, link))

    _save_seen(SEEN_JSON, seen)

    if me_rows:
        _write_csv(OUT_ME_CSV, me_rows)
        print(f"[{ts}] NEW ME_STRICT: {len(me_rows)} | {OUT_ME_CSV.resolve()}")
    else:
        print(f"[{ts}] NEW ME_STRICT: 0")

    if cand_rows:
        _write_csv(OUT_CAND_CSV, cand_rows)
        print(f"[{ts}] NEW CANDIDATE: {len(cand_rows)} | {OUT_CAND_CSV.resolve()}")
    else:
        print(f"[{ts}] NEW CANDIDATE: 0")

    print(f"Seen DB: {SEEN_JSON.resolve()}")

if __name__ == "__main__":
    main()
