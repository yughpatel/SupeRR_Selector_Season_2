# Step 1 : Cleaning the ball by ball data and finding the match state before every ball
#
# Run from the project folder : python src/01_clean.py
# Reads  : ball_by_ball.csv, matches.csv, competitions.csv
# Writes : outputs/balls_clean.parquet (one row per ball with the state before it)
#          outputs/01_checks.txt (checks to see if the table can be trusted)
#
# 3 problems in the raw data:
# 1. Super overs (innings 3 and 4) are in the file, I drop them
# 2. The file does not give the runs from byes, leg byes and extra runs on a wide,
#    so I work them out from whether the batters changed ends
# 3. Some matches were cut short by rain, so an innings is not always 120 balls

# Importing Libraries
import os
import numpy as np
import pandas as pd

folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
output_folder = os.path.join(folder, "outputs")
os.makedirs(output_folder, exist_ok=True)

# Loading Dataset
balls = pd.read_csv(os.path.join(folder, "ball_by_ball.csv"), low_memory=False)
matches = pd.read_csv(os.path.join(folder, "matches.csv"))
competitions = pd.read_csv(os.path.join(folder, "competitions.csv"))

# Dropping super overs
balls = balls[balls['innings'] <= 2].copy()

balls = balls.sort_values(['match_id', 'innings', 'innings_ball_num']).reset_index(drop=True)
balls = balls.rename(columns={'overid': 'over', 'runs': 'bat_runs'})

# Type of extra on each ball
# "Overstep" is a front foot no ball. "other" is never a legal ball in the data and
# the batter can score off it, same as a no ball, so I count it as a no ball
extras_type = balls['extras_type'].fillna('none')
balls['is_wide'] = extras_type == 'wide'
balls['is_noball'] = extras_type.isin(['Overstep', 'other'])
balls['is_bye'] = extras_type == 'byes'
balls['is_legbye'] = extras_type == 'legbyes'

# A wide or a no ball is bowled again so it is not a legal ball
# There is also 1 "Penalty" row which is not a ball at all
balls['legal'] = ~(balls['is_wide'] | balls['is_noball'] | (extras_type == 'Penalty'))


# Finding the runs from extras (not given in the raw file)
# If the batters run 1 or 3 they change ends, so the other batter faces the next ball.
# I can see who faced the next ball, so I know if the runs were odd or even.
# After the last ball of an over the bowling end changes, so there it is the opposite.
# On normal balls this is correct 99.9% of the time (check 1 at the bottom)
group = balls.groupby(['match_id', 'innings'], sort=False)
next_striker = group['striker_id'].shift(-1)
next_over = group['over'].shift(-1)

same_over = next_over == balls['over']
swapped = next_striker == balls['non_striker_id']
stayed = next_striker == balls['striker_id']

crossed = stayed.copy()
crossed[same_over] = swapped[same_over]

# Cannot tell on the last ball of an innings or when a wicket brings a new batter
crossed_known = next_striker.notna() & ~balls['is_wicket'] & (swapped | stayed)
balls['crossed'] = crossed & crossed_known
balls['crossed_known'] = crossed_known

balls['extras_runs'] = 0

# Byes and leg byes : odd means 1 run (3 is very rare)
# even cannot be 0 on a bye, so I take 4 (boundary)
# if I cannot tell, I take 1 which is the smallest possible
bye_or_legbye = balls['is_bye'] | balls['is_legbye']
balls.loc[bye_or_legbye, 'extras_runs'] = 1
balls.loc[bye_or_legbye & crossed_known & ~balls['crossed'], 'extras_runs'] = 4

# Wides : 1 run penalty, and 1 more if the batters changed ends
balls.loc[balls['is_wide'], 'extras_runs'] = 1
balls.loc[balls['is_wide'] & balls['crossed'], 'extras_runs'] = 2

# No balls : 1 run penalty + extras_2_runs (byes run on the no ball)
balls.loc[balls['is_noball'], 'extras_runs'] = 1 + balls.loc[balls['is_noball'], 'extras_2_runs']

balls['total_runs'] = balls['bat_runs'] + balls['extras_runs']

# Runs given by the bowler = runs off the bat + all wide runs + no ball penalty
# Byes and leg byes are not counted against the bowler
balls['bowler_runs'] = balls['bat_runs']
balls.loc[balls['is_wide'], 'bowler_runs'] += balls.loc[balls['is_wide'], 'extras_runs']
balls.loc[balls['is_noball'], 'bowler_runs'] += 1


