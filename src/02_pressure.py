# Step 2 : Giving every ball a pressure score
#
# Run from the project folder : python src/02_pressure.py
# Reads  : outputs/balls_clean.parquet (made by 01_clean.py)
# Writes : outputs/balls_pressure.parquet (one row per ball, keys + pressure columns)
#          outputs/02_checks.txt (checks to see if the scores can be trusted)
#          outputs/02_calibration.png (chart for the report)
#
# What I do:
# 1. Win probability model (LightGBM) : the chance the batting team wins, from the state of the ball
# 2. Leverage : how much the next ball can move the win probability, on average
#    Every possible outcome (0 to 6 runs, wicket) is weighted by how often it happens in that over
#    A big number means this ball matters a lot. Pressure = leverage as a percentile (0 to 100)
#    I also keep the simple gap (win prob after a four minus after a wicket) to compare with
# 3. Test 4 "felt" signals the scoreboard misses, keep only the ones that change the results
# 4. A simple rule based index as a backup, to compare with in step 5

# Importing Libraries
import os
import numpy as np
import pandas as pd
import lightgbm as lgb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
output_folder = os.path.join(folder, "outputs")

# Loading Dataset
balls = pd.read_parquet(os.path.join(output_folder, "balls_clean.parquet"))


# How often each outcome happens, by innings and over (outcomes : 0 to 6 runs, 7 = wicket)
# Every delivery counts here, wides and no balls too, to keep it simple
# The shares for a fold are counted on the other 4 folds only (done inside the loop below)
balls['outcome'] = np.where(balls['is_wicket'], 7, balls['total_runs'].clip(upper=6))


# Win probability model + leverage
# Each innings gets its own model. I force the model to follow cricket logic:
# more wickets in hand or more balls left never lowers the chance,
# more runs scored (innings 1) never lowers it, more runs needed (innings 2) never raises it
# Only clean matches (clear winner, full innings) are used for training, but every match is scored
win_prob = np.full(len(balls), np.nan)
win_prob_after = np.full((len(balls), 8), np.nan)
outcome_prob = np.full((len(balls), 8), np.nan)

for innings in [1, 2]:
    if innings == 1:
        features = ['score_before', 'wickets_left', 'balls_left', 'comp_code']
        constraints = [1, 1, 1, 0]
    else:
        features = ['runs_needed', 'wickets_left', 'balls_left', 'comp_code']
        constraints = [-1, 1, 1, 0]

    for fold in range(5):
        train = balls[(balls['innings'] == innings) & balls['clean_match'] & (balls['fold'] != fold)]
        model = lgb.LGBMClassifier(
            n_estimators=300, learning_rate=0.05, num_leaves=15, min_child_samples=500,
            monotone_constraints=constraints, random_state=42, verbose=-1,
        )
        model.fit(train[features], train['batting_won'].astype(int))

        rows = ((balls['innings'] == innings) & (balls['fold'] == fold)).values
        part = balls.loc[rows]
        win_prob[rows] = model.predict_proba(part[features])[:, 1]

        # How likely each outcome is for these balls, counted on the matches outside this fold
        other_folds = balls[balls['fold'] != fold]
        outcome_share = pd.crosstab([other_folds['innings'], other_folds['over_number']], other_folds['outcome'], normalize='index')
        over_index = pd.MultiIndex.from_arrays([part['innings'], part['over_number']])
        outcome_prob[rows] = outcome_share.reindex(over_index).values

        # Win probability after the next ball, for each of the 8 outcomes
        # Every ball is treated as a legal ball here (a wide does not use a ball, small effect)
        for outcome in range(8):
            after = part[features].copy()
            after['balls_left'] = part['balls_left'] - 1
            if outcome == 7:
                after['wickets_left'] = part['wickets_left'] - 1
            elif innings == 1:
                after['score_before'] = part['score_before'] + outcome
            else:
                after['runs_needed'] = part['runs_needed'] - outcome

            # The model never saw a state with 0 balls or 0 wickets left, so I keep the inputs at 1
            clipped = after.copy()
            clipped['balls_left'] = clipped['balls_left'].clip(lower=1)
            clipped['wickets_left'] = clipped['wickets_left'].clip(lower=1)
            if innings == 2:
                clipped['runs_needed'] = clipped['runs_needed'].clip(lower=1)
            p = model.predict_proba(clipped)[:, 1]

            # In a chase the end of the game is known : target reached = win, out of balls or wickets = loss
            if innings == 2:
                p = np.where(after['wickets_left'] == 0, 0.0, p)
                p = np.where(after['balls_left'] == 0, 0.0, p)
                p = np.where(after['runs_needed'] <= 0, 1.0, p)

            win_prob_after[rows, outcome] = p

