# Step 2: pressure score decisions and why each one is safe

This note lists every choice made in `src/02_pressure.py`, the numbers behind it, and what can go wrong. The numbers come from `outputs/02_checks.txt`.

## The win probability model

One LightGBM model per innings. The input is the state before the ball: score (first innings) or runs needed (second innings), wickets left, balls left and the competition group. The output is the chance that the batting team wins.

- The model must follow cricket logic. More wickets left, more balls left and more runs scored never lower the chance. More runs needed never raises it.
- It trains only on the 812 clean matches (clear winner, both innings complete). Every match is still scored, including ties, rain matches and matches with no result.
- The matches are split into 5 groups. Each match is scored by a model that did not train on any ball of that match, so no match is scored by a model that saw its result.

Result on clean matches: Brier score 0.178 (0.250 for always saying the base rate), log loss 0.522. The chasing team's average chance on the first ball is 0.497. The calibration table is in the checks file and the chart is `outputs/02_calibration.png`. When the model says 70% the team wins about 70% of the time, and the biggest gap in any of the 10 buckets is 2.6 points.

What the model can and cannot do: the second innings is predicted well (Brier 0.129). The first innings is weak (Brier 0.223), which is normal because nobody knows the final result at ball 1. The model does not know team strength or venue, so a wicket can look a little more costly than it really is.

## Leverage and the pressure score

My first version followed the plan: leverage = win chance after a four minus win chance after a wicket. It does not work early in an innings. A first-ball wicket cost 10.9 points of win probability, which is far too much. The model has almost no data on states like "9 wickets left, score 0, 119 balls left", so that number is a guess. I tried bigger trees, smaller leaves and a smooth spline model instead of LightGBM. The first-ball cost stayed unreliable in all of them. This is a data limit, not a tuning problem.

So the final leverage is the average size of the move in win probability over the next ball. For each of the 8 outcomes (0 to 6 runs, wicket) I take the win chance after that outcome, subtract the current win chance, and weight by how often that outcome happens in that over of that innings. A rare early wicket now counts for its 5% chance and not for a full swing. The shares for a fold are counted on the other 4 folds only, so a match is never scored with anything learned from itself (counting them on all matches changed almost nothing, but this keeps one rule everywhere).

- Pressure = leverage as a percentile over all balls (0 to 100), both innings pooled. A first innings ball is therefore compared with every second innings ball. Few first innings balls score high (3.6% are above 90, against 17.1% in the second innings). This is correct under this definition, but it means a batter who always bats first gets fewer high pressure balls. It goes in the limitations.
- I compared it once with the simple gap. The two agree well overall (rank correlation 0.81) and differ mostly in the first overs. Nothing later uses the gap, so it is not saved.
- Every ball is treated as a legal ball in the after-states. A wide does not use a ball, but the effect is small.
- In a chase the end of the game is known: target reached is a win, no balls or no wickets left is a loss. The model is never asked about states it never saw.

Spot checks on average pressure:

| Situation | Average pressure |
|---|---|
| Last over of a close chase (1 to 12 needed) | 92.1 |
| First over of the first innings | 36.3 |
| One sided chase (win chance above 95% or below 5%) | 13.1 |

## Felt signals

Four things the scoreboard does not show. For each one I ran a regression of runs per ball and wicket chance on the signal, holding the over, wickets down, innings and competition fixed. Standard errors are grouped by match. I keep a signal if t is 3 or more and the effect is at least 0.05 runs per ball or 1 percentage point of wicket chance. Those cutoffs are my own choice.

| Signal | On for | Runs per ball | Wicket chance | Decision |
|---|---|---|---|---|
| 3 or more dot balls in a row | 5.2% of balls | -0.121 (t -7.0) | -0.000 | Keep |
| 2 or more wickets in the last 18 balls | 19.5% | -0.102 (t -8.4) | -0.002 | Keep |
| Batter in his first 10 balls | 52.4% | -0.228 (t -22.8) | -0.005 (t -3.8) | Keep |
| Knockout match | 3.7% | -0.001 | +0.004 (t 1.5) | Drop |

Knockouts show no change once the match state is held fixed, so they are dropped. The three kept signals are saved as flags (`sig_dots`, `sig_wickets`, `sig_new_batter`) and a count (`felt_count`). They are not added into the pressure score. Step 4 can use them as extra conditions.

Caution: these tests show that runs fall when a signal is on. They do not prove the cause is pressure. A bowler on a roll or a hard pitch gives the same pattern. The first ten balls of a batter is on for half the balls, so it describes settling in more than a rare moment. I will say this in the report.

## Rule based index (backup)

A simple 0 to 100 score for step 5 to compare with. In a chase it is high when the required rate is close to what the batters can manage and the innings is near its end. "What they can manage" is the league scoring rate, lowered by the square root of the share of wickets left. In the first innings it uses only wickets lost and balls used, capped at 50.

It agrees only loosely with the leverage score (rank correlation 0.23 on all balls, 0.34 in the second innings, and 24% overlap in the top 10% of balls). This is expected because the index is a crude rule. Step 5 compares the final player lists, not single balls, so what matters is whether the same players come out.

## Output

`outputs/balls_pressure.parquet` has one row per ball (200,961 rows) with the keys (`match_id`, `innings`, `innings_ball_num`), the win probability, `leverage`, `pressure`, `rule_index` and the signal columns. It is not in git. Run `src/02_pressure.py` to make it.