# Wicket credit
# A run out or retired out is a team wicket, the bowler did not take it
bowler_dismissals = ['Caught', 'Bowled', 'LBW', 'Stump', 'Hit Wicket']
balls['bowler_wicket'] = balls['is_wicket'] & balls['dismissal_type'].isin(bowler_dismissals)

# Who got out? Mostly the striker, but in a run out it can be the non striker
out_player = balls['dismissed_player_id'].where(balls['is_wicket'])
balls['striker_out'] = balls['is_wicket'] & (out_player.isna() | (out_player == balls['striker_id']))


# State before each ball : score, wickets down, legal balls bowled
group = balls.groupby(['match_id', 'innings'], sort=False)
balls['score_before'] = group['total_runs'].cumsum() - balls['total_runs']
balls['wickets_before'] = group['is_wicket'].cumsum() - balls['is_wicket'].astype(int)
balls['balls_bowled'] = group['legal'].cumsum() - balls['legal'].astype(int)


# Match details
matches = matches.merge(competitions, on='comp_id', how='left')

# 3 groups : IPL, T20 internationals and 2 smaller "A team" events
matches['comp_group'] = 'Other T20'
matches.loc[matches['match_format'] == 'T20I', 'comp_group'] = 'T20I'
matches.loc[matches['comp_name'].str.startswith('IPL'), 'comp_group'] = 'IPL'

# Getting the margin out of the result text, like "Won by 9 Wickets" or "Won by 1 Run"
result = matches['result'].fillna('')
matches['margin_runs'] = result.str.extract(r"(\d+)\s*[Rr]uns?")[0].astype(float)
matches['margin_wkts'] = result.str.extract(r"(\d+)\s*(?:[Ww]ickets?|[Ww]kts?)")[0].astype(float)
matches['tied'] = result.str.contains(r"[Tt]ied|[Ss]uper [Oo]ver|Eliminator")
matches['has_winner'] = (matches['win_team_id'] > 0) & ~matches['tied']

# Rain : the revised columns have the number of balls the innings was cut to
matches['max_balls_1'] = matches['first_inn_revised_overs'].fillna(120)
matches['max_balls_2'] = matches['second_inn_revised_overs'].fillna(matches['max_balls_1'])


# One row per match with the totals of both innings
innings_totals = balls.groupby(['match_id', 'innings']).agg(
    final=('total_runs', 'sum'),
    legal=('legal', 'sum'),
    wkts=('is_wicket', 'sum'),
    last_runs=('total_runs', 'last'),
    bat_team=('batting_team_id', 'first'),
).reset_index()

summary = innings_totals.pivot(index='match_id', columns='innings')
summary.columns = [f"{name}_{innings}" for name, innings in summary.columns]
summary = summary.reset_index().merge(matches, on='match_id', how='left')


# Target for the chasing team
# My totals can be a few runs off because of the extras, so I fix the target
# using the official result:
# chasing team lost by N runs -> target = their final score + N + 1
# chasing team won            -> target = first innings score + 1, kept in the range
#                                where the last ball is the winning ball
# rain matches                -> official revised target if the first rule cannot be used
first_target = summary['revised_target'].fillna(summary['final_1'] + 1)
inn2_done = (summary['legal_2'] == summary['max_balls_2']) | (summary['wkts_2'] == 10)
chase_won = summary['has_winner'] & (summary['win_team_id'] == summary['bat_team_2'])
chase_lost = summary['has_winner'] & (summary['win_team_id'] == summary['bat_team_1'])

# Some rain matches stopped in the middle of the chase and the chasing team won "by runs"
# because it was ahead of the DLS par score. It never reached a target so I leave these
par_win = chase_won & summary['margin_runs'].notna()
chase_won = chase_won & ~par_win

summary['target'] = first_target
summary['target_rule'] = 'first innings + 1'

use_margin = chase_lost & inn2_done & summary['margin_runs'].notna()
summary.loc[use_margin, 'target'] = summary['final_2'] + summary['margin_runs'] + 1
summary.loc[use_margin, 'target_rule'] = 'result margin'

# The last ball has to be needed (lowest) and it has to reach the target (highest)
lowest = summary['final_2'] - summary['last_runs_2'] + 1
highest = summary['final_2']
summary.loc[chase_won, 'target'] = first_target.clip(lower=lowest, upper=highest)[chase_won]
summary.loc[chase_won, 'target_rule'] = 'first innings + 1, fitted to the win'

tie = summary['tied'] & summary['final_2'].notna()
summary.loc[tie, 'target'] = summary['final_2'] + 1
summary.loc[tie, 'target_rule'] = 'tie'