balls['win_prob'] = win_prob

# Leverage = average size of the move in win probability over the next ball
swing = np.abs(win_prob_after - win_prob[:, None])
balls['leverage'] = (outcome_prob * swing).sum(axis=1)
# Pressure = leverage as a percentile (0 to 100)
balls['pressure'] = balls['leverage'].rank(pct=True) * 100


# Felt signals (things the scoreboard misses)
keys = [balls['match_id'], balls['innings']]

# Signal 1 : 3 or more dot balls in a row just before this ball
balls['dot'] = balls['total_runs'] == 0
run_id = (~balls['dot']).groupby(keys).cumsum()
run_length = balls['dot'].astype(int).groupby([balls['match_id'], balls['innings'], run_id]).cumsum()
balls['dots_before'] = run_length.groupby(keys).shift(1).fillna(0)
balls['sig_dots'] = balls['dots_before'] >= 3

# Signal 2 : 2 or more wickets in the last 18 balls (3 overs)
wickets_so_far = balls['is_wicket'].astype(int).groupby(keys).cumsum() - balls['is_wicket'].astype(int)
wickets_18_ago = wickets_so_far.groupby(keys).shift(18).fillna(0)
balls['wickets_last_18'] = wickets_so_far - wickets_18_ago
balls['sig_wickets'] = balls['wickets_last_18'] >= 2

# Signal 3 : the batter is in his first 10 balls
faced_so_far = balls['legal'].astype(int).groupby([balls['match_id'], balls['striker_id']]).cumsum() - balls['legal'].astype(int)
balls['sig_new_batter'] = faced_so_far < 10

# Signal 4 : knockout match
balls['sig_knockout'] = balls['knock_out'] == 1

signals = ['sig_dots', 'sig_wickets', 'sig_new_batter', 'sig_knockout']

