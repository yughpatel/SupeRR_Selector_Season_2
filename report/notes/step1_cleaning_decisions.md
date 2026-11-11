# Step 1: cleaning decisions and why each one is safe

This note lists every choice made in `src/01_clean.py`, how many rows it touches, and why it does not bias the rankings. The report's "fair comparisons" and "limitations" sections will draw on it.

The raw file has 200,999 balls from 867 matches. The clean table has 200,961 balls. No column was deleted. Some columns are simply not used, and those are listed below with the reason.

## Rows removed

| What | Rows | Why it is safe |
|---|---|---|
| Super-over balls (innings 3 and 4) | 38 balls in 6 matches | A super over is a separate six-ball contest with its own rules (two wickets end it). Its match state cannot be compared with a 20-over innings, so one model cannot score both. 38 balls is 0.02% of the data and far too few to rank any player. The main match stays in the table and is marked as a tie. |

That is the only removal. The 16 abandoned matches in `matches.csv` never had ball data, so there was nothing to remove.

Cost of this choice: super overs are high-pressure moments and we do not score them. We say this in the limitations.

## Rows kept but flagged

These balls stay in the table. A flag tells later steps how to treat them.

| Flag | Matches | Balls | What it means | Why we keep the balls |
|---|---|---|---|---|
| `clean_match = True` | 812 | 192,618 | Clear winner and both innings ran their full course | These train the win-probability model |
| Ties | 10 | part of 8,343 | No winner after 20 overs each | The model needs a win or loss label to learn from, and a tie has neither. The balls still get a pressure score later, because the trained model can score any match state. |
| No winner | 24 | part of 8,343 | Rain ended the match with no result | Same reason. The batting and bowling on these balls is still real performance. |
| Winner, but an innings stops early | 21 | part of 8,343 | Rain cut the match short and DLS decided it, or the file is missing the last balls | The result was not decided by the balls we can see, so the model should not learn from it |
| `legal = False` | | 8,550 | 7,710 wides, 839 no-balls and 1 penalty row | They are real events with runs, but they do not use up a ball, so they must not count as balls faced or bowled |

In total 55 matches (8,343 balls, 4.2%) are not used to train the win-probability model. Dropping them from training cannot favour any player, because the choice depends on rain and ties, which no player controls.

## Columns we do not use

| Column | Why not |
|---|---|
| `extras1_runs` | The name is misleading. It is a code for the type of extra (1 no-ball, 2 wide, 3 leg-bye, 4 bye, 5 other, 6 none, 7 penalty). It repeats `extras_type` and holds no runs. |
| `bowl_speed` | 38.7% of balls have a speed of 0, which means it was not recorded. A feature that is missing for over a third of balls would treat matches unequally. |
| `delivery_ist_time` | The order of balls already comes from `innings_ball_num`. Clock time adds nothing to the match state. |
| `stroke`, `delivery_style`, `over_or_around`, `on_or_off` | They describe how a ball was bowled or played. Pressure depends on the match situation, and performance is judged by the outcome (runs and wickets). `stroke` is also missing on 6,158 balls. We may use these later for the team insights, never for the ranking. |
| `man_of_the_match` (matches) | It is a judge's opinion and is 0 for 119 matches. The brief says rankings must come from analysis, so we leave awards out. |
| Captain ids (matches) | Missing for 44 matches and not needed. |
| `dismissed_player_id` on balls with no wicket | 12 balls have a player id here while `is_wicket` is false (likely a batter retiring hurt). We trust `is_wicket`, so these are not wickets. |

`extras_2_runs` is used. It holds the byes run on a no-ball (values 0, 1 or 4).

## Values we had to infer

The raw file does not record how many runs came from byes, leg-byes, or extra runs on a wide. Without them, rebuilt scores matched the official margin in only 11.8% of test matches.

The fix uses a fact of cricket: batters swap ends when they run an odd number of runs. The file shows who faced the next ball, so we know if the runs were odd or even.

| Case | Balls | Runs given | Why |
|---|---|---|---|
| Bye or leg-bye, batters swapped | 2,679 | 1 | Odd. Three is very rare. |
| Bye or leg-bye, batters did not swap | 534 | 4 | Even, and it cannot be 0 on a bye, so a boundary is the usual case |
| Bye or leg-bye, cannot tell | 63 | 1 | Last ball of an innings or a wicket on the same ball. We take the smallest possible value. |
| Wide, batters swapped | 298 | 2 | The 1-run penalty plus one run |
| Wide, no swap | 7,412 | 1 | Penalty only |
| No-ball | 839 | 1 + `extras_2_runs` | Penalty plus recorded byes. Runs off the bat are already in the file. |

Proof that the rule works: on 177,095 normal balls, where the runs are known, the next striker agrees with the rule 99.98% of the time.

Result: on 390 matches won by runs (no rain, both innings complete), the rebuilt margin is exact in 62.3%, within 2 runs in 77.2%, and within 4 runs in 97.2%. The worst case is 8 runs.

What is still uncertain: an even bye could be 2 runs, and a wide can run away for 4 more. The file cannot tell us. The error is small and random, so it does not lean toward any player.

## Chase targets

A rebuilt first-innings total can be a few runs off, and in a close finish a few runs matter. So each target is tied to the official result.

| Situation | Matches | Target used |
|---|---|---|
| Chasing team lost by N runs | 401 | Their final score + N + 1. This is exact by definition. |
| Chasing team won by wickets | 419 | First-innings score + 1, kept in the range that makes the last ball the winning one |
| Tie | 10 | Chasing team's final score + 1 |
| No clean result | 15 | First-innings score + 1, or the official revised target |

Check: in clean matches, no ball is bowled after the target was already reached.

## Rain-shortened matches

34 matches have a revised innings length or target. The revised columns hold balls (114 means 19 overs). `balls_left` uses the revised length, so a ball in a 10-over match is not treated as if 20 overs were available.

## Credit rules

| Rule | Balls | Why |
|---|---|---|
| Bowler gets the wicket for caught, bowled, LBW, stumped, hit wicket | 10,261 of 10,868 wickets | These come from the bowler's delivery |
| Run-outs, retired out, obstructing the field count for the team only | 598 + 6 + 3 | The bowler did not cause them. Counting them would reward luck. |
| A wicket is charged to the batter who was out | 273 wickets were the non-striker | A striker should not be blamed when his partner is run out |
| Byes and leg-byes are not charged to the bowler | 3,276 | The runs did not come from a bad ball in the scoring sense, and scorecards treat them the same way |
| Wides and the no-ball penalty are charged to the bowler | 8,549 | They are the bowler's errors |

## Open decision

30 matches (6,973 balls) come from two A-team events: Emerging Teams Asia Cup 2024 and Asia Cup Rising Stars 2025. The brief names only IPL and T20Is. The plan is to let the models learn from these balls and leave their players out of the rankings.
