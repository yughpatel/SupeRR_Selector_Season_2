# Step 3 : Comparing every ball with what an average player would do
#
# Run from the project folder : python src/03_expected.py
# Reads  : outputs/balls_clean.parquet (01_clean.py), outputs/balls_pressure.parquet (02_pressure.py, for the folds)
# Writes : outputs/balls_value.parquet (one row per ball, keys + expected outcomes + value of the ball)
#          outputs/03_checks.txt (checks to see if the values can be trusted)
#
# What I do:
# 1. Expected outcomes : a LightGBM model says how many runs and how likely a wicket on this ball
#    for an average player, from the over, wickets down, innings, pace or spin, competition
#    and the strength of the opponent. It never sees a player name or id.
#    Opponent strength = how many runs the team usually gives or scores per ball and how often it loses
#    or takes a wicket, measured on all its OTHER matches (not the match being scored)
# 2. Wicket cost : how many runs a wicket costs in each phase of an innings, measured from the data
# 3. Value of a ball = actual minus expected, runs and wickets on one scale (runs)
#    batter : runs above expected, minus the wicket cost if he got out more than expected
#    bowler : runs saved against expected, plus the wicket cost if he took a wicket

# Importing Libraries
import os
import numpy as np
import pandas as pd
import lightgbm as lgb

folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
output_folder = os.path.join(folder, "outputs")
keys = ['match_id', 'innings', 'innings_ball_num']

# Loading Dataset
balls = pd.read_parquet(os.path.join(output_folder, "balls_clean.parquet"))
folds = pd.read_parquet(os.path.join(output_folder, "balls_pressure.parquet"), columns=keys + ['fold'])
balls = balls.merge(folds, on=keys, how='left', validate='one_to_one')