# Test : does the signal change runs per ball or the chance of a wicket,
# once the state of the match is held fixed (over, wickets down, innings, competition)?
# Plain regression on legal balls, standard errors grouped by match
legal = balls[balls['legal']].reset_index(drop=True)
over_number = (legal['balls_bowled'] // 6).astype(int)
x = pd.concat([
    legal[signals].astype(float),
    (legal['innings'] == 2).astype(float).rename('innings_2'),
    pd.get_dummies(legal['comp_group'], prefix='comp', drop_first=True).astype(float),
    pd.get_dummies(over_number, prefix='over', drop_first=True).astype(float),
    pd.get_dummies(legal['wickets_before'], prefix='wkts', drop_first=True).astype(float),
], axis=1)
x.insert(0, 'const', 1.0)
x_values = x.values

signal_results = {}
for outcome in ['total_runs', 'is_wicket']:
    y = legal[outcome].astype(float).values
    xtx_inv = np.linalg.inv(x_values.T @ x_values)
    beta = xtx_inv @ (x_values.T @ y)
    resid = y - x_values @ beta
    scores = pd.DataFrame(x_values * resid[:, None]).groupby(legal['match_id'].values).sum().values
    n_groups = scores.shape[0]
    variance = xtx_inv @ (scores.T @ scores) @ xtx_inv * n_groups / (n_groups - 1)
    std_error = np.sqrt(np.diag(variance))
    for signal in signals:
        i = list(x.columns).index(signal)
        signal_results[(signal, outcome)] = (beta[i], beta[i] / std_error[i])

# Keep a signal if the effect is clearly not noise (t of 3 or more) and big enough to matter
# (0.05 runs per ball or 1 percentage point of wicket chance), for runs or for wickets
kept = []
for signal in signals:
    runs_effect, runs_t = signal_results[(signal, 'total_runs')]
    wicket_effect, wicket_t = signal_results[(signal, 'is_wicket')]
    if (abs(runs_t) >= 3 and abs(runs_effect) >= 0.05) or (abs(wicket_t) >= 3 and abs(wicket_effect) >= 0.01):
        kept.append(signal)
balls['felt_count'] = balls[kept].astype(int).sum(axis=1) if kept else 0


# Rule based index (backup) from the required rate, wickets in hand and balls left, 0 to 100
# A chase is under pressure when the required rate is close to what the batters can manage,
# and the closer to the end, the more it counts
# "What they can manage" = league scoring rate, lowered when wickets are lost (square root of wickets in hand)
# League scoring rate is the average runs per over over all legal balls
league_rate = balls.loc[balls['legal'], 'total_runs'].mean() * 6
manageable_rate = league_rate * np.sqrt(balls['wickets_left'] / 10)
closeness = (1 - (balls['required_rate'] - manageable_rate).abs() / 6).clip(0, 1)
used = 1 - balls['balls_left'] / balls['max_balls']
balls['rule_index'] = 100 * closeness * used
# No target in the first innings, so only the wickets lost and the balls used count, and it is capped at 50
balls.loc[balls['innings'] == 1, 'rule_index'] = 50 * (1 - balls['wickets_left'] / 10) * used


# Saving the pressure table (keys + new columns, step 3 merges it with the clean table)
save_columns = [
    'match_id', 'innings', 'innings_ball_num', 'win_prob', 'leverage', 'pressure', 'rule_index', 'sig_dots', 'sig_wickets', 'sig_new_batter',
    'sig_knockout', 'felt_count',
]
balls[save_columns].to_parquet(os.path.join(output_folder, "balls_pressure.parquet"), index=False)


# Checks
checks = []
checks.append("STEP 2 CHECKS")
checks.append(f"balls scored: {len(balls):,}   missing win_prob: {int(balls['win_prob'].isna().sum())}"
              f"   missing leverage: {int(balls['leverage'].isna().sum())}")
checks.append("")

# Check 1 : is the win probability model honest? (clean matches, every ball scored by a model that did not see the match)
clean = balls[balls['clean_match']]
actual = clean['batting_won']
base_rate = actual.mean()
brier = lambda part: ((part['batting_won'] - part['win_prob']) ** 2).mean()
log_loss = -(actual * np.log(clean['win_prob']) + (1 - actual) * np.log(1 - clean['win_prob'])).mean()
checks.append("1. Win probability on clean matches (balls scored by a model that did not train on that match):")
checks.append(f"   balls: {len(clean):,}   Brier score: {brier(clean):.4f}"
              f"   (always saying the base rate gives {base_rate * (1 - base_rate):.4f}, lower is better)")
checks.append(f"   log loss: {log_loss:.4f}")
for innings in [1, 2]:
    checks.append(f"   innings {innings} Brier score: {brier(clean[clean['innings'] == innings]):.4f}")
first_ball_2 = balls[(balls['innings'] == 2) & (balls['balls_bowled'] == 0)]
checks.append(f"   average win probability of the chasing team on the first ball: {first_ball_2['win_prob'].mean():.3f}")
checks.append("")

# Check 2 : calibration table, when the model says 70% the team should win about 70% of the time
clean_cal = clean.assign(bucket=pd.qcut(clean['win_prob'], 10, duplicates='drop'))
table = clean_cal.groupby('bucket', observed=True).agg(predicted=('win_prob', 'mean'), actual=('batting_won', 'mean'), balls=('win_prob', 'size'))
checks.append("2. Calibration (10 equal buckets of balls, predicted against actual win rate):")
for _, row in table.iterrows():
    checks.append(f"   predicted {row['predicted']:.3f}   actual {row['actual']:.3f}   balls {int(row['balls']):,}")
worst_gap = (table['predicted'] - table['actual']).abs().max()
checks.append(f"   biggest gap between predicted and actual: {worst_gap:.3f}")
checks.append("")

plt.figure(figsize=(5, 5))
plt.plot([0, 1], [0, 1], color='grey', linestyle='--', label='perfect')
plt.plot(table['predicted'], table['actual'], marker='o', color='steelblue', label='model')
plt.xlabel("Predicted win probability")
plt.ylabel("Actual win rate")
plt.title("Win probability calibration")
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(output_folder, "02_calibration.png"), dpi=150)
plt.close()

