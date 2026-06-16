# Installation

## Option 1: Import ZIP files

Use the installable packages in `dist/`:

- `dist/data-processing-assistant-installable.zip`
- `dist/large-scale-sentiment-analysis-installable.zip`
- `dist/public-opinion-data-workflow-integrated-installable.zip`

Import the ZIP file into an agent platform that supports skills.

## Option 2: Copy skill folders

Copy one folder from `skills/` into the target agent's skill directory:

```text
skills/data-processing-assistant
skills/large-scale-sentiment-analysis
skills/public-opinion-data-workflow
```

## Health Check

Run:

```powershell
python tools/doctor.py --skip-deps
```

If Python dependencies are available, run:

```powershell
python tools/doctor.py
```

Required Python packages for the bundled scripts include `pandas` and `openpyxl`.
