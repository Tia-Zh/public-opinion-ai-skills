import argparse
import subprocess
import sys


RECOMMENDED = ["scikit-learn", "openpyxl"]
CHARTS = ["matplotlib"]


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
    args = parser.parse_args()

    packages = list(RECOMMENDED)
    if args.include_charts:
        packages.extend(CHARTS)

    command = [sys.executable, "-m", "pip", "install", *packages]
    print(" ".join(command), flush=True)
    if args.dry_run:
        return
    subprocess.check_call(command)


if __name__ == "__main__":
    main()
