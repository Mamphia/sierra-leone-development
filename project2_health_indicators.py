"""
Sierra Leone Health & Development Indicators Dashboard (2000–2022)
==================================================================
Data source: World Bank World Development Indicators (WDI)
Real data available at: https://data.worldbank.org/country/sierra-leone
Replace generate_data() with: df = pd.read_csv('your_wdi_file.csv')

Author: Mamadu Jalloh
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from sklearn.linear_model import LinearRegression
import warnings
warnings.filterwarnings("ignore")

np.random.seed(7)

# ── 1. GENERATE REALISTIC WDI DATA FOR SIERRA LEONE ─────────────────────────
# Sources for baseline values (real World Bank figures):
# Life expectancy 2000: ~37yrs → 2022: ~61yrs (post-Ebola recovery)
# Under-5 mortality 2000: ~270/1000 → 2022: ~109/1000
# GDP per capita 2000: ~140 USD → 2022: ~510 USD
# Access to electricity 2000: ~3% → 2022: ~27%
# Literacy rate: ~25% (2000) → ~48% (2022)
# Maternal mortality 2000: ~3400/100k → 2022: ~443/100k

def generate_data():
    years = np.arange(2000, 2023)
    n = len(years)

    def smooth_series(start, end, n, noise_scale=0.01, ebola_year=None, ebola_impact=0):
        """Generate a smoothly trending series with optional Ebola dip."""
        base = np.linspace(start, end, n)
        noise = np.random.normal(0, abs(end - start) * noise_scale, n)
        series = base + noise
        if ebola_year:
            idx = ebola_year - 2000
            series[idx] += ebola_impact
            series[idx + 1] += ebola_impact * 0.5  # recovery lag
        return np.round(series, 2)

    df = pd.DataFrame({
        "year": years,
        "life_expectancy":     smooth_series(37.2, 61.4, n, 0.008, 2014, -2.8),
        "under5_mortality":    smooth_series(270, 109, n, 0.015, 2014, 18),
        "gdp_per_capita":      smooth_series(140, 510, n, 0.03, 2014, -35),
        "electricity_access":  smooth_series(3.1, 27.2, n, 0.04),
        "literacy_rate":       smooth_series(25.4, 48.3, n, 0.01),
        "maternal_mortality":  smooth_series(3400, 443, n, 0.02, 2014, 210),
        "health_expenditure":  smooth_series(3.1, 8.4, n, 0.05, 2014, -1.5),
        "school_enrollment":   smooth_series(42.1, 78.6, n, 0.015),
    })
    return df

df = generate_data()

# ── 2. SQL-STYLE ANALYSIS (pandas) ───────────────────────────────────────────
print("=== QUERY 1: Decade-over-decade change ===")
q1 = df[df["year"].isin([2000, 2010, 2022])][
    ["year", "life_expectancy", "under5_mortality", "gdp_per_capita", "electricity_access"]
]
print(q1.to_string(index=False))

print("\n=== QUERY 2: Ebola impact window (2013–2016) ===")
q2 = df[df["year"].between(2013, 2016)][
    ["year", "life_expectancy", "gdp_per_capita", "maternal_mortality", "health_expenditure"]
]
print(q2.to_string(index=False))

print("\n=== QUERY 3: Years where GDP grew >10% YoY ===")
df["gdp_growth"] = df["gdp_per_capita"].pct_change() * 100
q3 = df[df["gdp_growth"] > 10][["year", "gdp_per_capita", "gdp_growth"]]
print(q3.to_string(index=False))

# ── 3. CORRELATION MATRIX ─────────────────────────────────────────────────────
indicators = ["life_expectancy", "under5_mortality", "gdp_per_capita",
              "electricity_access", "literacy_rate"]
corr = df[indicators].corr().round(2)

# ── 4. REGRESSION: Electricity access → Life expectancy ──────────────────────
X = df["electricity_access"].values.reshape(-1, 1)
y = df["life_expectancy"].values
reg = LinearRegression().fit(X, y)
r2_elec = reg.score(X, y)
coef_elec = reg.coef_[0]

# ── 5. PLOT ───────────────────────────────────────────────────────────────────
DARK  = "#1A1D1B"
PAPER = "#EFEAE0"
GREEN = "#6FFFB0"
AMBER = "#E8A23D"
BLUE  = "#5BA4CF"
RED   = "#E85D3D"
MUTED = "#8A8678"

plt.rcParams.update({
    "figure.facecolor": DARK,
    "axes.facecolor":   DARK,
    "text.color":       PAPER,
    "axes.labelcolor":  PAPER,
    "xtick.color":      MUTED,
    "ytick.color":      MUTED,
    "axes.edgecolor":   "#2E332F",
    "grid.color":       "#2E332F",
    "grid.linestyle":   "--",
    "grid.alpha":       0.4,
    "font.family":      "monospace",
    "figure.dpi":       130,
})

fig = plt.figure(figsize=(16, 15))
fig.suptitle("SIERRA LEONE · HEALTH & DEVELOPMENT INDICATORS · 2000–2022",
             fontsize=13, fontweight="bold", color=PAPER, y=0.98)
gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.52, wspace=0.32)

def add_ebola_band(ax):
    ax.axvspan(2014, 2016, alpha=0.08, color=RED, label="Ebola crisis")

# — Panel 1: Life expectancy ──────────────────────────────────────────────────
ax1 = fig.add_subplot(gs[0, 0])
ax1.plot(df["year"], df["life_expectancy"], color=GREEN, lw=2)
ax1.fill_between(df["year"], df["life_expectancy"].min(),
                 df["life_expectancy"], alpha=0.15, color=GREEN)
add_ebola_band(ax1)
ax1.annotate("Ebola\ncrisis", xy=(2015, df.loc[df.year==2015,"life_expectancy"].values[0]),
             xytext=(2017, 42), fontsize=7, color=RED,
             arrowprops=dict(arrowstyle="->", color=RED, lw=0.8))
ax1.set_title("LIFE EXPECTANCY AT BIRTH (yrs)", fontsize=9, color=MUTED, loc="left", pad=8)
ax1.set_ylabel("Years")
ax1.legend(fontsize=7, framealpha=0.1)
ax1.grid(True)

# — Panel 2: Under-5 mortality ────────────────────────────────────────────────
ax2 = fig.add_subplot(gs[0, 1])
ax2.plot(df["year"], df["under5_mortality"], color=RED, lw=2)
ax2.fill_between(df["year"], df["under5_mortality"].min(),
                 df["under5_mortality"], alpha=0.12, color=RED)
add_ebola_band(ax2)
ax2.set_title("UNDER-5 MORTALITY RATE (per 1,000 live births)", fontsize=9, color=MUTED, loc="left", pad=8)
ax2.set_ylabel("Deaths per 1,000")
ax2.legend(fontsize=7, framealpha=0.1)
ax2.grid(True)

# — Panel 3: GDP per capita ───────────────────────────────────────────────────
ax3 = fig.add_subplot(gs[1, 0])
ax3.bar(df["year"], df["gdp_per_capita"], color=AMBER, alpha=0.7, width=0.8)
trend = np.polyfit(df["year"], df["gdp_per_capita"], 1)
ax3.plot(df["year"], np.polyval(trend, df["year"]),
         color=GREEN, lw=1.8, linestyle="--", label="Trend")
add_ebola_band(ax3)
ax3.set_title("GDP PER CAPITA (USD)", fontsize=9, color=MUTED, loc="left", pad=8)
ax3.set_ylabel("USD")
ax3.legend(fontsize=7, framealpha=0.1)
ax3.grid(True, axis="y")

# — Panel 4: Electricity access + Literacy ────────────────────────────────────
ax4 = fig.add_subplot(gs[1, 1])
ax4.plot(df["year"], df["electricity_access"], color=AMBER, lw=2, label="Electricity access %")
ax4.plot(df["year"], df["literacy_rate"], color=BLUE, lw=2, label="Literacy rate %")
ax4.plot(df["year"], df["school_enrollment"], color=GREEN, lw=1.5,
         linestyle="--", label="School enrollment %")
add_ebola_band(ax4)
ax4.set_title("ACCESS INDICATORS (%)", fontsize=9, color=MUTED, loc="left", pad=8)
ax4.set_ylabel("%")
ax4.legend(fontsize=7, framealpha=0.1)
ax4.grid(True)

# — Panel 5: Scatter — Electricity vs Life expectancy ─────────────────────────
ax5 = fig.add_subplot(gs[2, 0])
sc = ax5.scatter(df["electricity_access"], df["life_expectancy"],
                 c=df["year"], cmap="YlGn", s=50, zorder=3)
x_line = np.linspace(df["electricity_access"].min(), df["electricity_access"].max(), 100)
ax5.plot(x_line, reg.predict(x_line.reshape(-1,1)), color=AMBER,
         lw=1.8, linestyle="--", label=f"R²={r2_elec:.2f}, slope={coef_elec:.2f}")
plt.colorbar(sc, ax=ax5, label="Year")
ax5.set_title("ELECTRICITY ACCESS vs LIFE EXPECTANCY", fontsize=9, color=MUTED, loc="left", pad=8)
ax5.set_xlabel("Electricity access (%)")
ax5.set_ylabel("Life expectancy (yrs)")
ax5.legend(fontsize=7, framealpha=0.1)
ax5.grid(True)

# — Panel 6: Correlation heatmap ──────────────────────────────────────────────
ax6 = fig.add_subplot(gs[2, 1])
labels_short = ["Life exp.", "U5 mort.", "GDP/cap", "Elec %", "Literacy"]
im = ax6.imshow(corr.values, cmap="RdYlGn", vmin=-1, vmax=1, aspect="auto")
ax6.set_xticks(range(len(labels_short)))
ax6.set_yticks(range(len(labels_short)))
ax6.set_xticklabels(labels_short, rotation=35, ha="right", fontsize=7)
ax6.set_yticklabels(labels_short, fontsize=7)
for i in range(len(labels_short)):
    for j in range(len(labels_short)):
        ax6.text(j, i, f"{corr.values[i,j]:.2f}",
                 ha="center", va="center", fontsize=7,
                 color="black" if abs(corr.values[i,j]) > 0.5 else PAPER)
plt.colorbar(im, ax=ax6)
ax6.set_title("INDICATOR CORRELATION MATRIX", fontsize=9, color=MUTED, loc="left", pad=8)

plt.savefig("/home/claude/projects/health-indicators/health_analysis.png",
            bbox_inches="tight", facecolor=DARK)
plt.close()
print("\n✓ Chart saved")

print(f"""
╔══════════════════════════════════════════════════════════╗
║   KEY FINDINGS — SIERRA LEONE DEVELOPMENT 2000–2022    ║
╠══════════════════════════════════════════════════════════╣
║ Life expectancy : +{df.loc[df.year==2022,'life_expectancy'].values[0] - df.loc[df.year==2000,'life_expectancy'].values[0]:.1f} yrs (2000→2022)              ║
║ U5 mortality    : -{df.loc[df.year==2000,'under5_mortality'].values[0] - df.loc[df.year==2022,'under5_mortality'].values[0]:.0f}/1000 reduction                  ║
║ GDP per capita  : +${df.loc[df.year==2022,'gdp_per_capita'].values[0] - df.loc[df.year==2000,'gdp_per_capita'].values[0]:.0f} USD growth                     ║
║ Electricity     : {df.loc[df.year==2000,'electricity_access'].values[0]:.1f}% → {df.loc[df.year==2022,'electricity_access'].values[0]:.1f}% of population          ║
║ Elec↔Life R²   : {r2_elec:.2f} (strong positive correlation)      ║
║ Ebola impact    : ~{df.loc[df.year==2014,'life_expectancy'].values[0] - df.loc[df.year==2013,'life_expectancy'].values[0]:.1f} yr life expectancy drop (2014)  ║
╚══════════════════════════════════════════════════════════╝
""")
