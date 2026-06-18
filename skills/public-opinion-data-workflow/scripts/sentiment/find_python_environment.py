import importlib.util
import json
import os
import platform
import subprocess
import sys


REQUIRED = ["pandas", "openpyxl"]
RECOMMENDED = ["sklearn"]


def check_command(command):
    probe = (
        "import importlib.util, json, sys; "
        f"mods={REQUIRED + RECOMMENDED!r}; "
        "print(json.dumps({'executable': sys.executable, "
        "'modules': {m: importlib.util.find_spec(m) is not None for m in mods}}, "
        "ensure_ascii=False))"
    )
    try:
        completed = subprocess.run(
            [*command, "-c", probe],
            check=True,
            capture_output=True,
            text=True,
            timeout=8,
        )
        data = json.loads(completed.stdout.strip().splitlines()[-1])
        data["command"] = " ".join(command)
        data["ok"] = True
        return data
    except Exception as exc:
        return {"command": " ".join(command), "ok": False, "error": str(exc)}


def main():
    candidates = []
    seen = set()

    raw_candidates = [[sys.executable]]
    env_python = os.environ.get("PYTHON")
    if env_python:
        raw_candidates.append([env_python])
    raw_candidates.append(["python"])
    if platform.system().lower().startswith("win"):
        raw_candidates.append(["py"])
    else:
        raw_candidates.append(["python3"])

    for command in raw_candidates:
        key = tuple(command)
        if key in seen:
            continue
        seen.add(key)
        candidates.append(check_command(command))

    usable = []
    for item in candidates:
        modules = item.get("modules") or {}
        required_missing = [m for m in REQUIRED if not modules.get(m)]
        recommended_missing = [m for m in RECOMMENDED if not modules.get(m)]
        item["required_missing"] = required_missing
        item["recommended_missing"] = recommended_missing
        if item.get("ok") and not required_missing:
            usable.append(item)

    best = None
    if usable:
        best = sorted(usable, key=lambda x: (len(x["recommended_missing"]), x["command"]))[0]

    print(
        json.dumps(
            {
                "required_modules": REQUIRED,
                "recommended_modules": RECOMMENDED,
                "best_python": best,
                "candidates": candidates,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
