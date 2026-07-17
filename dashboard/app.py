"""
The "Sugar Trap" — Market Gap Analysis dashboard
Helix CPG Partners | Data: Open Food Facts (European markets)
"""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="The Sugar Trap — Market Gap Analysis",
                   page_icon="🍫", layout="wide")

DATA = Path(__file__).parent.parent / "data" / "snacks_eu_clean.parquet"

QUAD_COLORS = {
    "Blue Ocean (Low Sugar, High Protein)": "#2E7D32",
    "Low Sugar, Low Protein": "#A5D6A7",
    "High Sugar + High Protein": "#FFB74D",
    "Sugar Trap (High Sugar, Low Protein)": "#C62828",
}
QUAD_ORDER = list(QUAD_COLORS)


@st.cache_data
def load_data():
    df = pd.read_parquet(DATA)
    df["brands"] = df["brands"].fillna("Unknown").astype(str)
    df["product_name"] = df["product_name"].astype(str)
    return df


BLUE = "Blue Ocean (Low Sugar, High Protein)"
LOLO = "Low Sugar, Low Protein"
HIHI = "High Sugar + High Protein"
TRAP = "Sugar Trap (High Sugar, Low Protein)"


def assign_quadrant(df, sugar_max, protein_min):
    """Mirrors the notebook's np.select logic exactly."""
    lo_sugar = df.sugars_100g < sugar_max
    hi_prot = df.proteins_100g >= protein_min
    return pd.Series(
        np.select(
            [lo_sugar & hi_prot, ~lo_sugar & hi_prot, lo_sugar & ~hi_prot],
            [BLUE, HIHI, LOLO],
            default=TRAP,
        ),
        index=df.index,
    )


try:
    df = load_data()
except Exception as e:
    st.error(f"Could not load data from `{DATA}`.\n\n{e}")
    st.stop()

# ---------------- sidebar ----------------
st.sidebar.title("Filters")
st.sidebar.caption("Helix CPG Partners · Open Food Facts · 8 European markets")

cats = sorted(df.primary_category.unique())
sel_cats = st.sidebar.multiselect("High-level category", cats, default=cats)

st.sidebar.markdown("---")
st.sidebar.subheader("Quadrant thresholds")
sugar_max = st.sidebar.slider("Max sugar — 'low sugar' (g/100g)", 2, 25, 10)
protein_min = st.sidebar.slider("Min protein — 'high protein' (g/100g)", 5, 25, 10)
st.sidebar.caption(
    "Defaults of 10g/10g reflect where EU nutrient-profile schemes begin flagging sugar, "
    "and a conventional high-protein bar. Move them: the ranking barely changes."
)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Cleaned dataset: US products excluded — only 5.3% carry nutrition data, versus "
    "86–95% across European markets. See notebook for the full audit trail."
)

df["quadrant"] = assign_quadrant(df, sugar_max, protein_min)
d = df[df.primary_category.isin(sel_cats)]

if d.empty:
    st.warning("No products match that filter.")
    st.stop()

