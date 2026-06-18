import argparse
import importlib.util
import subprocess
import sys


CORE = ["pandas", "openpyxl"]
RECOMMENDED = ["scikit-learn"]
CHARTS = ["matplotlib"]


IMPORT_NAMES = {
    "scikit-learn": "sklearn",
}


def missing_packages(packages):
    missing = []
    for package in packages:
        import_name = IMPORT_NAMES.get(package, package.replace("-", "_"))
        if importlib.util.find_spec(import_name) is None:
            missing.append(package)
    return missing


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--include-charts",
        action="store_true",
        help="also install matplotlib for chart generation",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the install command without running it",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="install even if packages appear to be available",
    )
    args = parser.parse_args()

    packages = list(CORE) + list(RECOMMENDED)
    if args.include_charts:
        packages.extend(CHARTS)

    install_packages = packages if args.force else missing_packages(packages)
    if not install_packages:
        print("all requested packages already available; nothing to install", flush=True)
        return

    command = [sys.executable, "-m", "pip", "install", *install_packages]
    print(" ".join(command), flush=True)
    if args.dry_run:
        return
    subprocess.check_call(command)


if __name__ == "__main__":
    main()