# Check 3 : spot checks, the last over of a close chase should score high and a one sided chase low
chase = balls[balls['innings'] == 2]
close_last_over = chase[(chase['balls_left'] <= 6) & (chase['runs_needed'] >= 1) & (chase['runs_needed'] <= 12)]
one_sided = chase[(chase['win_prob'] > 0.95) | (chase['win_prob'] < 0.05)]
first_over_1 = balls[(balls['innings'] == 1) & (balls['balls_bowled'] < 6)]
checks.append("3. Spot checks, average pressure (0 to 100):")
checks.append(f"   last over of a close chase (1 to 12 needed): {close_last_over['pressure'].mean():.1f}   balls: {len(close_last_over):,}")
checks.append(f"   one sided chase (win chance above 95% or below 5%): {one_sided['pressure'].mean():.1f}   balls: {len(one_sided):,}")
checks.append(f"   first over of the first innings: {first_over_1['pressure'].mean():.1f}")
checks.append(f"   share of balls above pressure 90 by innings: "
              f"innings 1 {(balls.loc[balls['innings'] == 1, 'pressure'] > 90).mean():.1%}, "
              f"innings 2 {(balls.loc[balls['innings'] == 2, 'pressure'] > 90).mean():.1%}")
phase = pd.cut(balls['balls_bowled'], [-1, 35, 95, 120], labels=['overs 1-6', 'overs 7-16', 'overs 17-20'])
by_phase = balls.groupby([balls['innings'], phase], observed=True)['pressure'].mean()
for (innings, name), value in by_phase.items():
    checks.append(f"   innings {innings} {name}: {value:.1f}")
checks.append("")

# Check 4 : the felt signals
checks.append("4. Felt signals, effect with the match state held fixed (over, wickets down, innings, competition):")
checks.append("   kept if t is 3 or more and the effect is 0.05 runs per ball or 1 percentage point of wicket chance")
for signal in signals:
    runs_effect, runs_t = signal_results[(signal, 'total_runs')]
    wicket_effect, wicket_t = signal_results[(signal, 'is_wicket')]
    share = balls.loc[balls['legal'], signal].mean()
    decision = "KEEP" if signal in kept else "drop"
    checks.append(f"   {signal}: on for {share:.1%} of balls   runs per ball {runs_effect:+.3f} (t {runs_t:+.1f})"
                  f"   wicket chance {wicket_effect:+.3f} (t {wicket_t:+.1f})   {decision}")
checks.append("")

# Check 5 : the rule based backup against the leverage score
rank_corr = balls[['pressure', 'rule_index']].corr(method='spearman').iloc[0, 1]
checks.append("5. Rule based index against the leverage pressure score:")
chase_corr = balls.loc[balls['innings'] == 2, ['pressure', 'rule_index']].corr(method='spearman').iloc[0, 1]
checks.append(f"   rank correlation: {rank_corr:.3f} on all balls, {chase_corr:.3f} on second innings balls only")
top_leverage = balls['pressure'] > 90
top_rule = balls['rule_index'] > balls['rule_index'].quantile(0.9)
checks.append(f"   share of the top 10% leverage balls that are also in the top 10% of the rule index: "
              f"{(top_leverage & top_rule).sum() / top_leverage.sum():.1%}")

with open(os.path.join(output_folder, "02_checks.txt"), "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(checks) + "\n")

for line in checks:
    print(line)

print(f"\nSaved {len(balls):,} rows to outputs/balls_pressure.parquet")
