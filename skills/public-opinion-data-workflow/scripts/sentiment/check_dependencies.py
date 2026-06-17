import importlib.util
import json
import sys


OPTIONAL_PACKAGES = [
    {
        "pip_name": "scikit-learn",
        "import_name": "sklearn",
        "purpose": "fast TF-IDF + logistic-regression classifier for large-scale text classification",
        "recommended": True,
    },
    {
        "pip_name": "openpyxl",
        "import_name": "openpyxl",
        "purpose": "read/write Excel workbooks",
        "recommended": True,
    },
    {
        "pip_name": "matplotlib",
        "import_name": "matplotlib",
        "purpose": "generate summary charts",
        "recommended": False,
    },
]


def main():
    rows = []
    missing = []
    for package in OPTIONAL_PACKAGES:
        available = importlib.util.find_spec(package["import_name"]) is not None
        row = {
            **package,
            "available": available,
        }
        rows.append(row)
        if package["recommended"] and not available:
            missing.append(package["pip_name"])

    result = {
        "python": sys.executable,
        "packages": rows,
        "recommended_missing": missing,
        "install_command": f"{sys.executable} -m pip install " + " ".join(missing) if missing else "",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
