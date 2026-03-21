import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import text
from datetime import datetime
import sys
import os

# ── Add project root to path so imports work when running from dashboard/ ──
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from warehouse.db import get_engine

# ══════════════════════════════════════════════════
#  PAGE CONFIG — must be first Streamlit call
# ══════════════════════════════════════════════════
st.set_page_config(
    page_title="GitPulse",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ══════════════════════════════════════════════════
#  GLOBAL CSS — dark techy theme
# ══════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600;700&family=Syne:wght@400;600;700;800&display=swap');

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
    background-color: #080B10;
    color: #C9D1D9;
}

/* ── Hide Streamlit default chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 2.5rem 2rem 2.5rem; max-width: 1400px; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0D1117;
    border-right: 1px solid #21262D;
}
[data-testid="stSidebar"] * { font-family: 'JetBrains Mono', monospace !important; }

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: #0D1117;
    border: 1px solid #21262D;
    border-radius: 8px;
    padding: 1.2rem 1.5rem;
    transition: border-color 0.2s;
}
[data-testid="metric-container"]:hover { border-color: #58A6FF; }
[data-testid="stMetricLabel"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.7rem !important;
    color: #8B949E !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}
[data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1.8rem !important;
    color: #58A6FF !important;
    font-weight: 700;
}
[data-testid="stMetricDelta"] { font-family: 'JetBrains Mono', monospace !important; }

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border: 1px solid #21262D;
    border-radius: 8px;
    overflow: hidden;
}

/* ── Selectbox & Multiselect ── */
[data-testid="stSelectbox"] > div > div,
[data-testid="stMultiSelect"] > div > div {
    background: #0D1117 !important;
    border-color: #21262D !important;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
}

/* ── Section headers ── */
.section-header {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    color: #58A6FF;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    margin-bottom: 0.75rem;
    border-left: 3px solid #58A6FF;
    padding-left: 0.75rem;
    font-weight: 600;
}

