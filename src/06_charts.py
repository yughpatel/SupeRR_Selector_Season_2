# Step 6b : Charts for the report
#
# Run from the project folder : python src/06_charts.py
# Reads  : outputs/05_batters.csv, 05_bowlers.csv, 05_splithalf.csv, 05_blend.csv (step 5)
#          outputs/06_batter_facts.csv, 06_bowler_facts.csv, 06_rr_profile.csv (06_facts.py)
#          outputs/balls_clean.parquet, balls_pressure.parquet, balls_value.parquet (steps 1 to 3)
# Writes : report/charts/*.png (one file per chart, the win probability chart is outputs/02_calibration.png from step 2)
#
# Colours : pink for batters and blue for bowlers in every chart, grey for everything else.

# Importing Libraries
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
output_folder = os.path.join(folder, "outputs")
chart_folder = os.path.join(folder, "report", "charts")
os.makedirs(chart_folder, exist_ok=True)
keys = ['match_id', 'innings', 'innings_ball_num']
bat_colour, bowl_colour, grey = '#d6246e', '#254aa5', '#9aa0a6'

plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.titlesize': 11, 'axes.titleweight': 'bold', 'figure.dpi': 100})

# Loading Dataset
batters = pd.read_csv(os.path.join(output_folder, "05_batters.csv"), index_col=0)
bowlers = pd.read_csv(os.path.join(output_folder, "05_bowlers.csv"), index_col=0)
split_half = pd.read_csv(os.path.join(output_folder, "05_splithalf.csv"), index_col=0)
blend = pd.read_csv(os.path.join(output_folder, "05_blend.csv"), index_col=0)
batter_facts = pd.read_csv(os.path.join(output_folder, "06_batter_facts.csv"))
bowler_facts = pd.read_csv(os.path.join(output_folder, "06_bowler_facts.csv"))
rr_profile = pd.read_csv(os.path.join(output_folder, "06_rr_profile.csv"))


# Chart 1 : the two final top 10s, level in IPL terms with how often each player is in the top 10 when the matches are drawn again
fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
for ax, table, colour, title in [(axes[0], batters.head(10), bat_colour, 'Batters'), (axes[1], bowlers.head(10), bowl_colour, 'Bowlers')]:
    table = table.iloc[::-1]
    ax.barh(table['name'], table['ipl_level'], color=colour, alpha=0.9)
    for position, (value, share) in enumerate(zip(table['ipl_level'], table['top10_share'])):
        ax.text(value + 0.004, position, f"{share:.0%}", va='center', fontsize=9, color='#333333')
    ax.set_title(f"{title}: value per ball in IPL terms")
    ax.set_xlabel("Runs per ball above an average player")
    ax.set_xlim(0, table['ipl_level'].max() * 1.22)
fig.text(0.5, 0.005, "Number at the end of a bar = share of 1,000 redraws of the matches in which the player is in the top 10",
         ha='center', fontsize=9, color='#555555')
plt.tight_layout(rect=(0, 0.03, 1, 1))
plt.savefig(os.path.join(chart_folder, "01_final_lists.png"), dpi=170)
plt.close()


# Chart 2 : does pressure change an average player? 10 groups of pressure, both should stay near 0
balls = pd.read_parquet(os.path.join(output_folder, "balls_clean.parquet"), columns=keys + ['legal', 'comp_group'])
balls = balls.merge(pd.read_parquet(os.path.join(output_folder, "balls_pressure.parquet"), columns=keys + ['pressure']), on=keys)
balls = balls.merge(pd.read_parquet(os.path.join(output_folder, "balls_value.parquet"), columns=keys + ['batter_value', 'bowler_value']), on=keys)
balls = balls[balls['comp_group'] != 'Other T20']
balls['pressure_group'] = (balls['pressure'] // 10).clip(upper=9).astype(int)
fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), sharey=True)
for ax, source, value, colour, title in [
    (axes[0], balls[balls['legal']], 'batter_value', bat_colour, 'All batters'),
    (axes[1], balls, 'bowler_value', bowl_colour, 'All bowlers'),
]:
    per_group = source.groupby('pressure_group')[value].agg(['mean', 'std', 'size'])
    ax.errorbar(per_group.index, per_group['mean'], yerr=2 * per_group['std'] / np.sqrt(per_group['size']),
                color=colour, marker='o', capsize=3, linestyle='none')
    ax.axhline(0, color=grey, linestyle='--', linewidth=1)
    ax.set_xticks(range(10))
    ax.set_xticklabels([f"{10 * g}-{10 * g + 10}" for g in range(10)], fontsize=8)
    ax.set_xlabel("Pressure score of the ball")
    ax.set_title(title)
