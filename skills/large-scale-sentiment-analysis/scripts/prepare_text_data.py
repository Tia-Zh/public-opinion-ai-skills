"""Prepare text for sentiment analysis without silently collapsing volume.

Default behavior keeps repeated comments because repeated comments may represent
real public-opinion volume. The script always records text_hash and
duplicate_count. It only removes duplicate rows when --dedupe-mode is explicitly
set to exact-text or source-date-text for expression-level analysis or spam
cleanup.
"""

import argparse
import hashlib
import re
from pathlib import Path

import pandas as pd


LOW_INFO = {
    "转发了", "转发", "分享", "666", "888", "999", "哈哈", "哈哈哈", "呵呵", "嗯", "嗯嗯", "哦", "啊",
    "了解", "好的", "收到", "知道了", "早安", "晚安",
}

SHORT_ATTITUDE_RE = re.compile(
    r"(\[(赞|强|爱心|心|比心|鼓掌|加油|支持|反对|怒|弱|鄙视|吐槽|裂开)\]|"
    r"[👍👎❤❤️💪👏🙌✅❌😡🤬💔]|"
    r"赞|支持|赞成|同意|点赞|强|顶|好评|反对|不同意|不支持|差评|无语|离谱|荒唐|不满|反感)"
)
BRACKET_TOKEN_RE = re.compile(r"(\[[^\]]{1,8}\]\s*)+")


def normalize_text(x):
    if pd.isna(x):
        return ""
    text = str(x)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"@\S+", "", text)
    text = re.sub(r"#([^#]+)#", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def info_len(text):
    t = re.sub(r"\[[^\]]+\]", "", str(text))
    t = re.sub(r"[\s\W_]+", "", t, flags=re.UNICODE)
    return len(t)


def has_short_attitude_signal(text):
    return bool(SHORT_ATTITUDE_RE.search(str(text)))


def is_low_information_candidate(text):
    text = str(text).strip()
    compact = re.sub(r"\s+", "", text)
    if compact in LOW_INFO:
        return True
    if BRACKET_TOKEN_RE.fullmatch(compact) and not has_short_attitude_signal(compact):
        return True
    if info_len(compact) == 0 and compact and not has_short_attitude_signal(compact):
        return True
    return False


def hash_value(x, salt):
    if pd.isna(x) or str(x).strip() == "":
        return ""
    return hashlib.sha256((salt + "|" + str(x).strip()).encode("utf-8")).hexdigest()[:16]


def read_input(path, sheet=None):
    path = Path(path)
    if path.suffix.lower() in [".xlsx", ".xls"]:
        return pd.read_excel(path, sheet_name=sheet or 0)
    return pd.read_csv(path, encoding="utf-8-sig")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--text-col", required=True)
    ap.add_argument("--sheet")
    ap.add_argument("--date-col")
    ap.add_argument("--source-col")
    ap.add_argument("--hash-col")
    ap.add_argument("--salt", default="large-scale-sentiment-analysis")
    ap.add_argument("--min-info-len", type=int, default=0)
    ap.add_argument(
        "--drop-obvious-low-info",
        action="store_true",
        help="Drop a very small set of obvious non-attitude rows such as forwarding markers.",
    )
    ap.add_argument(
        "--dedupe-mode",
        choices=["none", "exact-text", "source-date-text"],
        default="none",
        help="Default keeps all repeated comments for volume analysis. Use a dedupe mode only for expression-level analysis.",
    )
    args = ap.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = read_input(args.input, args.sheet)
    raw_rows = len(df)
    df["clean_text"] = df[args.text_col].apply(normalize_text)
    df["info_len"] = df["clean_text"].apply(info_len)
    df["short_attitude_signal"] = df["clean_text"].apply(has_short_attitude_signal)
    df["low_information_candidate"] = df["clean_text"].apply(is_low_information_candidate)
    df["date"] = pd.to_datetime(df[args.date_col], errors="coerce").dt.date.astype("string") if args.date_col else ""
    df["source"] = df[args.source_col].astype("string") if args.source_col else ""
    df["source_hash"] = df[args.hash_col].apply(lambda x: hash_value(x, args.salt)) if args.hash_col else ""
    df["text_hash"] = df["clean_text"].apply(lambda x: hash_value(x, args.salt))

    cleaned = df[df["clean_text"].ne("")].copy()
    nonempty_rows = len(cleaned)
    low_info_mask = cleaned["low_information_candidate"] & ~cleaned["short_attitude_signal"]
    low_info_removed = int(low_info_mask.sum()) if args.drop_obvious_low_info else 0
    if args.drop_obvious_low_info:
        cleaned = cleaned[~low_info_mask].copy()
    if args.min_info_len > 0:
        short_mask = (cleaned["info_len"] < args.min_info_len) & ~cleaned["short_attitude_signal"]
        short_removed = int(short_mask.sum())
        short_kept = int(((cleaned["info_len"] < args.min_info_len) & cleaned["short_attitude_signal"]).sum())
        cleaned = cleaned[~short_mask].copy()
    else:
        short_removed = 0
        short_kept = int(cleaned["short_attitude_signal"].sum())

    # Mark duplicate expressions for audit while preserving all rows by default.
    # Do not interpret the drop_duplicates branches below as the normal path:
    # they run only when --dedupe-mode is explicitly set away from "none".
    cleaned["duplicate_count"] = cleaned.groupby(["clean_text"])["clean_text"].transform("size")
    duplicate_extra_rows = int(len(cleaned) - cleaned["clean_text"].nunique())
    if args.dedupe_mode == "exact-text":
        cleaned = cleaned.drop_duplicates(subset=["clean_text"]).copy()
    elif args.dedupe_mode == "source-date-text":
        cleaned = cleaned.drop_duplicates(subset=["source", "date", "clean_text"]).copy()
    cleaned = cleaned.reset_index(drop=True)
    cleaned["row_id"] = range(len(cleaned))

    cols = [
        "row_id",
        "source",
        "date",
        "clean_text",
        "info_len",
        "short_attitude_signal",
        "low_information_candidate",
        "text_hash",
        "duplicate_count",
        "source_hash",
    ]
    cleaned[cols].to_csv(out_dir / "prepared_texts.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(
        [
            ["raw_rows", raw_rows],
            ["nonempty_rows", nonempty_rows],
            ["low_info_removed", low_info_removed],
            ["short_removed_by_min_len", short_removed],
            ["short_attitude_rows_kept", short_kept],
            ["low_information_candidates", int(cleaned["low_information_candidate"].sum())],
            ["prepared_rows", len(cleaned)],
            ["unique_clean_texts", cleaned["clean_text"].nunique()],
            ["duplicate_extra_rows_before_dedupe", duplicate_extra_rows],
            ["dedupe_mode", args.dedupe_mode],
            ["min_info_len", args.min_info_len],
        ],
        columns=["metric", "value"],
    ).to_csv(out_dir / "data_summary.csv", index=False, encoding="utf-8-sig")

    print(out_dir / "prepared_texts.csv")


if __name__ == "__main__":
    main()
