# GitPulse

An automated data pipeline that tracks AI/ML repositories on GitHub, scores them by impact, and surfaces trends through a live dashboard.

**Live:** [gitpulse-64rqmapppv4wwlu8qpghuam.streamlit.app](https://gitpulse-64rqmapppv4wwlu8qpghuam.streamlit.app)

---

## What it does

GitPulse pulls data on 148 AI/ML repositories across 8 topics every day, loads it into a PostgreSQL database, and calculates a composite impact score for each repo. The dashboard shows which repos are growing fastest, flags unusual spikes, and surfaces underrated repos with high momentum but low visibility.

The whole thing runs automatically at 6AM IST via GitHub Actions. No manual steps needed after setup.

---

## Architecture

```
GitHub REST API
      |
   fetch_repos.py      pulls top 25 repos per topic across 8 AI/ML topics
      |
   transform.py        cleans raw JSON, removes cross-topic duplicates
      |
   load.py             upserts into PostgreSQL with star schema design
      |
   PostgreSQL          Supabase cloud (dim_repos, fact_repo_stats, fact_repo_scores)
      |
   impact_score.py     calculates weighted scores, finds hidden gems
      |
   app.py              Streamlit dashboard, 4 pages
      |
   pipeline.yml        GitHub Actions runs the full pipeline daily
```

---

## Dashboard pages

**Overview** — KPI metrics, hidden gems section, top 5 by impact score, stars by language and topic charts

**Leaderboard** — all 148 repos ranked by impact score with language and topic filters, score breakdown columns showing what drove each rank

**Trends** — daily star growth chart, repo comparison over time

**Anomaly Detection** — repos flagged by 2 standard deviation threshold on growth rate, with a visual showing normal vs flagged repos

---

## Impact score

Each repo gets a score between 0 and 1 based on three factors:

```
Impact Score = (0.50 x Star Velocity) + (0.30 x Fork Score) + (0.20 x Issue Score)
```

Star velocity measures popularity relative to all tracked repos. Fork score measures the fork-to-star ratio, which captures how actively people build on top of a repo. Issue score uses open issue count as a proxy for active usage. All three are min-max normalized before combining.

A repo with 10k stars but a high fork ratio often tells you more about real adoption than one with 100k stars that nobody forks.

---

## Database schema

Two dimension tables store descriptive info. Two fact tables store daily measurements.

```
dim_repos           name, language, topics, URL, timestamps
dim_users           username, followers, public repos
fact_repo_stats     daily snapshot of stars, forks, watchers, open issues
fact_repo_scores    daily impact scores and component breakdown
```

Fact tables reference dim_repos by foreign key. Running the pipeline daily means each table accumulates one new row per repo per day, which is what makes the trend charts work over time.

---

## Tech stack

| Layer | Tool |
|---|---|
| Source | GitHub REST API |
| Ingestion | Python, Requests |
| Transform | Pandas |
| Storage | PostgreSQL via Supabase |
| ORM | SQLAlchemy |
| Analysis | Pandas, NumPy |
| Dashboard | Streamlit, Plotly |
| Scheduler | GitHub Actions |

---

## Topics tracked

machine-learning, deep-learning, llm, computer-vision, data-engineering, mlops, pytorch, transformers

---

## Running locally

Requires Python 3.11 and a PostgreSQL database.

```bash
git clone https://github.com/varunNeon/GitPulse.git
cd GitPulse
pip install -r requirements.txt
```

Create a `.env` file:

```
GITHUB_TOKEN=your_github_pat
DB_HOST=your_db_host
DB_PORT=5432
DB_NAME=gitpulse
DB_USER=postgres
DB_PASSWORD=your_password
```

Then run:

```bash
python -m warehouse.schema        # create tables
python -m pipeline.runner         # fetch and load data
python -m analysis.impact_score   # calculate scores
streamlit run dashboard/app.py    # launch dashboard
```

---

## Project structure

```
GitPulse/
  ingestion/
    fetch_repos.py       GitHub API fetcher
  pipeline/
    transform.py         cleaning and deduplication
    load.py              database loading with upsert logic
    runner.py            runs the full ETL in sequence
  warehouse/
    db.py                database connection
    schema.py            table definitions
    cleanup.py           removes duplicate rows
  analysis/
    impact_score.py      scoring and hidden gems
    trends.py            growth and anomaly detection
  dashboard/
    app.py               Streamlit app
  .github/workflows/
    pipeline.yml         daily GitHub Actions schedule
```

---

## Built by

Varun Lal — MSc Data Science and Analytics, Jain University

[GitHub](https://github.com/varunNeon) · [LinkedIn](https://www.linkedin.com/in/varunnlal/)