axes[0].set_ylabel("Average value per ball")
axes[0].set_ylim(-0.08, 0.08)
plt.tight_layout()
plt.savefig(os.path.join(chart_folder, "03_pressure_effect.png"), dpi=170)
plt.close()


# Chart 3 : split-half, does a number come back in the other half of the matches?
names = {'level': 'Level\n(all balls)', 'high pressure value': 'High pressure\nballs only', 'clutch': 'Clutch\n(high minus other)', 'consistency': 'Consistency'}
fig, ax = plt.subplots(figsize=(8.4, 3.8))
positions = np.arange(len(names))
for shift, group, colour, label in [(-0.2, 'batters', bat_colour, 'Batters'), (0.2, 'bowlers', bowl_colour, 'Bowlers')]:
    ax.bar(positions + shift, [split_half.loc[name, group + ' average'] for name in names], 0.38, color=colour, label=label)
    for position, name in zip(positions, names):
        value = split_half.loc[name, group + ' average']
        ax.text(position + shift, value + (0.012 if value >= 0 else -0.03), f"{value:+.2f}", ha='center', fontsize=9)
ax.axhline(0, color='#333333', linewidth=0.8)
ax.set_ylim(-0.31, 0.43)
ax.set_xticks(positions)
ax.set_xticklabels(list(names.values()))
ax.set_ylabel("Correlation between the two halves")
ax.set_title("Which numbers come back in the other half of the matches? (100 random splits)")
ax.legend(frameon=False)
plt.tight_layout()
plt.savefig(os.path.join(chart_folder, "04_split_half.png"), dpi=170)
plt.close()


# Chart 4 : rank confidence, the 15 best of each list
fig, axes = plt.subplots(1, 2, figsize=(11, 5.2))
for ax, table, colour, title in [(axes[0], batters.head(15), bat_colour, 'Batters'), (axes[1], bowlers.head(15), bowl_colour, 'Bowlers')]:
    table = table.iloc[::-1]
    ax.barh(table['name'], table['top10_share'], color=[colour if rank <= 10 else grey for rank in table['rank']])
    ax.axvline(0.5, color='#333333', linestyle=':', linewidth=1)
    ax.set_xlim(0, 1)
    ax.set_xlabel("Share of 1,000 redraws in which he is in the top 10")
    ax.set_title(f"{title}: places 1 to 15")
fig.text(0.5, 0.005, "Coloured = my top 10, grey = places 11 to 15", ha='center', fontsize=9, color='#555555')
plt.tight_layout(rect=(0, 0.03, 1, 1))
plt.savefig(os.path.join(chart_folder, "05_rank_confidence.png"), dpi=170)
plt.close()


