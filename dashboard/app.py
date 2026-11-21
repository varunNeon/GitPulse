import html
import os
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.impact_score import find_hidden_gems
from common.logging_config import get_logger
from ingestion.fetch_repos import TOPICS
from warehouse.db import get_engine


logger = get_logger(__name__)

st.set_page_config(
    page_title="GitPulse",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

GREEN = "#49d17d"
CYAN = "#1ec7c1"
BLUE = "#4f8cff"
AMBER = "#f3c969"
RED = "#ff6a7f"
MUTED = "#8aa39b"
TEXT = "#edf8f3"
LINE_PALETTE = [GREEN, BLUE, AMBER, RED, "#b38cff", CYAN, "#ff9f5a", "#9ad0ff"]


st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');
:root{--border:rgba(58,120,96,.24);--border-strong:rgba(73,209,125,.42);--text:#edf8f3;--muted:#8aa39b;--blue:#4f8cff;--cyan:#1ec7c1;--green:#49d17d;--red:#ff6a7f;--amber:#f3c969;--card:linear-gradient(180deg,rgba(5,14,18,.94),rgba(6,11,20,.98));}
html,body,[class*="css"]{font-family:'Space Grotesk',sans-serif;}
[data-testid="stAppViewContainer"]{background:radial-gradient(circle at top left,rgba(30,199,193,.08),transparent 26%),radial-gradient(circle at top right,rgba(79,140,255,.1),transparent 28%),linear-gradient(180deg,#010202 0%,#030507 38%,#071018 100%);}
[data-testid="stHeader"]{background:transparent;}
#MainMenu,footer{visibility:hidden;}
.block-container{max-width:1480px;padding:1.6rem 2rem 2rem 2rem;}
hr{border-color:rgba(89,122,173,.16)!important;}

/* nav */
[data-testid="stRadio"] [role="radiogroup"]{gap:.35rem;}
[data-testid="stRadio"] label[data-baseweb="radio"]{width:100%;margin:0;padding:.55rem .75rem;border-radius:12px;border:1px solid transparent;transition:background .15s ease,border-color .15s ease;}
[data-testid="stRadio"] label[data-baseweb="radio"]:hover{background:rgba(9,20,29,.9);border-color:var(--border);}
[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked){background:rgba(73,209,125,.08);border-color:var(--border-strong);}
[data-testid="stRadio"] label[data-baseweb="radio"] p{font-size:.92rem;}

[data-baseweb="tag"],[data-testid="stMultiSelectTagsContainer"] [data-tag]{background:rgba(73,209,125,.14)!important;border:1px solid rgba(73,209,125,.35);color:#bff3d2!important;}
[data-baseweb="tag"] *,[data-testid="stMultiSelectTagsContainer"] [data-tag] *{color:#bff3d2!important;fill:#bff3d2!important;}

/* shared */
.mono{font-family:'IBM Plex Mono',monospace;}
.kicker{font-family:'IBM Plex Mono',monospace;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);font-size:.62rem;}
.panel,.repo-card,.anomaly-card,.rail-block,.hero{background:var(--card);border:1px solid var(--border);border-radius:18px;}

/* rail */
.rail-title{font-size:1.6rem;line-height:1;font-weight:700;color:var(--text);}
.rail-title span{color:var(--green);}
.rail-sub{margin:.4rem 0 1.1rem 0;}
.rail-block{padding:.9rem 1rem;margin-top:1rem;}
.rail-row{display:flex;flex-wrap:wrap;justify-content:space-between;gap:0 .5rem;font-size:.8rem;color:var(--muted);padding:.28rem 0;}
.rail-row b{color:var(--text);font-weight:500;white-space:nowrap;}
.status{display:flex;align-items:center;gap:.5rem;font-size:.92rem;font-weight:500;margin:.35rem 0 .5rem 0;}
.dot{width:8px;height:8px;border-radius:50%;background:var(--green);box-shadow:0 0 10px rgba(73,209,125,.7);}
.status.warn{color:var(--amber);} .status.warn .dot{background:var(--amber);box-shadow:0 0 10px rgba(243,201,105,.6);}
.status.good{color:var(--green);}

/* hero */
.hero{position:relative;overflow:hidden;border-radius:24px;padding:1.4rem 1.5rem;margin-bottom:1.2rem;}
.hero::before{content:"";position:absolute;inset:0;background-image:linear-gradient(rgba(30,199,193,.04) 1px,transparent 1px),linear-gradient(90deg,rgba(79,140,255,.04) 1px,transparent 1px);background-size:28px 28px;opacity:.3;pointer-events:none;}
.hero > *{position:relative;}
.hero .kicker{color:var(--green);font-size:.7rem;}
.hero h1{font-size:clamp(2rem,3.6vw,3rem);line-height:1.05;font-weight:700;color:var(--text);margin:.45rem 0 0 0;padding:0;}
.hero h1 span{color:var(--cyan);}
.hero-copy{margin-top:.6rem;max-width:68ch;color:var(--muted);font-size:.96rem;line-height:1.55;}
.badges{display:flex;flex-wrap:wrap;gap:.5rem;margin-top:1rem;}
.badge{padding:.4rem .7rem;border-radius:999px;font-family:'IBM Plex Mono',monospace;letter-spacing:.1em;text-transform:uppercase;font-size:.62rem;border:1px solid var(--border);background:rgba(8,20,17,.8);color:var(--text);}

/* panels */
.panel-grid{display:grid;gap:1rem;margin-bottom:.4rem;}
.panel{padding:1rem 1.05rem;min-width:0;}
.panel-value{font-family:'IBM Plex Mono',monospace;font-size:1.6rem;color:var(--text);font-weight:600;margin:.4rem 0 .2rem 0;}
.panel-value.is-text{font-size:1.15rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;padding:.22rem 0;}
.panel-meta{color:var(--muted);font-size:.8rem;line-height:1.5;}
.section-header{display:flex;align-items:center;gap:.6rem;color:var(--green);font-family:'IBM Plex Mono',monospace;letter-spacing:.16em;text-transform:uppercase;font-size:.72rem;margin:1.6rem 0 .8rem 0;}
.section-header::before{content:"";width:30px;height:1px;background:linear-gradient(90deg,var(--green),transparent);}

/* repo cards */
.card-stack{display:grid;gap:.75rem;}
.card-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.85rem;}
.repo-card,.anomaly-card{display:flex;flex-direction:column;gap:.45rem;padding:.95rem 1.05rem;height:100%;box-sizing:border-box;transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease;}
.repo-card:hover,.anomaly-card:hover{transform:translateY(-2px);border-color:var(--border-strong);box-shadow:0 18px 36px rgba(1,6,8,.3);}
.repo-top{display:flex;justify-content:space-between;align-items:center;gap:.75rem;}
.repo-rank{min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-family:'IBM Plex Mono',monospace;font-size:.66rem;color:var(--cyan);letter-spacing:.14em;text-transform:uppercase;}
.gem-card .repo-rank{color:var(--green);}
.score-pill{padding:.25rem .6rem;border-radius:999px;background:rgba(79,140,255,.12);border:1px solid rgba(79,140,255,.24);color:#9cc1ff;font-family:'IBM Plex Mono',monospace;font-size:.72rem;font-weight:600;white-space:nowrap;}
.repo-mid{display:flex;justify-content:space-between;align-items:flex-end;gap:.75rem;}
.repo-name{font-size:1.05rem;font-weight:700;color:var(--text)!important;text-decoration:none!important;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.repo-name:hover{color:var(--cyan)!important;}
.repo-stats{display:flex;flex-wrap:wrap;gap:.2rem .9rem;font-family:'IBM Plex Mono',monospace;font-size:.76rem;color:var(--muted);}
.repo-stats span{white-space:nowrap;}
.repo-stats b{color:var(--text);font-weight:500;}
.chips{display:flex;flex-wrap:wrap;gap:.35rem;margin-top:auto;padding-top:.15rem;}
.chip{font-size:.68rem;padding:.15rem .5rem;border-radius:999px;background:rgba(30,199,193,.08);border:1px solid rgba(30,199,193,.18);color:#9fe3df;}
.spark{flex-shrink:0;}
.anomaly-card{border-color:rgba(255,106,127,.3);}
.anomaly-growth{font-family:'IBM Plex Mono',monospace;color:var(--red);font-weight:600;}

.footer-note{text-align:center;font-family:'IBM Plex Mono',monospace;font-size:.72rem;color:var(--muted);padding:1.6rem 0 .5rem 0;}
.footer-note a{color:var(--cyan);text-decoration:none;}
@media (max-width:1100px){.card-grid{grid-template-columns:repeat(2,minmax(0,1fr));}.panel-grid{grid-template-columns:repeat(2,minmax(0,1fr))!important;}}
@media (max-width:900px){.spark{display:none;}}
@media (max-width:700px){.card-grid{grid-template-columns:1fr;}.panel-grid{grid-template-columns:1fr 1fr!important;}}
</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------- data


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
        df = pd.read_sql(
            text(
                """
                SELECT r.name, r.full_name, r.language, r.html_url, s.snapshot_date, s.stars, s.forks, s.open_issues
                FROM dim_repos r
                JOIN fact_repo_stats s ON r.repo_id = s.repo_id
                ORDER BY r.full_name, s.snapshot_date ASC
                """
            ),
            conn,
        )
    df["star_growth"] = df.groupby("full_name")["stars"].diff()
    return df


@st.cache_data(ttl=3600)
def load_latest_growth():
    """Latest star growth per repo (needs at least two snapshots)."""
    df = load_trends().dropna(subset=["star_growth"])
    if df.empty:
        return pd.DataFrame()
    return df.groupby("full_name").last().reset_index().sort_values("star_growth", ascending=False)


@st.cache_data(ttl=3600)
def load_anomalies():
    """Returns (anomalies_df, threshold). threshold is None without enough history."""
    latest = load_latest_growth()
    if latest.empty:
        return pd.DataFrame(), None
    threshold = latest["star_growth"].mean() + 2 * latest["star_growth"].std()
    return latest[latest["star_growth"] > threshold], threshold


@st.cache_data(ttl=3600)
def load_hidden_gems():
    return find_hidden_gems()


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
                SELECT COUNT(DISTINCT s.snapshot_date) AS tracked_days,
                       COUNT(DISTINCT r.language) AS languages_covered
                FROM fact_repo_stats s
                JOIN dim_repos r ON r.repo_id = s.repo_id
                """
            )
        ).mappings().one()
    latest_snapshot = stats_result["latest_snapshot"]
    score_snapshot = scores_result["latest_score_snapshot"]
    healthy = bool(latest_snapshot) and latest_snapshot == score_snapshot
    return {
        "latest_snapshot": latest_snapshot,
        "latest_stats_rows": stats_result["latest_stats_rows"] or 0,
        "latest_repo_count": stats_result["latest_repo_count"] or 0,
        "latest_score_rows": scores_result["latest_score_rows"] or 0,
        "tracked_days": history_result["tracked_days"] or 0,
        "languages_covered": history_result["languages_covered"] or 0,
        "healthy": healthy,
    }


# ---------------------------------------------------------------- helpers


def render_html(markup: str):
    """Render HTML without blank or indented lines, which markdown would turn into code blocks."""
    st.markdown("\n".join(line.strip() for line in markup.splitlines() if line.strip()), unsafe_allow_html=True)


def esc(value) -> str:
    return html.escape(str(value)) if value is not None else ""


def compact(value) -> str:
    value = float(value)
    sign = "-" if value < 0 else ""
    value = abs(value)
    if value >= 1_000_000:
        out = f"{value / 1_000_000:.1f}M"
    elif value >= 10_000:
        out = f"{value / 1_000:.0f}k"
    elif value >= 1_000:
        out = f"{value / 1_000:.1f}k"
    else:
        out = f"{value:.0f}"
    return sign + out.replace(".0M", "M").replace(".0k", "k")


def split_topics(topics) -> list:
    if not topics or not isinstance(topics, str):
        return []
    return [topic.strip() for topic in topics.split(",") if topic.strip()]


def sparkline_svg(values, color=GREEN, width=110, height=30) -> str:
    values = [float(v) for v in values if pd.notna(v)]
    if len(values) < 2:
        return ""
    low, high = min(values), max(values)
    span = (high - low) or 1
    step = width / (len(values) - 1)
    points = [(i * step, height - 2 - (v - low) / span * (height - 4)) for i, v in enumerate(values)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    area = f"0,{height} {line} {width},{height}"
    return (
        f'<svg class="spark" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        f'<polygon points="{area}" fill="{color}" fill-opacity="0.12"/>'
        f'<polyline points="{line}" fill="none" stroke="{color}" stroke-width="1.6" stroke-linejoin="round"/>'
        "</svg>"
    )


def render_section_header(title: str):
    render_html(f'<div class="section-header">{esc(title)}</div>')


def render_panels(items):
    """items: list of (label, value, meta). Text values get a smaller, truncating style."""
    cells = []
    for label, value, meta in items:
        value_text = str(value)
        is_text = not any(ch.isdigit() for ch in value_text[:2])
        cls = "panel-value is-text" if is_text else "panel-value"
        cells.append(
            f'<div class="panel"><div class="kicker">{esc(label)}</div>'
            f'<div class="{cls}" title="{esc(value_text)}">{esc(value_text)}</div>'
            f'<div class="panel-meta">{esc(meta)}</div></div>'
        )
    render_html(f'<div class="panel-grid" style="grid-template-columns:repeat({len(items)},minmax(0,1fr))">{"".join(cells)}</div>')


def repo_card(kicker: str, pill: str, row, spark_values=None, extra_class: str = "") -> str:
    url = row.get("html_url") or f"https://github.com/{row.get('full_name', '')}"
    chips = "".join(f'<span class="chip">{esc(t)}</span>' for t in split_topics(row.get("topics"))[:4])
    spark = sparkline_svg(spark_values) if spark_values is not None else ""
    return (
        f'<div class="repo-card {extra_class}">'
        f'<div class="repo-top"><div class="repo-rank">{esc(kicker)}</div><div class="score-pill">{esc(pill)}</div></div>'
        f'<div class="repo-mid"><div style="min-width:0">'
        f'<a class="repo-name" href="{esc(url)}" target="_blank" rel="noopener">{esc(row["name"])}</a>'
        f'<div class="repo-stats"><span><b>{compact(row["stars"])}</b> stars</span>'
        f'<span><b>{compact(row["forks"])}</b> forks</span><span><b>{compact(row["open_issues"])}</b> issues</span></div>'
        f"</div>{spark}</div>"
        f'<div class="chips">{chips}</div>'
        "</div>"
    )


def render_hero(title: str, copy: str):
    render_html(
        f"""
        <div class="hero">
            <div class="kicker">GitPulse · AI repository telemetry</div>
            <h1>{esc(title)}</h1>
            <div class="hero-copy">{esc(copy)}</div>
            <div class="badges">
                <div class="badge">Snapshot {esc(snapshot_text)}</div>
                <div class="badge">{tracked_repo_count:,} repos</div>
                <div class="badge">{len(TOPICS)} search topics</div>
                <div class="badge">{anomaly_count} anomalies</div>
            </div>
        </div>
        """
    )


def style_fig(fig, height: int, title: str | None = None):
    fig.update_layout(
        height=height,
        title=dict(text=title, font=dict(color=TEXT, family="Space Grotesk", size=16), x=0, xanchor="left") if title else None,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(5,12,16,0.6)",
        font=dict(family="IBM Plex Mono", color=MUTED, size=11),
        margin=dict(l=10, r=30, t=50 if title else 20, b=10),
        hoverlabel=dict(bgcolor="#071018", bordercolor="rgba(73,209,125,0.4)", font=dict(family="IBM Plex Mono", color=TEXT)),
        legend=dict(
            title=None,
            font=dict(color=MUTED, family="IBM Plex Mono"),
            bgcolor="rgba(0,0,0,0)",
            orientation="h",
            yanchor="bottom",
            y=1.02,
            x=0,
        ),
        bargap=0.35,
    )
    axis = dict(title=None, gridcolor="rgba(58,120,96,0.14)", linecolor="rgba(58,120,96,0.16)", zeroline=False)
    fig.update_xaxes(**axis)
    fig.update_yaxes(**axis)
    return fig


def hbar(labels, values, text, color, hover, x_suffix=""):
    """Horizontal bar with room on the right so outside labels never clip."""
    fig = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker=dict(color=color, line=dict(width=0)),
            text=text,
            textposition="outside",
            textfont=dict(color=TEXT, size=11),
            cliponaxis=False,
            hovertemplate=hover,
        )
    )
    # Every bar carries its own value label, so the x axis would only repeat it.
    fig.update_xaxes(range=[0, max(values) * 1.35 if len(values) else 1], ticksuffix=x_suffix, showticklabels=False, showgrid=False)
    return fig


def show_chart(fig):
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


# ---------------------------------------------------------------- shared state

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
        "healthy": False,
    }

try:
    leaderboard_df = load_leaderboard()
except Exception:
    logger.exception("Failed to load leaderboard.")
    leaderboard_df = pd.DataFrame()

try:
    anomalies_df, anomaly_threshold = load_anomalies()
except Exception:
    logger.exception("Failed to load anomalies.")
    anomalies_df, anomaly_threshold = pd.DataFrame(), None

latest_snapshot = system_snapshot["latest_snapshot"]
snapshot_text = latest_snapshot.strftime("%d %b %Y") if latest_snapshot else "none yet"
tracked_repo_count = len(leaderboard_df)
anomaly_count = len(anomalies_df)

rail_col, main_col = st.columns([0.2, 0.8], gap="large")

with rail_col:
    render_html(
        """
        <div class="rail-title">Git<span>Pulse</span></div>
        <div class="kicker rail-sub">AI ecosystem telemetry</div>
        """
    )
    page = st.radio("Navigate", ["Overview", "Leaderboard", "Trends", "Anomalies"], label_visibility="collapsed")
    status_cls = "good" if system_snapshot["healthy"] else "warn"
    status_text = "Pipeline healthy" if system_snapshot["healthy"] else "Needs review"
    render_html(
        f"""
        <div class="rail-block">
            <div class="kicker">Pipeline</div>
            <div class="status {status_cls}"><span class="dot"></span>{status_text}</div>
            <div class="rail-row">Last run <b>{esc(snapshot_text)}</b></div>
            <div class="rail-row">Refreshed <b>{system_snapshot['latest_repo_count']:,} / {tracked_repo_count:,}</b></div>
            <div class="rail-row">Scores written <b>{system_snapshot['latest_score_rows']:,}</b></div>
            <div class="rail-row">History <b>{system_snapshot['tracked_days']:,} days</b></div>
            <div class="rail-row">Languages <b>{system_snapshot['languages_covered']:,}</b></div>
        </div>
        <div class="rail-block">
            <div class="kicker">Source</div>
            <div class="rail-row">GitHub REST API</div>
            <div class="rail-row">Supabase PostgreSQL</div>
        </div>
        """
    )

with main_col:

    if page == "Overview":
        try:
            df = leaderboard_df
            if df.empty:
                st.error("No leaderboard data found. Run the pipeline first.")
                st.stop()
            trends_df = load_trends()
            latest_growth = load_latest_growth()

            render_hero(
                "Overview",
                "Daily scores for the most active AI and ML repositories on GitHub, ranked by star velocity, fork activity and issue load.",
            )

            top = df.iloc[0]
            if latest_growth.empty:
                mover = ("Fastest mover", "Building history", "Needs a second daily snapshot")
            else:
                fastest = latest_growth.iloc[0]
                mover = ("Fastest mover", fastest["name"], f"+{fastest['star_growth']:,.0f} stars in the latest run")
            render_panels(
                [
                    ("Tracked repositories", f"{len(df):,}", f"Found across {len(TOPICS)} GitHub topics"),
                    ("Total stars", compact(df["stars"].sum()), f"{df['stars'].sum():,.0f} across all tracked repos"),
                    ("Top impact", top["name"], f"Impact score {top['impact_score']:.4f}"),
                    mover,
                ]
            )

            render_section_header("Priority repositories")
            left, right = st.columns([1.15, 1], gap="large")
            with left:
                cards = []
                for rank, (_, row) in enumerate(df.head(5).iterrows(), start=1):
                    history = trends_df.loc[trends_df["full_name"] == row["full_name"], "stars"].tail(30)
                    cards.append(
                        repo_card(f"#{rank:02d} · {row['language'] or 'Unknown'}", f"{row['impact_score']:.4f}", row, history)
                    )
                render_html(f'<div class="card-stack">{"".join(cards)}</div>')

            with right:
                lang_df = df.assign(language=df["language"].fillna("Unknown")).groupby("language")["stars"].sum()
                share = (lang_df / lang_df.sum() * 100).sort_values().tail(8)
                colors = [GREEN if lang == share.idxmax() else "rgba(30,199,193,0.55)" for lang in share.index]
                fig = hbar(
                    share.index,
                    share.values,
                    [f"{pct:.0f}%" for pct in share.values],
                    colors,
                    [f"{lang}: {pct:.1f}% of stars ({compact(lang_df[lang])})<extra></extra>" for lang, pct in share.items()],
                    x_suffix="%",
                )
                show_chart(style_fig(fig, 330, "Share of stars by language"))

                topic_counts = pd.Series([t for topics in df["topics"] for t in split_topics(topics)]).value_counts().head(8).sort_values()
                fig2 = hbar(
                    topic_counts.index,
                    topic_counts.values,
                    [str(v) for v in topic_counts.values],
                    "rgba(79,140,255,0.7)",
                    "%{y}: %{x} repos<extra></extra>",
                )
                show_chart(style_fig(fig2, 320, "Most common topics"))

            render_section_header("Hidden gems")
            st.caption("Below-median star counts but an above-average fork-to-star ratio: repos people build on before they get famous.")
            gems = load_hidden_gems()
            if gems.empty:
                st.info("Hidden gem scoring needs a populated repository snapshot.")
            else:
                gem_cards = [
                    repo_card(f"Gem {i:02d} · {row['language'] or 'Unknown'}", f"fork ratio {row['fork_ratio']:.2f}", row, extra_class="gem-card")
                    for i, (_, row) in enumerate(gems.head(6).iterrows(), start=1)
                ]
                render_html(f'<div class="card-grid">{"".join(gem_cards)}</div>')

        except Exception as exc:
            logger.exception("Overview page failed to load.")
            st.error(f"Error loading data: {exc}")

    elif page == "Leaderboard":
        try:
            df = leaderboard_df.copy()
            render_hero(
                "Leaderboard",
                "Every tracked repository ranked by impact score: 50% star velocity, 30% forks, 20% issue activity. Click a name to open it on GitHub.",
            )

            df["language"] = df["language"].fillna("Unknown")
            col1, col2 = st.columns([1, 2])
            with col1:
                selected_lang = st.selectbox("Language", ["All"] + sorted(df["language"].unique().tolist()))
            with col2:
                all_topics = sorted({t for topics in df["topics"] for t in split_topics(topics)})
                selected_topics = st.multiselect("Topics", all_topics, placeholder="Any topic")

            filtered = df
            if selected_lang != "All":
                filtered = filtered[filtered["language"] == selected_lang]
            if selected_topics:
                wanted = set(selected_topics)
                filtered = filtered[filtered["topics"].apply(lambda topics: bool(wanted & set(split_topics(topics))))]

            filtered = filtered.reset_index(drop=True)
            render_panels(
                [
                    ("Visible repos", f"{len(filtered):,}", "After the filters above"),
                    ("Avg impact", f"{filtered['impact_score'].mean():.4f}" if not filtered.empty else "0.0000", "Mean impact score in this view"),
                    ("Most stars", compact(filtered["stars"].max()) if not filtered.empty else "0", filtered.iloc[filtered["stars"].idxmax()]["name"] if not filtered.empty else "No repos match"),
                ]
            )

            display_df = pd.DataFrame(
                {
                    "#": range(1, len(filtered) + 1),
                    "Repository": filtered["html_url"],
                    "Language": filtered["language"],
                    "Stars": filtered["stars"],
                    "Forks": filtered["forks"],
                    "Issues": filtered["open_issues"],
                    "Star": (filtered["star_velocity"] * 0.50),
                    "Fork": (filtered["fork_score"] * 0.30),
                    "Issue": (filtered["issue_score"] * 0.20),
                    "Impact": filtered["impact_score"],
                }
            )

            render_section_header("Ranked repositories")
            max_impact = float(leaderboard_df["impact_score"].max()) if not leaderboard_df.empty else 1.0
            st.dataframe(
                display_df,
                hide_index=True,
                width="stretch",
                height=min(720, 35 * (len(display_df) + 1) + 3),
                column_config={
                    "#": st.column_config.NumberColumn(width="small"),
                    "Repository": st.column_config.LinkColumn(display_text=r"https://github\.com/[^/]+/(.+)", width="medium"),
                    "Stars": st.column_config.NumberColumn(format="compact"),
                    "Forks": st.column_config.NumberColumn(format="compact"),
                    "Issues": st.column_config.NumberColumn(format="compact"),
                    "Star": st.column_config.NumberColumn("Star pts", format="%.3f", help="Star velocity × 0.5"),
                    "Fork": st.column_config.NumberColumn("Fork pts", format="%.3f", help="Fork score × 0.3"),
                    "Issue": st.column_config.NumberColumn("Issue pts", format="%.3f", help="Issue score × 0.2"),
                    "Impact": st.column_config.ProgressColumn("Impact score", format="%.4f", min_value=0.0, max_value=max_impact),
                },
            )

        except Exception as exc:
            logger.exception("Leaderboard page failed to load.")
            st.error(f"Error loading data: {exc}")

    elif page == "Trends":
        try:
            df = load_trends()
            latest = load_latest_growth()
            render_hero(
                "Trends",
                "Which repositories gained the most stars in the latest run, and how their totals have moved over time.",
            )

            if latest.empty:
                st.info("Only one snapshot is available. Growth analytics will appear after the next daily run.")
            else:
                fastest = latest.head(10)
                render_panels(
                    [
                        ("Fastest daily mover", fastest.iloc[0]["name"], f"+{fastest.iloc[0]['star_growth']:,.0f} stars in the latest run"),
                        ("Total growth today", f"+{compact(latest['star_growth'].clip(lower=0).sum())}", "Stars gained across all tracked repos"),
                        ("Repos with history", f"{len(latest):,}", "Repositories with at least two snapshots"),
                    ]
                )

                render_section_header("Fastest growing now")
                ordered = fastest.sort_values("star_growth")
                fig = hbar(
                    ordered["name"],
                    ordered["star_growth"].values,
                    [f"+{compact(v)}" for v in ordered["star_growth"]],
                    [GREEN if i == len(ordered) - 1 else "rgba(73,209,125,0.5)" for i in range(len(ordered))],
                    "%{y}: +%{x:,.0f} stars<extra></extra>",
                )
                show_chart(style_fig(fig, 380))

                render_section_header("Compare repositories")
                ranked = df.groupby("name")["stars"].max().sort_values(ascending=False)
                options = ranked.head(30).index.tolist()
                pick_col, mode_col = st.columns([3, 1.2], vertical_alignment="bottom")
                with pick_col:
                    selected = st.multiselect("Repositories", options=options, default=options[:5], max_selections=len(LINE_PALETTE))
                with mode_col:
                    mode = st.segmented_control("Show", ["Total stars", "% growth"], default="Total stars") or "Total stars"

                if selected:
                    fig2 = go.Figure()
                    for color, name in zip(LINE_PALETTE, selected):
                        series = df[df["name"] == name].sort_values("snapshot_date")
                        if mode == "% growth":
                            y = (series["stars"] / series["stars"].iloc[0] - 1) * 100
                            hover = f"{name}<br>%{{x|%d %b %Y}}: %{{y:+.1f}}%<extra></extra>"
                        else:
                            y = series["stars"]
                            hover = f"{name}<br>%{{x|%d %b %Y}}: %{{y:,.0f}} stars<extra></extra>"
                        fig2.add_trace(go.Scatter(x=series["snapshot_date"], y=y, name=name, mode="lines", line=dict(width=2.4, color=color), hovertemplate=hover))
                    style_fig(fig2, 440)
                    if mode == "% growth":
                        fig2.update_yaxes(ticksuffix="%")
                    show_chart(fig2)

        except Exception as exc:
            logger.exception("Trends page failed to load.")
            st.error(f"Error loading data: {exc}")

    elif page == "Anomalies":
        try:
            render_hero(
                "Anomalies",
                "Repositories whose latest star growth is more than two standard deviations above the average. These are the spikes worth a closer look.",
            )

            if anomaly_threshold is None:
                st.info("Need at least two snapshots before anomaly detection becomes meaningful.")
            else:
                render_panels(
                    [
                        ("Flagged repositories", f"{anomaly_count:,}", "Above the current threshold"),
                        ("Threshold", f"+{anomaly_threshold:,.0f}", "Stars gained in one run to get flagged"),
                        ("Detection rule", "Mean + 2σ", "Computed over the latest run"),
                    ]
                )

                render_section_header("Flagged growth events")
                if anomalies_df.empty:
                    st.success("No repositories are above the anomaly threshold in the latest run.")
                else:
                    cards = []
                    for _, row in anomalies_df.iterrows():
                        url = row.get("html_url") or f"https://github.com/{row['full_name']}"
                        multiple = row["star_growth"] / anomaly_threshold if anomaly_threshold else 0
                        cards.append(
                            f'<div class="anomaly-card">'
                            f'<div class="repo-top"><div class="repo-rank">Outlier · {esc(row["language"] or "Unknown")}</div>'
                            f'<div class="anomaly-growth">+{row["star_growth"]:,.0f}</div></div>'
                            f'<a class="repo-name" href="{esc(url)}" target="_blank" rel="noopener">{esc(row["name"])}</a>'
                            f'<div class="repo-stats"><span><b>{compact(row["stars"])}</b> total stars</span>'
                            f"<span><b>{multiple:.1f}×</b> the threshold</span></div>"
                            "</div>"
                        )
                    render_html(f'<div class="card-grid">{"".join(cards)}</div>')

                render_section_header("Latest growth vs threshold")
                top20 = load_latest_growth().head(20)
                flagged_mask = top20["star_growth"] > anomaly_threshold
                fig = go.Figure(
                    go.Bar(
                        x=top20["name"],
                        y=top20["star_growth"],
                        marker_color=[RED if f else "rgba(79,140,255,0.45)" for f in flagged_mask],
                        hovertemplate="%{x}: +%{y:,.0f} stars<extra></extra>",
                    )
                )
                fig.add_hline(
                    y=anomaly_threshold,
                    line_dash="dash",
                    line_color=AMBER,
                    line_width=1.5,
                    annotation_text=f"threshold +{anomaly_threshold:,.0f}",
                    annotation_position="top right",
                    annotation_font=dict(color=AMBER, family="IBM Plex Mono", size=10),
                )
                style_fig(fig, 420)
                fig.update_xaxes(tickangle=-35)
                show_chart(fig)

        except Exception as exc:
            logger.exception("Anomalies page failed to load.")
            st.error(f"Error loading data: {exc}")

    render_html(
        """
        <div class="footer-note">
            Built by Varun Lal · <a href="https://github.com/varunNeon" target="_blank">GitHub</a> · <a href="https://www.linkedin.com/in/varunnlal/" target="_blank">LinkedIn</a>
        </div>
        """
    )
