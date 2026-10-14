# WorkPulse — Employee Performance Review System

**Understand Performance. Empower Growth.**

WorkPulse is a Streamlit and SQLite application for maintaining employee profiles, organizing review periods, recording weighted assessments, exploring real review data, and exporting filtered reports. It also provides optional experimental Decision Tree and Random Forest estimates using the project's NumPy-based implementations.

## Modules

- **Dashboard:** database-backed employee, review-period, assessment, and indicator counts; performance distribution; department comparison; monthly trends; recent reviews; and review follow-up.
- **Employees:** searchable and filterable directory with add, edit, and confirmed delete actions. Employee profiles are independent from assessments; adding a person does not invent review results.
- **Performance periods:** create, edit, activate, complete, and delete review windows. A period with assessments cannot be deleted.
- **Performance areas:** configure assessment indicators and their weights. Active weights must total 100%.
- **Assessments:** record per-indicator scores, reviewer comments, and dates. The overall score is calculated from the active weights and retained in assessment history.
- **Analytics:** filter recorded assessment data by period and department and explore outcome, distribution, and monthly charts.
- **Predictions:** evaluate models only when complete labelled records are available, show held-out metrics, estimate a category, and record predictions separately from human assessments.
- **Reports:** filter assessments by department, employee, and period; download the matching records as CSV.
- **Notifications:** review saved workflow updates and employees still awaiting assessment during an active period.
- **Settings:** persist workspace and administrator display preferences.

New databases start with five configurable assessment indicators, but **no fabricated employees or assessments**. The bundled CSVs are optional example datasets and are not automatically imported.

## Requirements

- Python 3.10 or newer
- Dependencies listed in `requirements.txt`

## Local setup

### Windows PowerShell

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Open <http://localhost:8501>. On first launch, WorkPulse creates or migrates `data/workpulse.db`. Back up this file to preserve employee and assessment data. The schema is documented in [`sql/schema.sql`](sql/schema.sql); application startup applies compatible migrations to existing databases.

## Run tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Prediction and assessment methodology

- Reviews are human-entered assessments. Their category labels are derived from the weighted overall score: under 60 is **Needs Support**, under 80 is **Moderate**, and 80 or above is **High**.
- A model estimate is clearly identified as a prediction and never replaces or edits an assessment.
- Model training uses complete historical rows with an actual `performance_category`. The label is excluded from the input-feature list; the existing trainer evaluates using a separate held-out test split.
- If there are not enough complete labelled rows to evaluate a model, the Predictions page explains why rather than showing made-up metrics.
- Model scores are experimental decision support and must not be used as the sole basis for employment decisions.

## Security and deployment

The application currently has **no authentication or role-based access control**. The administrator name in Settings is only a display preference; it does not establish identity or permissions. Do not expose this app publicly with real employee information until authentication, authorization, and an appropriate data-protection policy have been implemented.

For a hosted Streamlit deployment, connect the repository to Streamlit Community Cloud and select `app.py` as the entry point. The hosting provider, not your laptop, runs the app. The included SQLite database is local to the running instance and may not survive a restart or redeploy; use managed persistent storage before relying on hosted data.

## Project layout

```text
app.py                        Streamlit entry point
workpulse_ui.py               Navigation, dashboard, and module views
ui_components.py              Shared cards, headings, status, and chart styling
services/workpulse_service.py SQLite-backed employee and review workflows
database/db_manager.py        Existing employee, review, and model persistence
models/train_model.py         Decision Tree, Random Forest, metrics, explanations
sql/schema.sql                Database schema reference
tests/                        Unit and workflow tests
```