# Chart 5 : IPL against T20I, the same player in both (ranked players with 300+ balls in both)
fig, axes = plt.subplots(1, 2, figsize=(10, 4.4))
for ax, source, id_column, value, table, colour, title in [
    (axes[0], balls[balls['legal']], None, 'batter_value', batters, bat_colour, 'Batters'),
    (axes[1], balls, None, 'bowler_value', bowlers, bowl_colour, 'Bowlers'),
]:
    clean = pd.read_parquet(os.path.join(output_folder, "balls_clean.parquet"), columns=keys + ['striker_id' if value == 'batter_value' else 'bowler_id'])
    player_column = 'striker_id' if value == 'batter_value' else 'bowler_id'
    source = source.merge(clean, on=keys)
    source = source[source[player_column].isin(table.index)]
    per_comp = source.groupby([player_column, 'comp_group'])[value].agg(['mean', 'size']).unstack()
    both = (per_comp[('size', 'IPL')] >= 300) & (per_comp[('size', 'T20I')] >= 300)
    x, y = per_comp.loc[both, ('mean', 'IPL')], per_comp.loc[both, ('mean', 'T20I')]
    ax.scatter(x, y, color=colour, alpha=0.8)
    limit = max(x.max(), y.max()) * 1.1
    ax.plot([-0.1, limit], [-0.1, limit], color=grey, linestyle='--', linewidth=1)
    ax.set_xlim(-0.1, limit)
    ax.set_ylim(-0.1, limit)
    ax.set_xlabel("Value per ball in the IPL")
    ax.set_ylabel("Value per ball in T20Is")
    ax.set_title(f"{title}: {both.sum()} players with 300+ balls in both")
    ax.text(0.04, 0.93, f"T20I minus IPL: {(y - x).mean():+.2f} per ball on average\ncorrelation {x.corr(y):.2f}", transform=ax.transAxes, fontsize=9, va='top')
plt.tight_layout()
plt.savefig(os.path.join(chart_folder, "06_ipl_vs_t20i.png"), dpi=170)
plt.close()


# Chart 6 : value by year for the 20 players. A year with fewer than 100 balls is left blank, the number is too noisy
years = list(range(2022, 2027))
fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
for ax, facts, title in [(axes[0], batter_facts, 'Batters'), (axes[1], bowler_facts, 'Bowlers')]:
    values = facts[[f'value {year}' for year in years]].values.astype(float)
    values[facts[[f'balls {year}' for year in years]].values < 100] = np.nan
    image = ax.imshow(values, cmap='RdBu', vmin=-0.6, vmax=0.6, aspect='auto')
    for row in range(values.shape[0]):
        for column in range(values.shape[1]):
            text = "" if np.isnan(values[row, column]) else f"{values[row, column]:+.2f}"
            ax.text(column, row, text, ha='center', va='center', fontsize=8.5,
                    color='white' if abs(values[row, column]) > 0.4 else 'black')
    ax.set_xticks(range(len(years)))
    ax.set_xticklabels(years)
    ax.set_yticks(range(len(facts)))
    ax.set_yticklabels(facts['name'])
    ax.set_title(f"{title}: value per ball by year")
    ax.spines[:].set_visible(False)
fig.text(0.5, 0.005, "Blue = better than an average player, red = worse. Blank = fewer than 100 balls that year. 2026 is the IPL season only.",
         ha='center', fontsize=9, color='#555555')
plt.tight_layout(rect=(0, 0.03, 1, 1))
plt.savefig(os.path.join(chart_folder, "07_value_by_year.png"), dpi=170)
plt.close()


# Chart 7 : the Rajasthan Royals in IPL 2025 and 2026 against the other nine teams, by phase and by type of the other side
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharex=True)
for ax, side, colour, title in [(axes[0], 'batting', bat_colour, 'Rajasthan Royals batting'), (axes[1], 'bowling', bowl_colour, 'Rajasthan Royals bowling')]:
    part = rr_profile[(rr_profile['side'] == side) & (rr_profile['split'] != 'all balls')].iloc[::-1]
    ax.barh(part['split'], part['gap'], xerr=2 * part['rr_se'], color=colour, alpha=0.85, error_kw={'ecolor': '#333333', 'capsize': 3})
    ax.axvline(0, color='#333333', linewidth=0.8)
    ax.set_title(title)
    ax.set_xlabel("Value per ball minus the other teams (right = better)")
fig.text(0.5, 0.005, "Black line = how far luck alone can move the number (2 standard errors). 30 matches, so most bars are hints and not results.",
         ha='center', fontsize=9, color='#555555')
plt.tight_layout(rect=(0, 0.03, 1, 1))
plt.savefig(os.path.join(chart_folder, "08_rr_profile.png"), dpi=170)
plt.close()

print("charts saved in", chart_folder)
for name in sorted(os.listdir(chart_folder)):
    print("  ", name)
