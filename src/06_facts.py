# Step 6a : Facts for the report, for the 20 players in the final lists and for the Rajasthan Royals themselves
#
# Run from the project folder : python src/06_facts.py
# Reads  : outputs/balls_clean.parquet, balls_pressure.parquet, balls_value.parquet (steps 1 to 3)
#          outputs/05_batters.csv, outputs/05_bowlers.csv (final lists from step 5)
# Writes : outputs/06_batter_facts.csv and outputs/06_bowler_facts.csv (one row per player of the final lists)
#          outputs/06_rr_profile.csv (how the Rajasthan Royals did in IPL 2025 and 2026, by phase and bowler or batter type)
#          outputs/06_rr_players.csv (who batted and bowled for them in IPL 2026)
#          outputs/06_checks.txt
#
# What I do:
# 1. For every player of the final lists : value per ball (runs above an average player in the same situation, step 3)
#    split by phase, by type of the other side (pace or spin for batters, left or right hand for bowlers),
#    by innings, by competition and by year. The report uses these to say where the player would help.
# 2. The same split for the Rajasthan Royals as a team, to see where the squad is strong and where it is not.
# These are plain averages with the balls behind each number. They are not shrunk, so a number with few balls is a hint and not a result.

# Importing Libraries
import os
import numpy as np
import pandas as pd

folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
output_folder = os.path.join(folder, "outputs")
keys = ['match_id', 'innings', 'innings_ball_num']
rr_team_id = 3
phase_names = {0: 'overs 1-6', 1: 'overs 7-16', 2: 'overs 17-20'}

# Loading Dataset (the 3 tables from steps 1 to 3, one row per ball)
balls = pd.read_parquet(os.path.join(output_folder, "balls_clean.parquet"), columns=keys + [
    'striker_id', 'striker_name', 'bowler_id', 'bowler_name', 'batting_team_id', 'bowling_team_id', 'batting_type',
    'bowling_type', 'pace_or_spin', 'batting_order', 'bat_runs', 'bowler_runs', 'bowler_wicket', 'is_four', 'is_six',
    'is_wicket', 'legal', 'comp_group', 'match_date'])
balls = balls.merge(pd.read_parquet(os.path.join(output_folder, "balls_pressure.parquet"), columns=keys + ['pressure']), on=keys)
balls = balls.merge(pd.read_parquet(os.path.join(output_folder, "balls_value.parquet"), columns=keys + ['phase', 'batter_value', 'bowler_value']), on=keys)
balls['year'] = pd.to_datetime(balls['match_date']).dt.year
balls['high'] = balls['pressure'] >= 80
balls = balls[balls['comp_group'] != 'Other T20']

batters = pd.read_csv(os.path.join(output_folder, "05_batters.csv"), index_col=0)
bowlers = pd.read_csv(os.path.join(output_folder, "05_bowlers.csv"), index_col=0)
checks = []


# Average value per ball and the number of balls behind it, for a set of balls
def value_and_balls(part, value):
    return part[value].mean() if len(part) else np.nan, len(part)


# Batters : legal balls only (a wide is not a ball faced)
faced = balls[balls['legal']]
rows = []
for player_id, row in batters.head(10).iterrows():
    mine = faced[faced['striker_id'] == player_id]
    fact = {'rank': row['rank'], 'name': row['name'], 'team': row['team'], 'hand': mine['batting_type'].mode()[0],
            'usual_position': mine['batting_order'].median(), 'balls': len(mine),
            'ipl_level': row['ipl_level'], 'top10_share': row['top10_share']}
    fact['strike_rate'] = 100 * mine['bat_runs'].sum() / len(mine)
    fact['boundary_share'] = (mine['is_four'].sum() + mine['is_six'].sum()) / len(mine)
    fact['out_every_balls'] = len(mine) / max(mine['is_wicket'].sum(), 1)
    for phase, phase_name in phase_names.items():
        fact[f'value {phase_name}'], fact[f'balls {phase_name}'] = value_and_balls(mine[mine['phase'] == phase], 'batter_value')
    for kind in ['Pace', 'Spin']:
        fact[f'value vs {kind}'], fact[f'balls vs {kind}'] = value_and_balls(mine[mine['pace_or_spin'] == kind], 'batter_value')
    for innings in [1, 2]:
        fact[f'value innings {innings}'], fact[f'balls innings {innings}'] = value_and_balls(mine[mine['innings'] == innings], 'batter_value')
    for comp in ['IPL', 'T20I']:
        fact[f'value {comp}'], fact[f'balls {comp}'] = value_and_balls(mine[mine['comp_group'] == comp], 'batter_value')
    fact['value high pressure'], fact['balls high pressure'] = value_and_balls(mine[mine['high']], 'batter_value')
    for year in range(2022, 2027):
        fact[f'value {year}'], fact[f'balls {year}'] = value_and_balls(mine[mine['year'] == year], 'batter_value')
    rows.append(fact)
