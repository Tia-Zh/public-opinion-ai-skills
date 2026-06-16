import argparse
import hashlib
import re
from pathlib import Path

import pandas as pd


LOW_INFO = {
    "转发了", "转发", "分享", "666", "888", "999", "哈哈", "哈哈哈", "呵呵", "嗯", "哦", "啊", "行", "好", "赞",
}


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
    ap.add_argument("--min-info-len", type=int, default=3)
    args = ap.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = read_input(args.input, args.sheet)
    raw_rows = len(df)
    df["clean_text"] = df[args.text_col].apply(normalize_text)
    df["info_len"] = df["clean_text"].apply(info_len)
    df["date"] = pd.to_datetime(df[args.date_col], errors="coerce").dt.date.astype("string") if args.date_col else ""
    df["source"] = df[args.source_col].astype("string") if args.source_col else ""
    df["source_hash"] = df[args.hash_col].apply(lambda x: hash_value(x, args.salt)) if args.hash_col else ""

    cleaned = df[df["clean_text"].ne("")].copy()
    cleaned = cleaned[~cleaned["clean_text"].isin(LOW_INFO)].copy()
    cleaned = cleaned[cleaned["info_len"] >= args.min_info_len].copy()
    cleaned = cleaned.drop_duplicates(subset=["source", "date", "clean_text"]).copy().reset_index(drop=True)
    cleaned["row_id"] = range(len(cleaned))

    cols = ["row_id", "source", "date", "clean_text", "source_hash"]
    cleaned[cols].to_csv(out_dir / "prepared_texts.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(
        [["raw_rows", raw_rows], ["prepared_rows", len(cleaned)]],
        columns=["metric", "value"],
    ).to_csv(out_dir / "data_summary.csv", index=False, encoding="utf-8-sig")

    print(out_dir / "prepared_texts.csv")


if __name__ == "__main__":
    main()