revised = summary['revised_target'].notna() & ~use_margin & ~chase_won
summary.loc[revised, 'target_rule'] = 'official revised target'

# No target if there is no second innings in the data
summary.loc[summary['final_2'].isna(), 'target'] = np.nan
summary.loc[summary['final_2'].isna(), 'target_rule'] = np.nan

# An innings is complete if all balls are used, 10 wickets fell or the chase was won
summary['inn1_complete'] = (summary['legal_1'] == summary['max_balls_1']) | (summary['wkts_1'] == 10)
summary['inn2_complete'] = inn2_done | chase_won

# Clean match = has a winner and both innings are complete
# Step 2 trains the win probability model only on these
clean_match = summary['has_winner'] & summary['inn1_complete'] & summary['inn2_complete'] & ~par_win
summary['clean_match'] = clean_match.fillna(False)


# Adding the match columns to every ball
match_columns = [
    'match_id', 'comp_id', 'comp_name', 'comp_group', 'season', 'match_date', 'stage',
    'knock_out', 'venue_id', 'win_team_id', 'has_winner', 'tied', 'result',
    'max_balls_1', 'max_balls_2', 'target', 'target_rule', 'inn1_complete',
    'inn2_complete', 'clean_match', 'final_1', 'final_2', 'margin_runs', 'margin_wkts',
]
balls = balls.merge(summary[match_columns], on='match_id', how='left')

