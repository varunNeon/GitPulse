# ⚡ GitPulse — GitHub Repository Intelligence Pipeline

> Real-time intelligence across the AI/ML GitHub ecosystem. GitPulse automatically ingests, processes, scores, and visualizes data from hundreds of AI/ML repositories — running fully autonomously every day.

**🔴 Live Dashboard:** [gitpulse-64rqmapppv4wwlu8qpghuam.streamlit.app](https://gitpulse-64rqmapppv4wwlu8qpghuam.streamlit.app)

---

## What is GitPulse?

Most GitHub trend tools just show you star counts. GitPulse goes deeper — it tracks 148 AI/ML repositories across 8 topics, calculates a composite impact score for each one, detects anomalous growth patterns, and surfaces hidden gems that most people haven't noticed yet.

The pipeline runs automatically every day at 6AM IST via GitHub Actions, writes fresh data into a cloud PostgreSQL database, and the dashboard reflects the latest state in real time.

---

## Architecture

```
GitHub REST API
      ↓
[INGESTION]  fetch_repos.py — pulls top 25 repos per topic, 8 topics
      ↓
[TRANSFORM]  transform.py — cleans JSON, removes duplicates, extracts fields
      ↓
[LOAD]       load.py — upserts into PostgreSQL star schema
      ↓
[POSTGRESQL] Supabase cloud — dim_repos, dim_users, fact_repo_stats, fact_repo_scores
      ↓
[ANALYSIS]   impact_score.py — weighted scoring, hidden gems, trend detection
      ↓
[DASHBOARD]  Streamlit — 4-page interactive intelligence interface
      ↑
[SCHEDULER]  GitHub Actions — runs full pipeline daily at 00:30 UTC (6AM IST)
```

---

## Features

**Overview Page**
- KPI metrics — repos tracked, total stars, top impact score, language diversity
- Hidden Gems — underrated repos with high fork ratio but below-median star count
- Top 5 repos by composite impact score
- Stars by language and topic distribution charts

**Leaderboard**
- All 148 repos ranked by impact score
- Filter by programming language and topic
- Score breakdown showing star, fork, and issue contributions

**Trends**
- Fastest growing repos by daily star growth
- Star growth over time line chart with repo comparison
- Identifies momentum shifts across the AI/ML ecosystem

**Anomaly Detection**
- Statistical 2σ threshold detection on daily star growth
- Flags repos with unusually high activity (viral growth events)
- Visual comparison of normal vs anomalous growth patterns

---

## Impact Score Formula

Each repo is scored using a weighted composite of three normalized metrics:

```
Impact Score = (0.50 × Star Velocity) + (0.30 × Fork Score) + (0.20 × Issue Score)
```

- **Star Velocity** — normalized star count relative to all tracked repos
- **Fork Score** — fork-to-star ratio, measuring how actively people build on it
- **Issue Score** — open issue count, measuring active usage and community engagement

All metrics are min-max normalized to [0, 1] before scoring.

---

## Database Schema (Star Schema)

```
dim_repos          — repository metadata (id, name, language, topics, url)
dim_users          — contributor/owner profiles
fact_repo_stats    — daily snapshots (stars, forks, watchers, open_issues)
fact_repo_scores   — daily impact scores (star_velocity, fork_score, impact_score)
```

Fact tables reference dimension tables via foreign keys, following standard data warehouse design patterns.

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Data Source | GitHub REST API | Live repository data |
| Ingestion | Python + Requests | API fetching with auth |
| Transform | Pandas | Cleaning, deduplication, feature engineering |
| Storage | PostgreSQL (Supabase) | Cloud data warehouse |
| ORM | SQLAlchemy | Database abstraction |
| Analysis | Pandas + NumPy | Statistical scoring and anomaly detection |
| Dashboard | Streamlit + Plotly | Interactive visualization |
| Scheduler | GitHub Actions | Daily automated pipeline runs |
| Secrets | GitHub Secrets + .env | Credential management |

---

## Topics Tracked

`machine-learning` · `deep-learning` · `llm` · `computer-vision` · `data-engineering` · `mlops` · `pytorch` · `transformers`

---

## Running Locally

**Prerequisites:** Python 3.11+, PostgreSQL

**1. Clone the repository**
```bash
git clone https://github.com/varunNeon/GitPulse.git
cd GitPulse
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Set up environment variables**

Create a `.env` file in the project root:
```
GITHUB_TOKEN=your_github_pat
DB_HOST=your_db_host
DB_PORT=5432
DB_NAME=gitpulse
DB_USER=postgres
DB_PASSWORD=your_password
```

**4. Initialize the database**
```bash
python -m warehouse.schema
```

**5. Run the pipeline**
```bash
python -m pipeline.runner
```

**6. Calculate impact scores**
```bash
python -m analysis.impact_score
```

**7. Launch the dashboard**
```bash
streamlit run dashboard/app.py
```

---

## Project Structure

```
GitPulse/
├── ingestion/
│   ├── __init__.py
│   └── fetch_repos.py       # GitHub API fetcher
├── pipeline/
│   ├── __init__.py
│   ├── transform.py         # Data cleaning and transformation
│   ├── load.py              # Database loading with upsert logic
│   └── runner.py            # ETL orchestrator
├── warehouse/
│   ├── __init__.py
│   ├── db.py                # Database connection manager
│   ├── schema.py            # Table creation
│   └── cleanup.py           # Duplicate removal utility
├── analysis/
│   ├── __init__.py
│   ├── impact_score.py      # Scoring engine + hidden gems
│   └── trends.py            # Growth analysis + anomaly detection
├── dashboard/
│   └── app.py               # Streamlit dashboard
├── .github/
│   └── workflows/
│       └── pipeline.yml     # GitHub Actions daily scheduler
├── requirements.txt
├── .python-version
└── .gitignore
```

---

## Automated Pipeline

The pipeline runs automatically every day at **6:00 AM IST** via GitHub Actions:

1. GitHub spins up an Ubuntu runner
2. Installs Python dependencies
3. Fetches fresh data from GitHub API (200 repos → 148 unique after deduplication)
4. Loads into Supabase PostgreSQL
5. Recalculates all impact scores
6. Dashboard reflects updated data automatically

No manual intervention required.

---

## Built By

**Varun Lal** — MSc Data Science & Analytics, Jain University

[GitHub](https://github.com/varunNeon) · [LinkedIn](https://www.linkedin.com/in/varunnlal/)

---

*GitPulse v1.0 — Built as a portfolio project demonstrating end-to-end data engineering: API ingestion, ETL pipeline, cloud data warehouse, statistical analysis, and automated deployment.*
