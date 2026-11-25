# COER Admission Intelligence AI

## Run on Windows
Install Python 3.10+. Extract this ZIP, open Command Prompt in the folder, then run:

```powershell
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m streamlit run app.py
```

Open http://localhost:8501.

## Deploy with GitHub + Streamlit Community Cloud
1. Create a GitHub repository (private initially is recommended).
2. Upload `app.py`, `requirements.txt`, `README.md`, and `coer_admission_data_template.csv`.
3. Sign in at https://share.streamlit.io/ with GitHub.
4. Create app; choose repository, branch `main`, main file `app.py`; deploy.

## Data format
Required: `state, district, city, applications, admissions`.
Recommended: `year, programme, pcm_students, school_count, coaching_count, marketing_spend, travel_km, competitor_count, latitude, longitude`.
CSV and XLSX are accepted.

## Important limitations
Demo data is fictional and is not COER's actual admission data or verified market research. Upload approved university data before relying on rankings. Do not upload identifiable student data to a public repository or public demo.

The opportunity score is a transparent heuristic, not a trained AI model. The admission estimate is a baseline using observed conversion. A robust predictive model needs several years of consistent, granular data, time-based testing, and reported error metrics.