balls['max_balls'] = balls['max_balls_1']
balls.loc[balls['innings'] == 2, 'max_balls'] = balls['max_balls_2']
balls['balls_left'] = balls['max_balls'] - balls['balls_bowled']
balls['wickets_left'] = 10 - balls['wickets_before']
balls['over_number'] = (balls['balls_bowled'] // 6).clip(upper=19)
balls['comp_code'] = balls['comp_group'].map({'IPL': 0, 'T20I': 1, 'Other T20': 2})

# Splitting the matches into 5 groups (folds) for the models in steps 2 and 3
# Every match is scored by a model that was trained on the other 4 groups,
# so no match is scored by a model that already saw its result
match_ids = balls['match_id'].unique()
shuffled = np.random.RandomState(42).permutation(match_ids)
balls['fold'] = balls['match_id'].map(pd.Series(np.arange(len(shuffled)) % 5, index=shuffled))

# Target and runs needed only make sense in the second innings
balls.loc[balls['innings'] == 1, 'target'] = np.nan
balls['runs_needed'] = balls['target'] - balls['score_before']

# Required rate per over. On the last ball balls_left can be 0 so I avoid dividing by 0
balls['required_rate'] = balls['runs_needed'] / balls['balls_left'].where(balls['balls_left'] > 0) * 6

# 1 if the batting team won the match, 0 if it lost, empty if there is no winner
balls['batting_won'] = np.nan
balls.loc[balls['has_winner'], 'batting_won'] = (balls['win_team_id'] == balls['batting_team_id']).astype(float)

balls = balls.drop(columns=['max_balls_1', 'max_balls_2'])

# Saving the clean table
balls.to_parquet(os.path.join(output_folder, "balls_clean.parquet"), index=False)


# Checks
checks = []

total_innings = balls.groupby(['match_id', 'innings']).ngroups
group_counts = balls.groupby('comp_group')['match_id'].nunique().to_dict()
no_winner = int((~summary['has_winner'] & ~summary['tied']).sum())

checks.append("STEP 1 CHECKS")
checks.append(f"balls kept: {len(balls):,}   matches: {balls['match_id'].nunique()}   innings: {total_innings}")
checks.append(f"by competition group (matches): {group_counts}")
checks.append(f"matches with a clear winner: {int(summary['has_winner'].sum())}   ties: {int(summary['tied'].sum())}   no winner: {no_winner}")
checks.append("")

# Check 1 : on normal balls the runs are known, so I can test the change of ends idea
any_extra = balls['is_wide'] | balls['is_noball'] | balls['is_bye'] | balls['is_legbye']
normal = balls[balls['crossed_known'] & ~any_extra]
rule_correct = (normal['crossed'] == (normal['bat_runs'] % 2 == 1)).mean()

checks.append("1. Does the swap-ends rule work? Share of normal balls where the next striker matches the runs scored:")
checks.append(f"   {rule_correct:.4%} of {len(normal):,} balls")
checks.append("")

# Check 2 : my totals against the official margin, in matches won by runs with no rain
no_rain = summary['revised_target'].isna() & summary['first_inn_revised_overs'].isna() & summary['second_inn_revised_overs'].isna()
both_complete = summary['inn1_complete'] & summary['inn2_complete']
bat_first_won = summary['win_team_id'] == summary['bat_team_1']
test = summary[summary['has_winner'] & summary['margin_runs'].notna() & no_rain & both_complete & bat_first_won]
error = (test['final_1'] - test['final_2']) - test['margin_runs']

# Same thing without my extras (only runs off the bat + 1 for each wide and no ball)
raw_runs = balls['bat_runs'] + (balls['is_wide'] | balls['is_noball'])
raw_totals = raw_runs.groupby([balls['match_id'], balls['innings']]).sum().unstack()
raw_error = (raw_totals.loc[test['match_id'], 1].values - raw_totals.loc[test['match_id'], 2].values) - test['margin_runs'].values

checks.append("2. Do rebuilt totals match official results? Matches won by runs, no rain, both innings complete:")
checks.append(f"   matches: {len(test)}   exact: {(error == 0).mean():.1%}   within 2 runs: {(error.abs() <= 2).mean():.1%}"
              f"   within 4 runs: {(error.abs() <= 4).mean():.1%}   worst: {int(error.abs().max())}")
checks.append(f"   without the inferred extras only {np.mean(raw_error == 0):.1%} are exact, so the inference helps")
checks.append("")

# Check 3 : the winner should match the type of margin
by_wickets = summary[summary['has_winner'] & summary['margin_wkts'].notna() & summary['margin_runs'].isna()]
by_runs = summary[summary['clean_match'] & summary['margin_runs'].notna() & summary['margin_wkts'].isna()]
by_wickets_no_rain = by_wickets[by_wickets['revised_target'].isna()]

checks.append("3. Winner agrees with the type of margin:")
checks.append(f"   'won by wickets' and the winner batted second: {(by_wickets['win_team_id'] == by_wickets['bat_team_2']).mean():.1%} of {len(by_wickets)}")
checks.append(f"   'won by runs' and the winner batted first:      {(by_runs['win_team_id'] == by_runs['bat_team_1']).mean():.1%} of {len(by_runs)}")
checks.append(f"   wickets in hand at the end equals the stated margin: {((10 - by_wickets_no_rain['wkts_2']) == by_wickets_no_rain['margin_wkts']).mean():.1%}")
checks.append("")

# Check 4 : no innings should have more balls or wickets than allowed
innings_check = balls.groupby(['match_id', 'innings']).agg(legal=('legal', 'sum'), wickets=('is_wicket', 'sum'), max_balls=('max_balls', 'first'))

checks.append("4. Innings limits:")
checks.append(f"   innings with more legal balls than allowed: {int((innings_check['legal'] > innings_check['max_balls']).sum())}"
              f"   more than 10 wickets: {int((innings_check['wickets'] > 10).sum())}")
checks.append(f"   first innings that stop early in the data (rain or missing balls): {int((~summary['inn1_complete']).sum())}")
checks.append(f"   matches with no second innings in the data: {int(summary['final_2'].isna().sum())}")
checks.append("")

# Check 5 : in a chase runs needed should stay above 0 till the winning ball
chase = balls[(balls['innings'] == 2) & balls['clean_match']]
chase_stops_early = summary['has_winner'] & ~summary['inn2_complete'] & summary['final_2'].notna()

checks.append("5. Chases: runs needed must be above 0 before every ball and reach 0 or less on a winning last ball.")
checks.append(f"   balls where runs needed was already 0 or less: {int((chase['runs_needed'] <= 0).sum())}")
checks.append(f"   matches with a winner where the chase stops early (rain or missing balls): {int(chase_stops_early.sum())}")
checks.append(f"   clean matches (winner, both innings complete): {int(summary['clean_match'].sum())}")
checks.append(f"   how each target was set: {summary['target_rule'].value_counts().to_dict()}")
checks.append("")

# Check 6 : missing values
checks.append("6. Missing values in the columns later steps use:")
for column in ['score_before', 'wickets_before', 'balls_left', 'pace_or_spin', 'striker_id', 'bowler_id']:
    checks.append(f"   {column}: {int(balls[column].isna().sum())}")

# Saving and printing the checks
with open(os.path.join(output_folder, "01_checks.txt"), "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(checks) + "\n")

for line in checks:
    print(line)

print(f"\nSaved {len(balls):,} rows and {balls.shape[1]} columns to outputs/balls_clean.parquet")
