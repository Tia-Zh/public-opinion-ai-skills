import importlib.util
import json
import sys


REQUIRED_PACKAGES = [
    {
        "pip_name": "pandas",
        "import_name": "pandas",
        "purpose": "read, clean, merge, and export tabular data",
        "required": True,
    },
]

RECOMMENDED_PACKAGES = [
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
]

OPTIONAL_PACKAGES = [
    {
        "pip_name": "matplotlib",
        "import_name": "matplotlib",
        "purpose": "generate summary charts",
        "optional": True,
    },
]


def main():
    rows = []
    required_missing = []
    recommended_missing = []
    for package in REQUIRED_PACKAGES + RECOMMENDED_PACKAGES + OPTIONAL_PACKAGES:
        available = importlib.util.find_spec(package["import_name"]) is not None
        row = {
            **package,
            "available": available,
        }
        rows.append(row)
        if package.get("required") and not available:
            required_missing.append(package["pip_name"])
        if package.get("recommended") and not available:
            recommended_missing.append(package["pip_name"])

    install_packages = required_missing + recommended_missing
    result = {
        "python": sys.executable,
        "packages": rows,
        "required_missing": required_missing,
        "recommended_missing": recommended_missing,
        "install_command": f"{sys.executable} -m pip install " + " ".join(install_packages) if install_packages else "",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