balls['over_number'] = (balls['balls_bowled'] // 6).clip(upper=19)
balls['spin'] = (balls['pace_or_spin'] == 'Spin').astype(int)
balls['comp_code'] = balls['comp_group'].map({'IPL': 0, 'T20I': 1, 'Other T20': 2})

# 3 phases of an innings, by balls bowled
phase_names = ['overs 1-6', 'overs 7-16', 'overs 17-20']
balls['phase'] = pd.cut(balls['balls_bowled'], [-1, 35, 95, 120], labels=[0, 1, 2]).astype(int)


# Strength of every team, from its other matches
# For a team bowling : runs it gives per ball and wickets it takes per ball
# For a team batting : runs it scores per ball and wickets it loses per ball
# The current match is left out, so a big innings in this match cannot lift the baseline it is compared with.
# Teams with few balls are pulled towards the competition average (like 600 extra balls at that average)
k = 600
for side, team_column, runs_column, prefix in [
    ('bowl', 'bowling_team_id', 'bowler_runs', 'bowl'),
    ('bat', 'batting_team_id', 'total_runs', 'bat'),
]:
    per_match = balls.groupby(['match_id', team_column]).agg(
        runs=(runs_column, 'sum'), deliveries=(runs_column, 'size'), wickets=('is_wicket', 'sum'),
    ).reset_index()
    for column in ['runs', 'deliveries', 'wickets']:
        per_match['other_' + column] = per_match.groupby(team_column)[column].transform('sum') - per_match[column]
    average = balls.groupby('comp_group').agg(
        avg_runs=(runs_column, 'mean'), avg_wickets=('is_wicket', 'mean'),
    )
    per_match = per_match.merge(balls[['match_id', 'comp_group']].drop_duplicates('match_id'), on='match_id')
    per_match = per_match.merge(average, left_on='comp_group', right_index=True)
    per_match[prefix + '_runs_rate'] = (per_match['other_runs'] + k * per_match['avg_runs']) / (per_match['other_deliveries'] + k)
    per_match[prefix + '_wicket_rate'] = (per_match['other_wickets'] + k * per_match['avg_wickets']) / (per_match['other_deliveries'] + k)
    balls = balls.merge(
        per_match[['match_id', team_column, prefix + '_runs_rate', prefix + '_wicket_rate']],
        on=['match_id', team_column], how='left', validate='many_to_one',
    )


# Expected outcomes, 4 models
# A batter is compared with an average batter against the SAME opponent (the bowling team),
# a bowler with an average bowler against the batting team. Only the opponent is an input,
# the player's own team is not, because that would hide the player's own quality.
# Batters are judged on legal balls (a wide is not a ball faced), bowlers on every delivery.
# Every match is scored by a model that did not train on that match (same 5 folds as step 2).
# Pressure and the target are NOT inputs, so the expected value is for a normal ball in that situation
base_features = ['innings', 'over_number', 'wickets_before', 'spin', 'comp_code']
configs = [
    {'name': 'exp_bat_runs', 'rows': balls['legal'], 'target': balls['bat_runs'], 'opponent': 'bowl', 'kind': 'runs'},
    {'name': 'exp_bat_out', 'rows': balls['legal'], 'target': balls['striker_out'], 'opponent': 'bowl', 'kind': 'wicket'},
    {'name': 'exp_bowl_runs', 'rows': pd.Series(True, index=balls.index), 'target': balls['bowler_runs'], 'opponent': 'bat', 'kind': 'runs'},
    {'name': 'exp_bowl_wicket', 'rows': pd.Series(True, index=balls.index), 'target': balls['bowler_wicket'], 'opponent': 'bat', 'kind': 'wicket'},
]

for config in configs:
    data = balls[base_features].copy()
    data['opponent_runs_rate'] = balls[config['opponent'] + '_runs_rate']
    data['opponent_wicket_rate'] = balls[config['opponent'] + '_wicket_rate']
    target = config['target'].astype(float)
    in_population = config['rows'].values

    expected = np.full(len(balls), np.nan)
    for fold in range(5):
        train = in_population & (balls['fold'] != fold).values
        test = in_population & (balls['fold'] == fold).values
        if config['kind'] == 'runs':
            model = lgb.LGBMRegressor(n_estimators=200, learning_rate=0.05, num_leaves=15, min_child_samples=500, random_state=42, verbose=-1)
            model.fit(data[train], target[train])
            expected[test] = model.predict(data[test])
        else:
            model = lgb.LGBMClassifier(n_estimators=200, learning_rate=0.05, num_leaves=15, min_child_samples=500, random_state=42, verbose=-1)
            model.fit(data[train], target[train].astype(int))
            expected[test] = model.predict_proba(data[test])[:, 1]
    balls[config['name']] = expected


# Wicket cost : how many runs a wicket costs in each phase
# Runs scored from this ball to the end of the first innings, against wickets already lost.
# For each phase a straight line fit of: remaining runs = a + b * balls bowled + c * wickets lost
# c (with the sign flipped) is the number of runs one more wicket costs in that phase.
# Only first innings of complete innings, because a chase stops when the target is reached
first = balls[(balls['innings'] == 1) & balls['inn1_complete']].copy()
first['remaining_runs'] = first['final_1'] - first['score_before']
wicket_cost = {}
for phase in [0, 1, 2]:
    part = first[first['phase'] == phase]
    x = np.column_stack([np.ones(len(part)), part['balls_bowled'], part['wickets_before']])
    coefficients = np.linalg.lstsq(x, part['remaining_runs'].values, rcond=None)[0]
    wicket_cost[phase] = -coefficients[2]
balls['wicket_cost'] = balls['phase'].map(wicket_cost)


# Value of every ball (positive = good for the player), runs and wickets on one scale (runs)
balls['batter_value'] = (balls['bat_runs'] - balls['exp_bat_runs']) \
    - balls['wicket_cost'] * (balls['striker_out'].astype(float) - balls['exp_bat_out'])
balls['bowler_value'] = (balls['exp_bowl_runs'] - balls['bowler_runs']) \
    + balls['wicket_cost'] * (balls['bowler_wicket'].astype(float) - balls['exp_bowl_wicket'])
balls.loc[~balls['legal'], 'batter_value'] = np.nan


# Saving the value table (keys + new columns, step 4 merges it with the other tables)
save_columns = keys + [
    'fold', 'phase', 'wicket_cost', 'exp_bat_runs', 'exp_bat_out', 'exp_bowl_runs',
    'exp_bowl_wicket', 'batter_value', 'bowler_value',
]
balls[save_columns].to_parquet(os.path.join(output_folder, "balls_value.parquet"), index=False)


# Checks
checks = []
legal = balls[balls['legal']]
checks.append("STEP 3 CHECKS")
checks.append(f"balls: {len(balls):,}   legal balls (batters): {len(legal):,}")
checks.append("missing values (batter columns counted on legal balls only): "
              f"exp_bat_runs {int(legal['exp_bat_runs'].isna().sum())}, exp_bat_out {int(legal['exp_bat_out'].isna().sum())}, "
              f"batter_value {int(legal['batter_value'].isna().sum())}, exp_bowl_runs {int(balls['exp_bowl_runs'].isna().sum())}, "
              f"exp_bowl_wicket {int(balls['exp_bowl_wicket'].isna().sum())}, bowler_value {int(balls['bowler_value'].isna().sum())}")
checks.append("")

# Check 1 : are the expected outcomes close to what really happened, and better than a flat average?
checks.append("1. Expected outcomes against what happened (every ball scored by a model that did not train on that match):")
for name, actual, population in [
    ('exp_bat_runs', balls['bat_runs'], legal.index),
    ('exp_bowl_runs', balls['bowler_runs'], balls.index),
]:
    a = actual[population].astype(float)
    e = balls.loc[population, name]
    r2 = 1 - ((a - e) ** 2).sum() / ((a - a.mean()) ** 2).sum()
    checks.append(f"   {name}: average expected {e.mean():.4f}   average actual {a.mean():.4f}   share of variance explained {r2:.3f}")
for name, actual, population in [
    ('exp_bat_out', balls['striker_out'], legal.index),
    ('exp_bowl_wicket', balls['bowler_wicket'], balls.index),
]:
    a = actual[population].astype(float)
    e = balls.loc[population, name]
    brier = ((a - e) ** 2).mean()
    flat = a.mean() * (1 - a.mean())
    checks.append(f"   {name}: average expected {e.mean():.4f}   average actual {a.mean():.4f}   Brier {brier:.5f} against {flat:.5f} for a flat rate")
checks.append("")

# Check 2 : what a wicket costs
checks.append("2. Runs a wicket costs in each phase (first innings, complete innings):")
for phase in [0, 1, 2]:
    checks.append(f"   {phase_names[phase]}: {wicket_cost[phase]:.1f} runs")
checks.append("")

# Check 3 : the average value over all players should be near zero in every phase
checks.append("3. Average value per ball over all players, should be near 0 (runs per ball, std of a single ball in brackets):")
for phase in [0, 1, 2]:
    bat = legal.loc[legal['phase'] == phase, 'batter_value']
    bowl = balls.loc[balls['phase'] == phase, 'bowler_value']
    checks.append(f"   {phase_names[phase]}: batters {bat.mean():+.4f} ({bat.std():.2f})   bowlers {bowl.mean():+.4f} ({bowl.std():.2f})")
for innings in [1, 2]:
    bat = legal.loc[legal['innings'] == innings, 'batter_value']
    bowl = balls.loc[balls['innings'] == innings, 'bowler_value']
    checks.append(f"   innings {innings}: batters {bat.mean():+.4f}   bowlers {bowl.mean():+.4f}")
for group in ['IPL', 'T20I', 'Other T20']:
    bat = legal.loc[legal['comp_group'] == group, 'batter_value']
    bowl = balls.loc[balls['comp_group'] == group, 'bowler_value']
    checks.append(f"   {group}: batters {bat.mean():+.4f}   bowlers {bowl.mean():+.4f}")
for kind in ['Pace', 'Spin']:
    bowl = balls.loc[balls['pace_or_spin'] == kind, 'bowler_value']
    checks.append(f"   {kind} bowlers: {bowl.mean():+.4f}")
order_group = pd.cut(legal['batting_order'], [0, 2, 4, 7, 13], labels=['order 1-2', 'order 3-4', 'order 5-7', 'order 8-13'])
by_order = legal.groupby(order_group, observed=True)['batter_value'].mean()
checks.append("   by batting order (role) : " + "   ".join(f"{name} {value:+.4f}" for name, value in by_order.items()))
checks.append("")

# Check 4 : opponent strength does something sensible (a team that usually gives more runs -> more expected runs for the batter)
# Looked at inside one competition, because the IPL and T20I teams are different pools
checks.append("4. Opponent strength, runs per legal ball for batters, by how many runs the bowling team usually gives (3 equal groups of balls, inside one competition):")
for group in ['T20I', 'IPL']:
    part = legal[legal['comp_group'] == group]
    tercile = pd.qcut(part['bowl_runs_rate'], 3, duplicates='drop')
    table = part.groupby(tercile, observed=True).agg(usual=('bowl_runs_rate', 'mean'), expected=('exp_bat_runs', 'mean'), actual=('bat_runs', 'mean'))
    for _, row in table.iterrows():
        checks.append(f"   {group}: bowling team usually gives {row['usual']:.3f} per ball   expected {row['expected']:.3f}   actual {row['actual']:.3f}")

with open(os.path.join(output_folder, "03_checks.txt"), "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(checks) + "\n")

for line in checks:
    print(line)

print(f"\nSaved {len(balls):,} rows to outputs/balls_value.parquet")