# ---------------- header ----------------
st.title("🍫 The Sugar Trap: Where is the Blue Ocean in the snack aisle?")
st.caption(
    f"{len(df):,} European snack products · {len(d):,} in current selection · "
    "Open Food Facts"
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Products shown", f"{len(d):,}")
c2.metric("In the Sugar Trap", f"{(d.quadrant == TRAP).mean():.1%}",
          help="High sugar, low protein")
c3.metric("In the Blue Ocean", f"{(d.quadrant == BLUE).mean():.1%}",
          help="Low sugar, high protein")
ratio = (d.quadrant == TRAP).sum() / max((d.quadrant == BLUE).sum(), 1)
c4.metric("Trap : Ocean ratio", f"{ratio:.1f} : 1")

# ---------------- key insight ----------------
st.success(
    "**Key Insight — Based on the data, the biggest market opportunity is in "
    "Savoury Snacks (chips & crackers), specifically targeting products with 15g of protein "
    "and less than 5g of sugar.**\n\n"
    "15g is the 75th percentile of products *already succeeding* in this quadrant — an "
    "achievable target, not an aspiration. Chips & Savoury ranks first for blue-ocean share "
    "at every threshold tested, and 68% of the category is already low-sugar: it fails on "
    "protein alone.\n\n"
    "⚠️ **Salt caveat:** blue-ocean savoury products carry 1.78g salt/100g and score "
    "Nutri-Score A/B only 9.2% of the time. The brief is three variables, not two — "
    "**15g protein, <5g sugar, <1.0g salt.**"
)

# ---------------- tabs ----------------
tab1, tab2, tab3 = st.tabs(["Nutrient Matrix", "Category breakdown", "Product explorer"])

with tab1:
    st.subheader("Sugar vs Protein — where the products cluster")
    samp = d.sample(min(len(d), 6000), random_state=42)
    fig = px.scatter(
        samp, x="sugars_100g", y="proteins_100g", color="primary_category",
        hover_name="product_name", hover_data={"brands": True},
        opacity=0.35, color_discrete_sequence=px.colors.qualitative.Dark24,
        labels={"sugars_100g": "Sugar (g per 100g)",
                "proteins_100g": "Protein (g per 100g)",
                "primary_category": "Category"},
    )
    fig.update_traces(marker=dict(size=4))
    fig.add_shape(type="rect", x0=0, x1=sugar_max, y0=protein_min, y1=50,
                  fillcolor="green", opacity=0.10, line_width=0, layer="below")
    fig.add_vline(x=sugar_max, line_dash="dash", line_color="grey")
    fig.add_hline(y=protein_min, line_dash="dash", line_color="grey")
    fig.add_annotation(x=5, y=32, ax=80, ay=-45, showarrow=True, arrowhead=2,
                       arrowcolor="#2E7D32", text="<b>BLUE OCEAN</b>",
                       font=dict(color="#2E7D32", size=13))
    fig.update_layout(height=600, yaxis_range=[0, 50], xaxis_range=[0, 85],
                      plot_bgcolor="white")
    fig.update_xaxes(gridcolor="#EEE")
    fig.update_yaxes(gridcolor="#EEE")
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        f"Showing a random sample of {len(samp):,} for legibility; all metrics above are "
        "computed on the full selection."
    )

with tab2:
    st.subheader("Where each category sits")
    q = (pd.crosstab(d.primary_category, d.quadrant, normalize="index") * 100).round(1)
    order = d.primary_category.value_counts().index[::-1]
    q = q.reindex(order)
    for col in QUAD_ORDER:
        if col not in q.columns:
            q[col] = 0.0
    q = q[QUAD_ORDER]

    fig2 = px.bar(q, orientation="h", color_discrete_map=QUAD_COLORS,
                  labels={"value": "% of category", "primary_category": ""})
    fig2.update_layout(height=520, barmode="stack", xaxis_range=[0, 100],
                       legend_title_text="",
                       legend=dict(orientation="h", y=-0.15))
    st.plotly_chart(fig2, use_container_width=True)
    st.caption(
        "Chips & Savoury is the only mass-market category that is predominantly green — it has "
        "already solved sugar and fails on protein alone. Nuts & Seeds has the best profile but "
        "only 1.8% of shelf."
    )

    st.subheader("Category medians")
    stats = (d.groupby("primary_category")
               .agg(products=("code", "size"),
                    median_sugar=("sugars_100g", "median"),
                    median_protein=("proteins_100g", "median"),
                    median_salt=("salt_100g", "median"))
               .round(2).sort_values("products", ascending=False))
    st.dataframe(stats, use_container_width=True)

with tab3:
    st.subheader("Products in the Blue Ocean")
    bo = d[d.quadrant == BLUE]
    n_raw = len(bo)
    bo = bo[bo.proteins_100g <= 40].sort_values("proteins_100g", ascending=False)
    st.caption(
        f"{n_raw:,} products meet <{sugar_max}g sugar and ≥{protein_min}g protein. "
        f"Table excludes {n_raw - len(bo):,} with protein >40g/100g — implausible for a "
        "finished snack and almost certainly data entry errors (e.g. confectionery listed "
        "at 97g protein)."
    )
    st.dataframe(
        bo[["product_name", "brands", "primary_category",
            "proteins_100g", "sugars_100g", "salt_100g"]].head(300),
        use_container_width=True, hide_index=True,
    )
    st.info(
        "**Note the top of this table:** pork rinds and cortezas de cerdo — 70g protein, 0g "
        "sugar, and 3.7–9.4g salt. The blue ocean's highest-protein incumbents are salt bombs. "
        "This is the Nutri-Score problem in product form."
    )

    st.subheader("Who is already there?")
    named = bo[bo.brands != "Unknown"]
    st.bar_chart(named.brands.value_counts().head(15))
    st.caption(
        f"Excludes {len(bo) - len(named):,} products with no brand recorded. The remainder is "
        "retailer own-brand and small regional producers — no global snack manufacturer "
        "appears in the top 15. The space is commercially proven but has no branded incumbent."
    )
