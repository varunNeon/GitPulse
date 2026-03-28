import os
import sys

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.impact_score import find_hidden_gems
from common.logging_config import get_logger
from warehouse.db import get_engine


logger = get_logger(__name__)

st.set_page_config(
    page_title="GitPulse",
    page_icon="GP",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');
:root{--bg:#030507;--bg-elev:#071018;--panel:rgba(7,16,24,.92);--panel-strong:rgba(9,22,18,.94);--border:rgba(58,120,96,.24);--text:#edf8f3;--muted:#8aa39b;--blue:#4f8cff;--cyan:#1ec7c1;--green:#49d17d;--green-deep:#0e3b2c;--blue-deep:#0f264f;--red:#ff6a7f;--amber:#c7f27b;}
html,body,[class*="css"]{font-family:'Space Grotesk',sans-serif;color:var(--text);}
[data-testid="stAppViewContainer"]{background:radial-gradient(circle at top left,rgba(30,199,193,.1),transparent 26%),radial-gradient(circle at top right,rgba(79,140,255,.12),transparent 28%),radial-gradient(circle at bottom right,rgba(73,209,125,.08),transparent 24%),linear-gradient(180deg,#010202 0%,#030507 38%,#071018 100%);}
[data-testid="stHeader"],#MainMenu,footer{visibility:hidden;}
.block-container{max-width:1480px;padding:1.4rem 2rem 2rem 2rem;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,rgba(4,8,11,.98) 0%,rgba(5,12,15,.98) 48%,rgba(6,15,22,.98) 100%);border-right:1px solid rgba(30,199,193,.16);}
[data-testid="stSidebar"] *{font-family:'IBM Plex Mono',monospace!important;}
[data-testid="stSidebarCollapseButton"] span{display:none;}
[data-testid="stMetric"]{background:linear-gradient(180deg,rgba(6,16,20,.92),rgba(7,13,24,.96));border:1px solid var(--border);border-radius:18px;padding:.9rem 1rem;transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease;}
[data-testid="stMetric"]:hover{transform:translateY(-2px);border-color:rgba(73,209,125,.42);box-shadow:0 16px 34px rgba(2,8,10,.28);}
[data-testid="stMetricLabel"]{font-family:'IBM Plex Mono',monospace!important;font-size:.68rem!important;letter-spacing:.16em;text-transform:uppercase;color:var(--muted)!important;}
[data-testid="stMetricValue"]{font-family:'IBM Plex Mono',monospace!important;color:var(--text)!important;font-size:1.55rem!important;text-shadow:0 0 18px rgba(73,209,125,.08);}
[data-testid="stMetricDelta"]{font-family:'IBM Plex Mono',monospace!important;}
[data-testid="stDataFrame"]{background:rgba(5,11,15,.9);border:1px solid rgba(58,120,96,.28);border-radius:18px;overflow:hidden;}
[data-testid="stSelectbox"] > div > div,[data-testid="stMultiSelect"] > div > div{background:rgba(5,12,16,.98)!important;border:1px solid rgba(58,120,96,.3)!important;border-radius:14px!important;}
[data-testid="stRadio"] label{font-size:.74rem!important;}
[data-testid="stRadio"] [role="radiogroup"]{gap:.45rem;}
[data-testid="stRadio"] [role="radio"]{background:rgba(7,16,22,.86);border:1px solid rgba(58,120,96,.22);border-radius:14px;padding:.6rem .75rem;transition:border-color .16s ease,background .16s ease,transform .16s ease;}
[data-testid="stRadio"] [role="radio"]:hover{transform:translateX(2px);border-color:rgba(79,140,255,.36);background:rgba(9,20,29,.96);}
hr{border-color:rgba(89,122,173,.16)!important;}
.shell,.panel,.status-card,.repo-card,.anomaly-card,.sidebar-block{background:linear-gradient(180deg,rgba(5,14,18,.94),rgba(6,11,20,.98));border:1px solid var(--border);box-shadow:inset 0 1px 0 rgba(255,255,255,.02);transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease;}
.shell{position:relative;overflow:hidden;border-radius:28px;padding:1.35rem 1.4rem;margin-bottom:1.2rem;box-shadow:0 22px 48px rgba(1,5,7,.42);}
.shell::before{content:"";position:absolute;inset:0;background-image:linear-gradient(rgba(30,199,193,.04) 1px,transparent 1px),linear-gradient(90deg,rgba(79,140,255,.04) 1px,transparent 1px);background-size:28px 28px;opacity:.22;pointer-events:none;}
.hero-grid{display:grid;grid-template-columns:1.6fr .9fr;gap:1rem;position:relative;z-index:1;}
.hero-eyebrow,.section-header,.panel-label,.status-label,.badge,.sidebar-kicker{font-family:'IBM Plex Mono',monospace;letter-spacing:.16em;text-transform:uppercase;}
.hero-eyebrow{color:var(--green);font-size:.72rem;margin-bottom:.55rem;}
.hero-title{font-size:clamp(2rem,4vw,3.3rem);line-height:.95;font-weight:700;color:var(--text);margin:0;max-width:10ch;}
.hero-title span{color:var(--cyan);}
.hero-copy{margin-top:.8rem;max-width:60ch;color:var(--muted);font-size:.96rem;line-height:1.55;}
.hero-badges{display:flex;flex-wrap:wrap;gap:.55rem;margin-top:1rem;}
.badge{padding:.45rem .7rem;border-radius:999px;font-size:.64rem;border:1px solid rgba(58,120,96,.3);background:linear-gradient(180deg,rgba(8,20,17,.95),rgba(8,16,24,.9));color:var(--text);}
.hero-side,.panel,.status-card,.repo-card,.anomaly-card,.sidebar-block{position:relative;overflow:hidden;border-radius:22px;}
.hero-side{padding:1rem;}
.status-stack{display:grid;gap:.75rem;}
.status-card{padding:.9rem 1rem;}
.status-label,.sidebar-kicker,.panel-label{color:var(--muted);font-size:.62rem;margin-bottom:.45rem;}
.status-value,.sidebar-value{color:var(--text);font-size:.94rem;line-height:1.6;}
.good{color:var(--green)!important;}
.warn{color:var(--amber)!important;}
.panel{padding:1rem 1.05rem;margin-bottom:1rem;}
.panel:hover,.repo-card:hover,.status-card:hover,.anomaly-card:hover,.sidebar-block:hover{transform:translateY(-2px);border-color:rgba(73,209,125,.34);box-shadow:0 18px 36px rgba(1,6,8,.24);}
.panel-value{font-family:'IBM Plex Mono',monospace;font-size:1.6rem;color:var(--text);font-weight:600;text-shadow:0 0 16px rgba(79,140,255,.08);}
.panel-meta,.repo-meta,.sidebar-value,.footer-note{color:var(--muted);font-size:.8rem;line-height:1.55;}
.section-header{display:flex;align-items:center;gap:.6rem;color:var(--green);font-size:.72rem;margin:1.1rem 0 .8rem 0;}
.section-header::before{content:"";width:30px;height:1px;background:linear-gradient(90deg,var(--green),transparent);}
.repo-card,.anomaly-card{padding:1rem 1.05rem;margin-bottom:.85rem;}
.repo-kicker{display:flex;justify-content:space-between;gap:.75rem;margin-bottom:.55rem;}
.repo-rank{font-family:'IBM Plex Mono',monospace;font-size:.67rem;color:var(--cyan);letter-spacing:.14em;text-transform:uppercase;}
.score-pill{display:inline-flex;align-items:center;justify-content:center;min-width:78px;padding:.3rem .65rem;border-radius:999px;background:rgba(79,140,255,.12);border:1px solid rgba(79,140,255,.24);color:#7fb0ff;font-family:'IBM Plex Mono',monospace;font-size:.74rem;font-weight:600;}
.repo-name,.anomaly-name{font-size:1.04rem;font-weight:700;color:var(--text);}
.gem-card{border-color:rgba(73,209,125,.28);}
.gem-card .repo-rank{color:var(--green);}
.anomaly-card{border-color:rgba(255,93,115,.26);}
.anomaly-growth{font-family:'IBM Plex Mono',monospace;color:var(--red);font-weight:600;}
.sidebar-title{font-size:1.6rem;line-height:.95;font-weight:700;color:var(--text);}
.sidebar-title span{color:var(--green);}
.sidebar-sub{color:var(--muted);font-size:.66rem;margin-top:.45rem;letter-spacing:.16em;text-transform:uppercase;}
.sidebar-block{padding:.9rem 1rem;margin-top:.75rem;border-radius:16px;}
.footer-note{text-align:center;font-family:'IBM Plex Mono',monospace;font-size:.72rem;padding:.8rem 0 .5rem 0;}
.footer-note a{color:var(--cyan);text-decoration:none;}
@media (max-width:1100px){.hero-grid{grid-template-columns:1fr;}}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data(ttl=3600)
def load_leaderboard():
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(
            text(
                """
                WITH latest_stats AS (
                    SELECT repo_id, snapshot_date, stars, forks, open_issues,
                           ROW_NUMBER() OVER (PARTITION BY repo_id ORDER BY snapshot_date DESC, id DESC) AS row_num
                    FROM fact_repo_stats
                ),
                latest_scores AS (
                    SELECT repo_id, snapshot_date, impact_score, star_velocity, fork_score, issue_score,
                           ROW_NUMBER() OVER (PARTITION BY repo_id ORDER BY snapshot_date DESC, id DESC) AS row_num
                    FROM fact_repo_scores
                )
                SELECT r.name, r.full_name, r.language, r.topics, r.html_url,
                       s.stars, s.forks, s.open_issues,
                       sc.impact_score, sc.star_velocity, sc.fork_score, sc.issue_score, sc.snapshot_date
                FROM dim_repos r
                JOIN latest_stats s ON r.repo_id = s.repo_id AND s.row_num = 1
                JOIN latest_scores sc ON r.repo_id = sc.repo_id AND sc.row_num = 1
                ORDER BY sc.impact_score DESC
                """
            ),
            conn,
        )


@st.cache_data(ttl=3600)
def load_trends():
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(
            text(
                """
                SELECT r.name, r.full_name, r.language, s.snapshot_date, s.stars, s.forks, s.open_issues
                FROM dim_repos r
                JOIN fact_repo_stats s ON r.repo_id = s.repo_id
                ORDER BY r.name, s.snapshot_date ASC
                """
            ),
            conn,
        )


@st.cache_data(ttl=3600)
def load_anomalies():
    df = load_trends()
    df = df.sort_values(["full_name", "snapshot_date"])
    df["star_growth"] = df.groupby("full_name")["stars"].diff()
    trend_df = df.dropna(subset=["star_growth"])
    if trend_df.empty:
        return pd.DataFrame()
    latest = trend_df.groupby("full_name").last().reset_index()
    threshold = latest["star_growth"].mean() + 2 * latest["star_growth"].std()
    anomalies = latest[latest["star_growth"] > threshold].sort_values("star_growth", ascending=False)
    return anomalies, threshold


@st.cache_data(ttl=3600)
def load_system_snapshot():
    engine = get_engine()
    with engine.connect() as conn:
        stats_result = conn.execute(
            text(
                """
                SELECT MAX(snapshot_date) AS latest_snapshot,
                       COUNT(*) FILTER (WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM fact_repo_stats)) AS latest_stats_rows,
                       COUNT(DISTINCT repo_id) FILTER (WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM fact_repo_stats)) AS latest_repo_count
                FROM fact_repo_stats
                """
            )
        ).mappings().one()
        scores_result = conn.execute(
            text(
                """
                SELECT MAX(snapshot_date) AS latest_score_snapshot,
                       COUNT(*) FILTER (WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM fact_repo_scores)) AS latest_score_rows
                FROM fact_repo_scores
                """
            )
        ).mappings().one()
        history_result = conn.execute(
            text(
                """
                SELECT
                    COUNT(DISTINCT snapshot_date) AS tracked_days,
                    COUNT(DISTINCT language) AS languages_covered
                FROM (
                    SELECT s.snapshot_date, r.language
                    FROM fact_repo_stats s
                    JOIN dim_repos r ON r.repo_id = s.repo_id
                ) history
                """
            )
        ).mappings().one()
    latest_snapshot = stats_result["latest_snapshot"]
    score_snapshot = scores_result["latest_score_snapshot"]
    status = "Pipeline healthy" if latest_snapshot and latest_snapshot == score_snapshot else "Needs review"
    return {
        "latest_snapshot": latest_snapshot,
        "latest_stats_rows": stats_result["latest_stats_rows"] or 0,
        "latest_repo_count": stats_result["latest_repo_count"] or 0,
        "latest_score_rows": scores_result["latest_score_rows"] or 0,
        "tracked_days": history_result["tracked_days"] or 0,
        "languages_covered": history_result["languages_covered"] or 0,
        "status": status,
    }


def build_chart_theme():
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(5, 12, 16, 0.92)",
        font=dict(family="IBM Plex Mono", color="#8aa39b", size=11),
        xaxis=dict(
            gridcolor="rgba(58, 120, 96, 0.16)",
            linecolor="rgba(58, 120, 96, 0.16)",
            tickcolor="rgba(58, 120, 96, 0.16)",
            zeroline=False,
            title_font=dict(color="#49d17d", family="IBM Plex Mono"),
        ),
        yaxis=dict(
            gridcolor="rgba(58, 120, 96, 0.16)",
            linecolor="rgba(58, 120, 96, 0.16)",
            tickcolor="rgba(58, 120, 96, 0.16)",
            zeroline=False,
            title_font=dict(color="#4f8cff", family="IBM Plex Mono"),
        ),
        margin=dict(l=20, r=20, t=40, b=20),
        title_font=dict(color="#edf8f3", family="Space Grotesk", size=18),
        legend=dict(font=dict(color="#8aa39b", family="IBM Plex Mono")),
    )


def render_section_header(title: str):
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)


def render_repo_card(rank: int, row, accent_class: str = ""):
    topics = row["topics"][:72] if row["topics"] else "No topic metadata"
    st.markdown(
        f"""
        <div class="repo-card {accent_class}">
            <div class="repo-kicker">
                <div class="repo-rank">Rank {rank:02d} | {row['language'] or 'Unknown'}</div>
                <div class="score-pill">{row['impact_score']:.4f}</div>
            </div>
            <div class="repo-name">{row['name']}</div>
            <div class="repo-meta">Stars {row['stars']:,} | Forks {row['forks']:,} | Issues {row['open_issues']:,}</div>
            <div class="repo-meta">{topics}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_shell_header(page_title: str, page_copy: str, snapshot: dict, repo_count: int, anomaly_count: int):
    latest_snapshot = snapshot["latest_snapshot"]
    latest_snapshot_text = latest_snapshot.strftime("%d %b %Y") if latest_snapshot else "No snapshot"
    health_class = "good" if snapshot["status"] == "Pipeline healthy" else "warn"
    st.markdown(
        f"""
        <div class="shell">
            <div class="hero-grid">
                <div>
                    <div class="hero-eyebrow">Developer Command Center</div>
                    <h1 class="hero-title">Git<span>Pulse</span> {page_title}</h1>
                    <div class="hero-copy">{page_copy}</div>
                    <div class="hero-badges">
                        <div class="badge">Snapshot {latest_snapshot_text}</div>
                        <div class="badge">Tracked repos {repo_count:,}</div>
                        <div class="badge">Topics 8</div>
                        <div class="badge">Anomalies {anomaly_count}</div>
                    </div>
                </div>
                <div class="hero-side">
                    <div class="status-stack">
                        <div class="status-card">
                            <div class="status-label">Pipeline status</div>
                            <div class="status-value {health_class}">{snapshot['status']}</div>
                        </div>
                        <div class="status-card">
                            <div class="status-label">Latest warehouse rows</div>
                            <div class="status-value">{snapshot['latest_stats_rows']:,} stats | {snapshot['latest_score_rows']:,} scores</div>
                        </div>
                        <div class="status-card">
                            <div class="status-label">Signal posture</div>
                            <div class="status-value">GitHub API to ETL to scoring to dashboard</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


CHART_THEME = build_chart_theme()

try:
    system_snapshot = load_system_snapshot()
except Exception:
    logger.exception("Failed to load system snapshot.")
    system_snapshot = {
        "latest_snapshot": None,
        "latest_stats_rows": 0,
        "latest_repo_count": 0,
        "latest_score_rows": 0,
        "tracked_days": 0,
        "languages_covered": 0,
        "status": "Needs review",
    }


with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-logo">
            <div class="sidebar-title">Git<span>Pulse</span></div>
            <div class="sidebar-sub">AI ecosystem telemetry</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    page = st.radio(
        "Navigate",
        ["Overview", "Leaderboard", "Trends", "Anomalies"],
        label_visibility="visible",
    )

    latest_snapshot = system_snapshot["latest_snapshot"]
    latest_snapshot_text = latest_snapshot.strftime("%d %b %Y") if latest_snapshot else "No snapshot"
    status_class = "good" if system_snapshot["status"] == "Pipeline healthy" else "warn"

    st.markdown(
        f"""
        <div class="sidebar-block">
            <div class="sidebar-kicker">Snapshot</div>
            <div class="sidebar-value">{latest_snapshot_text}</div>
        </div>
        <div class="sidebar-block">
            <div class="sidebar-kicker">Pipeline</div>
            <div class="sidebar-value {status_class}">{system_snapshot['status']}</div>
        </div>
        <div class="sidebar-block">
            <div class="sidebar-kicker">Warehouse</div>
            <div class="sidebar-value">{system_snapshot['latest_repo_count']:,} tracked repos</div>
            <div class="sidebar-value">{system_snapshot['latest_stats_rows']:,} stats rows</div>
            <div class="sidebar-value">{system_snapshot['tracked_days']:,} tracked days</div>
        </div>
        <div class="sidebar-block">
            <div class="sidebar-kicker">Source</div>
            <div class="sidebar-value">GitHub REST API</div>
            <div class="sidebar-value">Supabase PostgreSQL</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


if page == "Overview":
    try:
        df = load_leaderboard()
        trends_df = load_trends()
        anomalies_result = load_anomalies()

        if df.empty:
            st.error("No leaderboard data found. Run the pipeline first.")
            st.stop()

        anomaly_count = 0 if isinstance(anomalies_result, pd.DataFrame) else len(anomalies_result[0])
        render_shell_header(
            "Overview",
            "A live intelligence layer for AI and ML repositories. Designed to feel like an engineering control room, not a static report.",
            system_snapshot,
            len(df),
            anomaly_count,
        )

        latest_growth = trends_df.sort_values(["full_name", "snapshot_date"]).copy()
        latest_growth["star_growth"] = latest_growth.groupby("full_name")["stars"].diff()
        latest_growth = latest_growth.dropna(subset=["star_growth"])
        fastest_repo = (
            latest_growth.groupby("full_name").last().reset_index().sort_values("star_growth", ascending=False).head(1)
            if not latest_growth.empty
            else pd.DataFrame()
        )

        meta_cols = st.columns(4)
        metrics = [
            ("Tracked repositories", f"{len(df):,}", "Current scored repo universe"),
            ("Total stars", f"{df['stars'].sum():,.0f}", "Aggregate popularity across the graph"),
            ("Peak impact", f"{df['impact_score'].max():.4f}", "Highest impact score in the latest snapshot"),
            (
                "Fastest mover",
                fastest_repo.iloc[0]["name"] if not fastest_repo.empty else "Building history",
                "Top star-growth repo in the latest interval",
            ),
        ]
        for col, (label, value, meta) in zip(meta_cols, metrics):
            with col:
                st.markdown(
                    f"""
                    <div class="panel">
                        <div class="panel-label">{label}</div>
                        <div class="panel-value">{value}</div>
                        <div class="panel-meta">{meta}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        render_section_header("System pulse")
        pulse_left, pulse_mid, pulse_right, pulse_far = st.columns([1.2, 1, 1, 1])
        score_sync_gap = abs(system_snapshot["latest_stats_rows"] - system_snapshot["latest_score_rows"])
        with pulse_left:
            st.markdown(
                f"""
                <div class="panel">
                    <div class="panel-label">Latest run telemetry</div>
                    <div class="panel-value">{system_snapshot['latest_stats_rows']:,}</div>
                    <div class="panel-meta">Stats rows written in the latest snapshot. Scores rows: {system_snapshot['latest_score_rows']:,}. This gives the interface a live operational backbone.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with pulse_mid:
            st.markdown(
                f"""
                <div class="panel">
                    <div class="panel-label">Coverage</div>
                    <div class="panel-value">{system_snapshot['languages_covered']:,}</div>
                    <div class="panel-meta">Distinct languages represented across the tracked graph.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with pulse_right:
            st.markdown(
                f"""
                <div class="panel">
                    <div class="panel-label">History depth</div>
                    <div class="panel-value">{system_snapshot['tracked_days']:,}</div>
                    <div class="panel-meta">Distinct snapshot days available for trend and anomaly analysis.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with pulse_far:
            st.markdown(
                f"""
                <div class="panel">
                    <div class="panel-label">Sync integrity</div>
                    <div class="panel-value">{score_sync_gap}</div>
                    <div class="panel-meta">Difference between latest stats and latest score rows. Lower is better.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        render_section_header("Priority repositories")
        left, right = st.columns([1.2, 1], gap="large")
        with left:
            top5 = df.head(5)
            for rank, (_, row) in enumerate(top5.iterrows(), start=1):
                render_repo_card(rank, row)

        with right:
            lang_df = df.groupby("language")["stars"].sum().sort_values(ascending=True).tail(8).reset_index()
            fig = go.Figure(
                go.Bar(
                    x=lang_df["stars"],
                    y=lang_df["language"],
                    orientation="h",
                    marker=dict(color=lang_df["stars"], colorscale=[[0, "#0e3b2c"], [0.5, "#1ec7c1"], [1, "#4f8cff"]], showscale=False),
                    text=[f"{value:,.0f}" for value in lang_df["stars"]],
                    textposition="outside",
                )
            )
            fig.update_layout(**CHART_THEME, height=340, title="Stars by language")
            st.plotly_chart(fig, use_container_width=True)

            topic_series = df["topics"].dropna().str.split(", ").explode()
            topic_counts = topic_series.value_counts().head(8).reset_index()
            topic_counts.columns = ["topic", "count"]
            fig2 = px.bar(
                topic_counts,
                x="count",
                y="topic",
                orientation="h",
                color="count",
                color_continuous_scale=["#0e3b2c", "#49d17d", "#4f8cff"],
            )
            fig2.update_layout(**CHART_THEME, height=320, title="Topic footprint")
            fig2.update_traces(textposition="outside")
            fig2.update_coloraxes(showscale=False)
            st.plotly_chart(fig2, use_container_width=True)

        render_section_header("Hidden gems")
        gems = find_hidden_gems()
        if gems.empty:
            st.info("Hidden gem scoring needs a populated repository snapshot.")
        else:
            gem_cols = st.columns(3)
            for idx, (_, row) in enumerate(gems.head(6).iterrows(), start=1):
                with gem_cols[(idx - 1) % 3]:
                    st.markdown(
                        f"""
                        <div class="repo-card gem-card">
                            <div class="repo-kicker">
                                <div class="repo-rank">Gem {idx:02d} | {row['language'] or 'Unknown'}</div>
                                <div class="score-pill">{(row['forks'] / (row['stars'] + 1)):.4f}</div>
                            </div>
                            <div class="repo-name">{row['name']}</div>
                            <div class="repo-meta">Stars {row['stars']:,} | Forks {row['forks']:,} | Issues {row['open_issues']:,}</div>
                            <div class="repo-meta">{row['topics'][:68] if row['topics'] else 'Emergent candidate with high momentum.'}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    except Exception as exc:
        logger.exception("Overview page failed to load.")
        st.error(f"Error loading data: {exc}")


elif page == "Leaderboard":
    try:
        df = load_leaderboard()
        render_shell_header(
            "Leaderboard",
            "Composite ranking across the tracked graph. Built for quick scanning, filter-driven exploration, and signal decomposition.",
            system_snapshot,
            len(df),
            0,
        )

        col1, col2 = st.columns([1, 2])
        with col1:
            languages = ["All"] + sorted(df["language"].dropna().unique().tolist())
            selected_lang = st.selectbox("Language filter", languages)
        with col2:
            all_topics = sorted(set(t.strip() for topics in df["topics"].dropna() for t in topics.split(",")))
            selected_topics = st.multiselect("Topic filter", all_topics)

        filtered = df.copy()
        if selected_lang != "All":
            filtered = filtered[filtered["language"] == selected_lang]
        if selected_topics:
            filtered = filtered[filtered["topics"].apply(lambda topics: any(topic in (topics or "") for topic in selected_topics))]

        filtered = filtered.reset_index(drop=True)
        filtered.index += 1
        filtered["Star Score"] = (filtered["star_velocity"] * 0.50).round(4)
        filtered["Fork Score"] = (filtered["fork_score"] * 0.30).round(4)
        filtered["Issue Score"] = (filtered["issue_score"] * 0.20).round(4)

        render_section_header("Filter telemetry")
        info_cols = st.columns(3)
        info_values = [
            ("Visible repos", f"{len(filtered):,}", "Repositories after active filters"),
            ("Avg impact", f"{filtered['impact_score'].mean():.4f}" if not filtered.empty else "0.0000", "Mean impact score in current view"),
            ("Highest star count", f"{filtered['stars'].max():,}" if not filtered.empty else "0", "Top raw star count in filtered selection"),
        ]
        for col, (label, value, meta) in zip(info_cols, info_values):
            with col:
                st.markdown(
                    f"""
                    <div class="panel">
                        <div class="panel-label">{label}</div>
                        <div class="panel-value">{value}</div>
                        <div class="panel-meta">{meta}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        display_df = filtered[
            ["name", "language", "stars", "forks", "open_issues", "Star Score", "Fork Score", "Issue Score", "impact_score"]
        ].rename(
            columns={
                "name": "Repository",
                "language": "Language",
                "stars": "Stars",
                "forks": "Forks",
                "open_issues": "Issues",
                "impact_score": "Impact Score",
            }
        )

        render_section_header("Ranked signal board")
        st.dataframe(
            display_df.style.background_gradient(subset=["Impact Score"], cmap="Blues").format(
                {"Impact Score": "{:.4f}", "Stars": "{:,}", "Forks": "{:,}", "Issues": "{:,}"}
            ),
            use_container_width=True,
            height=640,
        )

    except Exception as exc:
        logger.exception("Leaderboard page failed to load.")
        st.error(f"Error loading data: {exc}")


elif page == "Trends":
    try:
        df = load_trends()
        df = df.sort_values(["full_name", "snapshot_date"])
        df["star_growth"] = df.groupby("full_name")["stars"].diff()
        trend_df = df.dropna(subset=["star_growth"])

        anomalies_preview = load_anomalies()
        anomaly_count = 0 if isinstance(anomalies_preview, pd.DataFrame) else len(anomalies_preview[0])
        render_shell_header(
            "Trends",
            "Observe acceleration, compare repository trajectories, and track momentum like an engineering performance feed.",
            system_snapshot,
            df["full_name"].nunique(),
            anomaly_count,
        )

        if trend_df.empty:
            st.info("Only one snapshot is available. Growth analytics will appear after the next daily run.")
            snapshot = df.groupby("name").last().reset_index().sort_values("stars", ascending=False).head(15)
            fig = px.bar(
                snapshot,
                x="stars",
                y="name",
                orientation="h",
                color="stars",
                color_continuous_scale=["#0e3b2c", "#49d17d", "#4f8cff"],
            )
            fig.update_layout(**CHART_THEME, height=520, title="Current snapshot by star count")
            fig.update_coloraxes(showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            latest = trend_df.groupby("full_name").last().reset_index()
            fastest = latest.sort_values("star_growth", ascending=False).head(10)

            stat_cols = st.columns(3)
            trend_metrics = [
                ("Fastest daily mover", fastest.iloc[0]["name"], "Highest star growth in the latest interval"),
                ("Peak daily growth", f"+{fastest['star_growth'].max():,.0f}", "Largest detected delta across tracked repos"),
                ("Repos with history", f"{trend_df['full_name'].nunique():,}", "Repositories with at least two snapshots"),
            ]
            for col, (label, value, meta) in zip(stat_cols, trend_metrics):
                with col:
                    st.markdown(
                        f"""
                        <div class="panel">
                            <div class="panel-label">{label}</div>
                            <div class="panel-value">{value}</div>
                            <div class="panel-meta">{meta}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            render_section_header("Fastest growing now")
            fig = go.Figure(
                go.Bar(
                    x=fastest["star_growth"],
                    y=fastest["name"],
                    orientation="h",
                    marker=dict(color=fastest["star_growth"], colorscale=[[0, "#0f264f"], [0.5, "#1ec7c1"], [1, "#49d17d"]], showscale=False),
                    text=[f"+{value:,.0f}" for value in fastest["star_growth"]],
                    textposition="outside",
                )
            )
            fig.update_layout(**CHART_THEME, height=390, title="Latest star-growth leaders")
            st.plotly_chart(fig, use_container_width=True)

            render_section_header("Multi-repo comparison")
            top_repos = df.groupby("name")["stars"].max().sort_values(ascending=False).head(10).index.tolist()
            selected = st.multiselect("Select repositories to compare", options=top_repos, default=top_repos[:5])
            if selected:
                chart_df = df[df["name"].isin(selected)]
                fig2 = px.line(
                    chart_df,
                    x="snapshot_date",
                    y="stars",
                    color="name",
                    color_discrete_sequence=["#4f8cff", "#1ec7c1", "#49d17d", "#78e08f", "#86b5ff", "#1a7f63"],
                )
                fig2.update_traces(line=dict(width=2.5))
                fig2.update_layout(
                    **CHART_THEME,
                    height=460,
                    title="Star accumulation over time",
                    legend=dict(
                        bgcolor="rgba(9, 15, 27, 0.86)",
                        bordercolor="rgba(89, 122, 173, 0.16)",
                        borderwidth=1,
                    ),
                )
                st.plotly_chart(fig2, use_container_width=True)

    except Exception as exc:
        logger.exception("Trends page failed to load.")
        st.error(f"Error loading data: {exc}")


elif page == "Anomalies":
    try:
        result = load_anomalies()
        anomaly_count = 0 if isinstance(result, pd.DataFrame) else len(result[0])
        render_shell_header(
            "Anomalies",
            "Flag unusual growth patterns before they become obvious. This view focuses attention on statistical outliers, not just popular repos.",
            system_snapshot,
            system_snapshot["latest_repo_count"],
            anomaly_count,
        )

        if isinstance(result, pd.DataFrame) and result.empty:
            st.info("Need at least two snapshots before anomaly detection becomes meaningful.")
        else:
            anomalies, threshold = result
            overview_cols = st.columns(3)
            anomaly_metrics = [
                ("Flagged repositories", f"{len(anomalies):,}", "Current outliers above the active threshold"),
                ("Threshold", f"+{threshold:.0f}", "Stars per interval required to trip the detector"),
                ("Detection model", "2 sigma", "Mean plus two standard deviations"),
            ]
            for col, (label, value, meta) in zip(overview_cols, anomaly_metrics):
                with col:
                    st.markdown(
                        f"""
                        <div class="panel">
                            <div class="panel-label">{label}</div>
                            <div class="panel-value">{value}</div>
                            <div class="panel-meta">{meta}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            render_section_header("Flagged growth events")
            if anomalies.empty:
                st.success("No repositories are breaching the anomaly threshold in the latest interval.")
            else:
                for _, row in anomalies.iterrows():
                    st.markdown(
                        f"""
                        <div class="anomaly-card">
                            <div class="repo-kicker">
                                <div class="repo-rank">Outlier | {row['language'] or 'Unknown'}</div>
                                <div class="anomaly-growth">+{row['star_growth']:,.0f}</div>
                            </div>
                            <div class="anomaly-name">{row['name']}</div>
                            <div class="repo-meta">Total stars {row['stars']:,.0f} | Latest growth spike above threshold {threshold:.0f}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                trends_df = load_trends()
                trends_df["star_growth"] = trends_df.groupby("full_name")["stars"].diff()
                latest_all = (
                    trends_df.dropna(subset=["star_growth"])
                    .groupby("name")
                    .last()
                    .reset_index()
                    .sort_values("star_growth", ascending=False)
                    .head(20)
                )

                render_section_header("Threshold comparison")
                fig = go.Figure()
                normal = latest_all[latest_all["star_growth"] <= threshold]
                flagged = latest_all[latest_all["star_growth"] > threshold]
                fig.add_trace(go.Bar(x=normal["name"], y=normal["star_growth"], name="Normal", marker_color="rgba(77, 163, 255, 0.38)"))
                fig.add_trace(go.Bar(x=flagged["name"], y=flagged["star_growth"], name="Flagged", marker_color="#ff5d73"))
                fig.add_hline(
                    y=threshold,
                    line_dash="dash",
                    line_color="#f3c969",
                    line_width=1.5,
                    annotation_text=f"Threshold {threshold:.0f}",
                    annotation_font=dict(color="#f3c969", family="IBM Plex Mono", size=10),
                )
                fig.update_layout(
                    **CHART_THEME,
                    height=410,
                    title="Latest growth versus anomaly threshold",
                    barmode="overlay",
                    legend=dict(
                        bgcolor="rgba(9, 15, 27, 0.86)",
                        bordercolor="rgba(89, 122, 173, 0.16)",
                        borderwidth=1,
                    ),
                )
                st.plotly_chart(fig, use_container_width=True)

    except Exception as exc:
        logger.exception("Anomalies page failed to load.")
        st.error(f"Error loading data: {exc}")


st.markdown(
    """
    <div class="footer-note">
        Built by Varun Lal | <a href="https://github.com/varunNeon">GitHub</a> | <a href="https://www.linkedin.com/in/varunnlal/">LinkedIn</a> | GitPulse command center
    </div>
    """,
    unsafe_allow_html=True,
)