batter_facts = pd.DataFrame(rows)
batter_facts.round(4).to_csv(os.path.join(output_folder, "06_batter_facts.csv"), index=False)

# Bowlers : every delivery
rows = []
for player_id, row in bowlers.head(10).iterrows():
    mine = balls[balls['bowler_id'] == player_id]
    legal = mine[mine['legal']]
    fact = {'rank': row['rank'], 'name': row['name'], 'team': row['team'], 'type': mine['bowling_type'].mode()[0],
            'pace_or_spin': mine['pace_or_spin'].mode()[0], 'balls': len(mine),
            'ipl_level': row['ipl_level'], 'top10_share': row['top10_share']}
    fact['economy'] = 6 * mine['bowler_runs'].sum() / len(legal)
    fact['wicket_every_balls'] = len(legal) / max(mine['bowler_wicket'].sum(), 1)
    fact['dot_share'] = ((legal['bowler_runs'] == 0).sum()) / len(legal)
    for phase, phase_name in phase_names.items():
        fact[f'value {phase_name}'], fact[f'balls {phase_name}'] = value_and_balls(mine[mine['phase'] == phase], 'bowler_value')
    for hand in ['RHB', 'LHB']:
        fact[f'value vs {hand}'], fact[f'balls vs {hand}'] = value_and_balls(mine[mine['batting_type'] == hand], 'bowler_value')
    for innings in [1, 2]:
        fact[f'value innings {innings}'], fact[f'balls innings {innings}'] = value_and_balls(mine[mine['innings'] == innings], 'bowler_value')
    for comp in ['IPL', 'T20I']:
        fact[f'value {comp}'], fact[f'balls {comp}'] = value_and_balls(mine[mine['comp_group'] == comp], 'bowler_value')
    fact['value high pressure'], fact['balls high pressure'] = value_and_balls(mine[mine['high']], 'bowler_value')
    for year in range(2022, 2027):
        fact[f'value {year}'], fact[f'balls {year}'] = value_and_balls(mine[mine['year'] == year], 'bowler_value')
    rows.append(fact)
bowler_facts = pd.DataFrame(rows)
bowler_facts.round(4).to_csv(os.path.join(output_folder, "06_bowler_facts.csv"), index=False)

# Check 1 : the balls of a player split by phase, by innings and by competition must each add up to all of his balls
checks.append("Check 1 : the splits of every player add up to his balls")
for label, table in [('batters', batter_facts), ('bowlers', bowler_facts)]:
    by_phase = table[[f'balls {name}' for name in phase_names.values()]].sum(axis=1)
    by_innings = table[['balls innings 1', 'balls innings 2']].sum(axis=1)
    by_comp = table[['balls IPL', 'balls T20I']].sum(axis=1)
    by_year = table[[f'balls {year}' for year in range(2022, 2027)]].sum(axis=1)
    checks.append(f"   {label}: phase {bool((by_phase == table['balls']).all())}, innings {bool((by_innings == table['balls']).all())}, "
                  f"competition {bool((by_comp == table['balls']).all())}, year {bool((by_year == table['balls']).all())}")

# Check 2 : the value over all balls of a player must be his raw level from step 4
checks.append("Check 2 : value over all balls of a player against the raw level in 04_batters.csv and 04_bowlers.csv")
for label, group, source, id_column, value in [('batters', batters, faced, 'striker_id', 'batter_value'), ('bowlers', bowlers, balls, 'bowler_id', 'bowler_value')]:
    step4 = pd.read_csv(os.path.join(output_folder, f"04_{label}.csv"), index_col=0)
    mine = source[source[id_column].isin(group.head(10).index)].groupby(id_column)[value].mean()
    checks.append(f"   {label}: biggest gap {(mine - step4.loc[mine.index, 'raw_level']).abs().max():.5f}")