/* ── Anomaly alert box ── */
.anomaly-card {
    background: linear-gradient(135deg, #1a0a0a, #0D1117);
    border: 1px solid #F85149;
    border-radius: 8px;
    padding: 1rem 1.5rem;
    margin-bottom: 0.75rem;
}
.anomaly-name {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1rem;
    font-weight: 700;
    color: #F85149;
}
.anomaly-stat {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    color: #8B949E;
    margin-top: 0.2rem;
}
.anomaly-growth {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.1rem;
    font-weight: 700;
    color: #FF7B72;
}

/* ── Top repo card ── */
.repo-card {
    background: #0D1117;
    border: 1px solid #21262D;
    border-radius: 8px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.6rem;
    transition: border-color 0.2s, transform 0.1s;
}
.repo-card:hover { border-color: #58A6FF; transform: translateX(3px); }
.repo-rank {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: #58A6FF;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}
.repo-name {
    font-family: 'Syne', sans-serif;
    font-size: 1rem;
    font-weight: 700;
    color: #E6EDF3;
}
.repo-meta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: #8B949E;
    margin-top: 0.2rem;
}
.score-pill {
    display: inline-block;
    background: #0d2137;
    border: 1px solid #58A6FF;
    color: #58A6FF;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    font-weight: 700;
    padding: 0.15rem 0.6rem;
    border-radius: 20px;
}

/* ── Logo area ── */
.logo-text {
    font-family: 'Syne', sans-serif;
    font-size: 1.6rem;
    font-weight: 800;
    color: #E6EDF3;
    letter-spacing: -0.02em;
}
.logo-accent { color: #58A6FF; }
.logo-sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: #8B949E;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-top: -4px;
}
            /* Hide broken Material Icons text */
[data-testid="stSidebarCollapseButton"] span {
    display: none;
}

/* ── Divider ── */
hr { border-color: #21262D !important; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════
#  DATA LOADING FUNCTIONS — cached for performance
# ══════════════════════════════════════════════════

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_leaderboard():
    """Loads today's impact scores joined with repo metadata."""
    engine = get_engine()
    with engine.connect() as conn:
        df = pd.read_sql(text("""
            SELECT 
                r.name, r.full_name, r.language, r.topics, r.html_url,
                s.stars, s.forks, s.open_issues,
                sc.impact_score, sc.star_velocity, sc.snapshot_date
            FROM dim_repos r
            JOIN fact_repo_stats s ON r.repo_id = s.repo_id
            JOIN fact_repo_scores sc ON r.repo_id = sc.repo_id
            WHERE sc.snapshot_date = (SELECT MAX(snapshot_date) FROM fact_repo_scores)
            AND s.snapshot_date = (SELECT MAX(snapshot_date) FROM fact_repo_stats)
            ORDER BY sc.impact_score DESC
            """), conn)
    return df

@st.cache_data(ttl=300)
def load_trends():
    """Loads all historical snapshots to compute star growth over time."""
    engine = get_engine()
    with engine.connect() as conn:
        df = pd.read_sql(text("""
            SELECT 
                r.name, r.full_name, r.language,
                s.snapshot_date, s.stars, s.forks, s.open_issues
            FROM dim_repos r
            JOIN fact_repo_stats s ON r.repo_id = s.repo_id
            ORDER BY r.name, s.snapshot_date ASC
        """), conn)
    return df

@st.cache_data(ttl=300)
def load_anomalies():
    """Detects repos whose star growth is 2+ std deviations above the mean."""
    df = load_trends()
    df = df.sort_values(["full_name", "snapshot_date"])
    df["star_growth"] = df.groupby("full_name")["stars"].diff()
    trend_df = df.dropna(subset=["star_growth"])

    if trend_df.empty:
        return pd.DataFrame()

    # Get most recent growth per repo
    latest = trend_df.groupby("full_name").last().reset_index()

    # Anomaly = growth > mean + 2 * std deviation
    mean_g = latest["star_growth"].mean()
    std_g = latest["star_growth"].std()
    threshold = mean_g + 2 * std_g

    anomalies = latest[latest["star_growth"] > threshold].sort_values(
        "star_growth", ascending=False
    )
    return anomalies, threshold


# ══════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
        <div class="logo-text">Git<span class="logo-accent">Pulse</span></div>
        <div class="logo-sub">AI/ML Intelligence Layer</div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Navigation
    page = st.radio(
        "NAVIGATE",
        ["⚡ Overview", "🏆 Leaderboard", "📈 Trends", "🚨 Anomalies"],
        label_visibility="visible"
    )

    st.markdown("---")

    # Read last pipeline run time from file instead of showing page load time
    # Read last pipeline run time from database instead of local file
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT MAX(snapshot_date) FROM fact_repo_stats
            """)).fetchone()
            if result and result[0]:
                last_updated = str(result[0].strftime('%d %b %Y'))
            else:
                last_updated = "Never — run pipeline first"
    except Exception:
        last_updated = "Never — run pipeline first"

    st.markdown(f"""
        <div style="font-family:'JetBrains Mono',monospace; font-size:0.65rem; color:#8B949E;">
        LAST UPDATED<br>
        <span style="color:#3FB950;">{last_updated}</span>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
        <div style="font-family:'JetBrains Mono',monospace; font-size:0.65rem; color:#8B949E;">
            TRACKING<br>
            <span style="color:#58A6FF;">8 AI/ML TOPICS</span>
        </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════
#  PLOTLY DARK THEME — consistent across all charts
# ══════════════════════════════════════════════════

CHART_THEME = dict(
    paper_bgcolor="#080B10",
    plot_bgcolor="#0D1117",
    font=dict(family="JetBrains Mono", color="#8B949E", size=11),
    xaxis=dict(gridcolor="#21262D", linecolor="#21262D", tickcolor="#21262D"),
    yaxis=dict(gridcolor="#21262D", linecolor="#21262D", tickcolor="#21262D"),
    margin=dict(l=20, r=20, t=40, b=20)
)


# ══════════════════════════════════════════════════
#  PAGE: OVERVIEW
# ══════════════════════════════════════════════════

if page == "⚡ Overview":

    st.markdown("""
        <h1 style="font-family:'Syne',sans-serif; font-size:2rem; font-weight:800; 
        color:#E6EDF3; margin-bottom:0;">
        ⚡ GitPulse <span style="color:#58A6FF;">Overview</span>
        </h1>
        <p style="font-family:'JetBrains Mono',monospace; font-size:0.75rem; 
        color:#8B949E; margin-top:4px;">
        Real-time intelligence across the AI/ML GitHub ecosystem
        </p>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Load data
    try:
        df = load_leaderboard()
        trends_df = load_trends()

        if df.empty:
            st.error("⚠️ No data for today. Run `python -m pipeline.runner` first.")
            st.stop()

        # ── Top KPI metrics ──
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Repos Tracked", f"{len(df):,}")
        with col2:
            st.metric("Total Stars", f"{df['stars'].sum():,.0f}")
        with col3:
            st.metric("Top Impact Score", f"{df['impact_score'].max():.4f}")
        with col4:
            langs = df['language'].nunique()
            st.metric("Languages", f"{langs}")

        st.markdown("<br>", unsafe_allow_html=True)
        # ── Hidden Gems section ──
        from analysis.impact_score import find_hidden_gems
        st.markdown('<div class="section-header">💎 Hidden Gems — High Momentum, Low Visibility</div>', unsafe_allow_html=True)
        gems = find_hidden_gems()

        if not gems.empty:
            gem_cols = st.columns(3)
            for i, (_, row) in enumerate(gems.head(6).iterrows()):
                with gem_cols[i % 3]:
                    st.markdown(f"""
                        <div class="repo-card" style="border-color:#3FB950;">
                            <div class="repo-rank" style="color:#3FB950;">💎 &nbsp;{row['language'] or 'N/A'}</div>
                            <div class="repo-name">{row['name']}</div>
                            <div class="repo-meta">
                                {row['language'] or 'N/A'} &nbsp;·&nbsp; 
                                ⭐ {row['stars']:,} &nbsp;·&nbsp; 
                                🍴 {row['forks']:,}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Two column layout ──
        left, right = st.columns([1.2, 1], gap="large")

        with left:
            st.markdown('<div class="section-header">Top 5 by Impact Score</div>', unsafe_allow_html=True)
            top5 = df.head(5)
            for i, row in top5.iterrows():
                rank = df.index.get_loc(i) + 1
                st.markdown(f"""
                    <div class="repo-card">
                        <div class="repo-rank">#{rank} &nbsp;·&nbsp; {row['language'] or 'N/A'}</div>
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div class="repo-name">{row['name']}</div>
                            <div class="score-pill">{row['impact_score']:.4f}</div>
                        </div>
                        <div class="repo-meta">⭐ {row['stars']:,} &nbsp;·&nbsp; 🍴 {row['forks']:,} &nbsp;·&nbsp; {row['topics'][:60] if row['topics'] else '—'}</div>
                    </div>
                """, unsafe_allow_html=True)

        with right:
            st.markdown('<div class="section-header">Stars by Language</div>', unsafe_allow_html=True)
            lang_df = df.groupby("language")["stars"].sum().sort_values(ascending=True).tail(8).reset_index()

            fig = go.Figure(go.Bar(
                x=lang_df["stars"],
                y=lang_df["language"],
                orientation="h",
                marker=dict(
                    color=lang_df["stars"],
                    colorscale=[[0, "#0d2137"], [1, "#58A6FF"]],
                    showscale=False
                ),
                text=[f"{v:,.0f}" for v in lang_df["stars"]],
                textposition="outside",
                textfont=dict(family="JetBrains Mono", size=10, color="#8B949E")
            ))
            fig.update_layout(**CHART_THEME, height=300)
            st.plotly_chart(fig, use_container_width=True)

            st.markdown('<div class="section-header" style="margin-top:1rem;">Top Topics Distribution</div>', unsafe_allow_html=True)

            # Explode comma-separated topics into individual rows
            topic_series = df["topics"].dropna().str.split(", ").explode()
            topic_counts = topic_series.value_counts().head(8).reset_index()
            topic_counts.columns = ["topic", "count"]

            fig2 = px.bar(
                topic_counts, x="count", y="topic", orientation="h",
                color="count",
                color_continuous_scale=["#0d2137", "#3FB950"],
            )
            fig2.update_layout(**CHART_THEME, height=280, coloraxis_showscale=False)
            fig2.update_traces(textposition="outside")
            st.plotly_chart(fig2, use_container_width=True)

    except Exception as e:
        st.error(f"Error loading data: {e}")


# ══════════════════════════════════════════════════
#  PAGE: LEADERBOARD
# ══════════════════════════════════════════════════

elif page == "🏆 Leaderboard":

    st.markdown("""
        <h1 style="font-family:'Syne',sans-serif; font-size:2rem; font-weight:800; color:#E6EDF3;">
        🏆 <span style="color:#58A6FF;">Leaderboard</span>
        </h1>
        <p style="font-family:'JetBrains Mono',monospace; font-size:0.75rem; color:#8B949E;">
        All repos ranked by composite impact score
        </p>
    """, unsafe_allow_html=True)

    st.markdown("---")

    try:
        df = load_leaderboard()

        # ── Filters ──
        col1, col2 = st.columns([1, 2])
        with col1:
            languages = ["All"] + sorted(df["language"].dropna().unique().tolist())
            selected_lang = st.selectbox("Filter by Language", languages)
        with col2:
            all_topics = sorted(set(
                t.strip()
                for topics in df["topics"].dropna()
                for t in topics.split(",")
            ))
            selected_topics = st.multiselect("Filter by Topic", all_topics)

        # Apply filters
        filtered = df.copy()
        if selected_lang != "All":
            filtered = filtered[filtered["language"] == selected_lang]
        if selected_topics:
            filtered = filtered[filtered["topics"].apply(
                lambda t: any(topic.strip() in (t or "") for topic in selected_topics)
            )]

        filtered = filtered.reset_index(drop=True)
        filtered.index += 1  # Start ranking from 1

        # Add score breakdown columns so users understand why each repo is ranked
        filtered["⭐ Star Score"] = (filtered["star_velocity"] * 0.50).round(4)
        filtered["🍴 Fork Score"] = (filtered["star_velocity"] * 0.30).round(4)
        filtered["🐛 Issue Score"] = (filtered["star_velocity"] * 0.20).round(4)

        display_df = filtered[[
            "name", "language", "stars", "forks", "open_issues",
            "⭐ Star Score", "🍴 Fork Score", "🐛 Issue Score", "impact_score"
        ]].rename(columns={
            "name": "Repository",
            "language": "Language",
            "stars": "Stars",
            "forks": "Forks",
            "open_issues": "Issues",
            "impact_score": "Impact Score"
        })

        st.dataframe(
            display_df.style.background_gradient(
                subset=["Impact Score"],
                cmap="Blues"
            ).format({"Impact Score": "{:.4f}", "⭐ Stars": "{:,}", "🍴 Forks": "{:,}"}),
            use_container_width=True,
            height=600
        )

        st.markdown(f"""
            <div style="font-family:'JetBrains Mono',monospace; font-size:0.7rem; 
            color:#8B949E; margin-top:0.5rem;">
            Showing {len(filtered)} repositories
            </div>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error loading data: {e}")


# ══════════════════════════════════════════════════
#  PAGE: TRENDS
# ══════════════════════════════════════════════════

elif page == "📈 Trends":

    st.markdown("""
        <h1 style="font-family:'Syne',sans-serif; font-size:2rem; font-weight:800; color:#E6EDF3;">
        📈 <span style="color:#58A6FF;">Trends</span>
        </h1>
        <p style="font-family:'JetBrains Mono',monospace; font-size:0.75rem; color:#8B949E;">
        Star growth and momentum across AI/ML repositories
        </p>
    """, unsafe_allow_html=True)

    st.markdown("---")

    try:
        df = load_trends()
        df = df.sort_values(["full_name", "snapshot_date"])
        df["star_growth"] = df.groupby("full_name")["stars"].diff()

        trend_df = df.dropna(subset=["star_growth"])

        if trend_df.empty:
            st.info("⏳ Only one day of data so far. Run the pipeline daily to see growth trends build up.")

            st.markdown('<div class="section-header">Current Snapshot — Top 15 by Stars</div>', unsafe_allow_html=True)
            snapshot = df.groupby("name").last().reset_index()\
                .sort_values("stars", ascending=False).head(15)

            fig = px.bar(
                snapshot, x="stars", y="name", orientation="h",
                color="stars", color_continuous_scale=["#0d2137", "#58A6FF"]
            )
            fig.update_layout(**CHART_THEME, height=500, coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

        else:
            # ── Fastest growing today ──
            latest = trend_df.groupby("full_name").last().reset_index()
            fastest = latest.sort_values("star_growth", ascending=False).head(10)

            st.markdown('<div class="section-header">Fastest Growing Today</div>', unsafe_allow_html=True)

            fig = go.Figure(go.Bar(
                x=fastest["star_growth"],
                y=fastest["name"],
                orientation="h",
                marker=dict(
                    color=fastest["star_growth"],
                    colorscale=[[0, "#0d2137"], [1, "#3FB950"]],
                    showscale=False
                ),
                text=[f"+{v:.0f}" for v in fastest["star_growth"]],
                textposition="outside",
                textfont=dict(family="JetBrains Mono", size=10, color="#3FB950")
            ))
            fig.update_layout(**CHART_THEME, height=380)
            st.plotly_chart(fig, use_container_width=True)

            # ── Star history line chart ──
            st.markdown('<div class="section-header" style="margin-top:1rem;">Star Growth Over Time</div>', unsafe_allow_html=True)

            top_repos = df.groupby("name")["stars"].max()\
                .sort_values(ascending=False).head(10).index.tolist()
            selected = st.multiselect(
                "Select repos to compare",
                options=top_repos,
                default=top_repos[:5]
            )

            if selected:
                chart_df = df[df["name"].isin(selected)]
                fig2 = px.line(
                    chart_df, x="snapshot_date", y="stars",
                    color="name",
                    color_discrete_sequence=px.colors.qualitative.Safe
                )
                fig2.update_traces(line=dict(width=2))
                fig2.update_layout(**CHART_THEME, height=400, legend=dict(
                    bgcolor="#0D1117", bordercolor="#21262D", borderwidth=1
                ))
                st.plotly_chart(fig2, use_container_width=True)

    except Exception as e:
        st.error(f"Error loading data: {e}")


# ══════════════════════════════════════════════════
#  PAGE: ANOMALIES
# ══════════════════════════════════════════════════

elif page == "🚨 Anomalies":

    st.markdown("""
        <h1 style="font-family:'Syne',sans-serif; font-size:2rem; font-weight:800; color:#E6EDF3;">
        🚨 <span style="color:#F85149;">Anomaly</span> Detection
        </h1>
        <p style="font-family:'JetBrains Mono',monospace; font-size:0.75rem; color:#8B949E;">
        Repositories with statistically unusual growth — flagged via 2σ threshold
        </p>
    """, unsafe_allow_html=True)

    st.markdown("---")

    try:
        result = load_anomalies()

        if isinstance(result, pd.DataFrame) and result.empty:
            st.info("⏳ Need at least 2 days of data for anomaly detection.")
        else:
            anomalies, threshold = result

            if anomalies.empty:
                st.success("✅ No anomalies detected today. All repos growing within normal range.")
            else:
                st.markdown(f"""
                    <div style="font-family:'JetBrains Mono',monospace; font-size:0.75rem; 
                    color:#8B949E; margin-bottom:1.5rem;">
                    DETECTION THRESHOLD &nbsp;·&nbsp; 
                    <span style="color:#F85149;">+{threshold:.0f} stars/day</span> &nbsp;·&nbsp;
                    {len(anomalies)} repo(s) flagged
                    </div>
                """, unsafe_allow_html=True)

                # ── Anomaly cards ──
                for _, row in anomalies.iterrows():
                    st.markdown(f"""
                        <div class="anomaly-card">
                            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                                <div>
                                    <div class="anomaly-name">⚡ {row['name']}</div>
                                    <div class="anomaly-stat">
                                        {row['language'] or 'Unknown'} &nbsp;·&nbsp; 
                                        ⭐ {row['stars']:,.0f} total stars
                                    </div>
                                </div>
                                <div class="anomaly-growth">+{row['star_growth']:,.0f} ✦</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                # ── Comparison chart ──
                st.markdown('<div class="section-header" style="margin-top:1.5rem;">Growth vs Threshold</div>', unsafe_allow_html=True)

                trends_df = load_trends()
                trends_df["star_growth"] = trends_df.groupby("full_name")["stars"].diff()
                latest_all = trends_df.dropna(subset=["star_growth"])\
                    .groupby("name").last().reset_index()\
                    .sort_values("star_growth", ascending=False).head(20)

                fig = go.Figure()

                # Normal repos
                normal = latest_all[latest_all["star_growth"] <= threshold]
                fig.add_trace(go.Bar(
                    x=normal["name"], y=normal["star_growth"],
                    name="Normal", marker_color="#21262D"
                ))

                # Anomalous repos
                flagged = latest_all[latest_all["star_growth"] > threshold]
                fig.add_trace(go.Bar(
                    x=flagged["name"], y=flagged["star_growth"],
                    name="Anomaly", marker_color="#F85149"
                ))

                # Threshold line
                fig.add_hline(
                    y=threshold, line_dash="dash",
                    line_color="#FF7B72", line_width=1.5,
                    annotation_text=f"  2σ threshold: {threshold:.0f}",
                    annotation_font=dict(color="#FF7B72", family="JetBrains Mono", size=10)
                )

                fig.update_layout(**CHART_THEME, height=380, barmode="overlay",
                    legend=dict(bgcolor="#0D1117", bordercolor="#21262D", borderwidth=1))
                st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error loading data: {e}")


        # ══════════════════════════════════════════════════
#  FOOTER
# ══════════════════════════════════════════════════

st.markdown("---")
st.markdown("""
    <div style="font-family:'JetBrains Mono',monospace; font-size:0.7rem; 
    color:#8B949E; text-align:center; padding: 1rem 0;">
        Built by <span style="color:#E6EDF3; font-weight:600;">Varun Lal</span> 
        &nbsp;·&nbsp; 
        <a href="https://github.com/varunNeon"
        style="color:#58A6FF; text-decoration:none;">GitHub</a>
        &nbsp;·&nbsp;
        <a href="https://www.linkedin.com/in/varunnlal/"
        style="color:#58A6FF; text-decoration:none;">LinkedIn</a>
        &nbsp;·&nbsp;
        <span style="color:#8B949E;">GitPulse v1.0</span>
    </div>
""", unsafe_allow_html=True)