# The Rajasthan Royals in IPL 2025 and 2026
recent = balls[(balls['comp_group'] == 'IPL') & (balls['year'] >= 2025)]
rr_batting = recent[(recent['batting_team_id'] == rr_team_id) & recent['legal']]
rr_bowling = recent[recent['bowling_team_id'] == rr_team_id]
matches_played = recent[(recent['batting_team_id'] == rr_team_id) | (recent['bowling_team_id'] == rr_team_id)]['match_id'].nunique()
# The same for every other team, to see where the Rajasthan Royals stand
other_batting = recent[(recent['batting_team_id'] != rr_team_id) & recent['legal']]
other_bowling = recent[recent['bowling_team_id'] != rr_team_id]

profile = []
for side, rr_part, other_part, value in [('batting', rr_batting, other_batting, 'batter_value'), ('bowling', rr_bowling, other_bowling, 'bowler_value')]:
    kind_column, kinds = ('pace_or_spin', ['Pace', 'Spin']) if side == 'batting' else ('batting_type', ['RHB', 'LHB'])
    splits = [('all balls', slice(None), None)]
    splits += [(phase_name, 'phase', phase) for phase, phase_name in phase_names.items()]
    splits += [(f"against {kind}" if side == 'batting' else f"to {kind}", kind_column, kind) for kind in kinds]
    splits += [('high pressure', 'high', True)]
    for split_name, column, wanted in splits:
        if column == slice(None):
            rr_rows, other_rows = rr_part, other_part
        else:
            rr_rows, other_rows = rr_part[rr_part[column] == wanted], other_part[other_part[column] == wanted]
        profile.append({'side': side, 'split': split_name, 'rr_balls': len(rr_rows), 'rr_value': rr_rows[value].mean(),
                        'other_teams_value': other_rows[value].mean(),
                        'rr_se': rr_rows[value].std() / np.sqrt(len(rr_rows))})
profile = pd.DataFrame(profile)
profile['gap'] = profile['rr_value'] - profile['other_teams_value']
# rr_se = how far luck alone can move the Rajasthan Royals number (balls of one match are not independent,
# so the real figure is about 10% bigger). A gap smaller than twice rr_se is a hint and not a result.
profile.round(4).to_csv(os.path.join(output_folder, "06_rr_profile.csv"), index=False)

# Who batted and bowled for them in IPL 2026
latest = recent[recent['year'] == 2026]
rr_2026_batters = latest[(latest['batting_team_id'] == rr_team_id) & latest['legal']].groupby('striker_name').agg(
    balls=('batter_value', 'size'), value=('batter_value', 'mean'), position=('batting_order', 'median'))
rr_2026_bowlers = latest[latest['bowling_team_id'] == rr_team_id].groupby('bowler_name').agg(
    balls=('bowler_value', 'size'), value=('bowler_value', 'mean'), kind=('bowling_type', lambda x: x.mode()[0]))
players = pd.concat([rr_2026_batters.assign(role='batter'), rr_2026_bowlers.assign(role='bowler')]).reset_index(names='name')
players = players[players['balls'] >= 60].sort_values(['role', 'balls'], ascending=[True, False])
players.round(4).to_csv(os.path.join(output_folder, "06_rr_players.csv"), index=False)

checks.append(f"The Rajasthan Royals in IPL 2025 and 2026 : {matches_played} matches, {len(rr_batting)} legal balls batted, {len(rr_bowling)} balls bowled")
checks.append("   value per ball against the other teams, by split (the average of all teams is near 0):")
for _, line in profile.iterrows():
    checks.append(f"   {line['side']:8s} {line['split']:16s} {line['rr_balls']:6d} balls   RR {line['rr_value']:+.3f}   others {line['other_teams_value']:+.3f}   gap {line['gap']:+.3f}   (luck alone moves it by about {line['rr_se']:.3f})")

with open(os.path.join(output_folder, "06_checks.txt"), "w") as file:
    file.write("\n".join(checks) + "\n")
print("\n".join(checks))
