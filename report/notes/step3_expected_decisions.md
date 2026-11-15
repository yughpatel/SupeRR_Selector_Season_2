# Step 3: expected outcomes and ball value, decisions and why each one is safe

This note lists every choice made in `src/03_expected.py`, the numbers behind it, and what can go wrong. The numbers come from `outputs/03_checks.txt`.

## What the step does

Every ball gets a value: what happened minus what an average player would have done in the same situation. Raw strike rate or economy would be unfair, because an opener and a death bowler face different situations. A positive value is good for the player.

## Expected outcomes

Four LightGBM models, each trained on all matches:

| Model | Balls | Predicts |
|---|---|---|
| `exp_bat_runs` | 192,411 legal balls | Runs off the bat |
| `exp_bat_out` | 192,411 legal balls | Chance the striker gets out (run-outs of the striker included) |
| `exp_bowl_runs` | all 200,961 deliveries | Runs charged to the bowler (bat runs, wides, no-ball penalty) |
| `exp_bowl_wicket` | all 200,961 deliveries | Chance of a wicket the bowler gets credit for (not run-outs) |

Inputs: innings, over, wickets down, pace or spin, competition group, and two numbers about the opponent. No player name or id goes in, so the model describes an average player and not a particular one.

- A batter is compared with the average batter against the same opponent, which is the bowling team. A bowler is compared with the average bowler against the batting team. The player's own team is left out on purpose, because it would hide the player's own quality.
- Pressure, the target and the runs needed are not inputs. If they were, the expected value would already include the effect of pressure, and step 4 could not measure it.
- Every match is scored by a model that did not train on that match, using the same 5 folds as step 2.

Result: the average expected value matches the average actual value to the third decimal for runs (1.394 against 1.394 for batters) and for wickets. The models explain only about 1.9% of the ball to ball variation in runs. That is normal, because one ball is mostly luck. What matters is that the average is right in every situation, and check 3 below shows that.

Overfit test: the error on the training matches against the error on the held out matches. For runs the held out error is 0.019 above the training error on a base of about 2.96 (0.6%), for wickets 0.0003 on a base of 0.05 (0.5%). The gain over a flat average is about 2% for runs, so the gap is small next to the gain, and the models are not memorising.

## Opponent strength

The opponent is described by two rates: runs per delivery (given or scored) and wickets per delivery (taken or lost). A team with few balls is pulled towards the competition average, as if it had 600 extra balls at that average.

Fixed in the audit: my first version took the rates from all the team's other matches, leaving out only the match being scored. That is a leak. A team's rate drops in the matches where it gave many runs, so inside one team the rate and the match's runs had a correlation of -0.67 (38 teams). The model could use this to peek at the result of the match it was scoring. It made the expected value follow the actual value a little, and it made the explained variance look 30% better than it is (2.7% against the honest 1.9%).

Now every fold gets its rates from the matches that fold trains on and never from the matches it scores. The match being scored is never part of its own opponent rate. In the training rows a team's rate does include the team's own training matches, which is fine because it is one number per team and the model cannot pick out a single match from it.

Honest finding: on held out matches the opponent rates add nothing for batters (error 2.9770 with against 2.9770 without), nothing for wickets, and a little for bowlers (2.874 against 2.881, so the batting team matters a bit). I kept them anyway, for one reason: inside the T20I, batters score 1.287, 1.346 and 1.394 per ball against the easiest, middle and hardest to score against bowling teams, and the model expects 1.277, 1.338 and 1.412. Without the rates, a T20I batter who faced weak attacks would get credit for it. The inputs are cheap and the held out check shows they do not make the model worse. Inside the IPL the gaps are small and the pattern is not clean, which is expected when ten teams play each other all season.

## What a wicket costs

Runs scored from this ball to the end of the first innings (complete innings only), fitted against balls bowled, wickets already lost, and their interaction, with a squared term for the balls. The cost of one more wicket is the fall in expected remaining runs, and it changes smoothly with the ball number. The IPL and T20I have their own fits. The 30 Other T20 matches use the fit on everything. Costs below zero are set to zero.

| Ball | IPL | T20I |
|---|---|---|
| 0 (first ball) | 18.2 | 13.2 |
| 18 (middle of the powerplay) | 14.6 | 10.9 |
| 35 / 36 | 11.5 / 11.3 | 8.9 / 8.8 |
| 60 | 7.6 | 6.3 |
| 95 / 96 | 3.3 / 3.2 | 3.2 / 3.2 |
| 110 | 1.9 | 2.1 |

Fixed in the audit: my first version used one number per phase (11.8, 6.6, 1.9). That made a wicket on ball 35 cost 11.8 runs and a wicket on ball 36 cost 6.6, which is not how cricket works, and it punished batters and credited bowlers at the end of each phase. A 5 fold test by match shows the smooth curve with separate IPL and T20I fits predicts the remaining runs better than the three straight lines (mean squared error 588.4 against 604.8). A fit with one curve for all competitions scored 601.1, so the split helps a little.

Cautions:
- The IPL and T20I costs differ by about 4 runs early on. A bootstrap by match puts the early gap between -0.3 and +7.0 at 90%, so the gap is probably real but its size is uncertain.
- Early wickets cost less in the data than a cricketer would say once the batting team's own strength is controlled for (about 7% less in the powerplay). A weak team loses wickets and scores less, so the plain fit has a little team strength inside it. It is the same cost for every player, so it does not favour anyone.
- Only first innings are used, since a chase stops as soon as the target is reached. The same cost is used for both innings.

## Value of a ball

- Batter: (runs off the bat minus expected runs) minus the wicket cost times (got out minus expected chance of getting out). Legal balls only.
- Bowler: (expected runs minus runs charged) plus the wicket cost times (took a wicket minus expected chance of a wicket). All deliveries, so wides and no-balls count against the bowler.

A single ball with a wicket is worth 11 to 18 runs early in an innings, so single ball values are very spread out (standard deviation 3.4 in the powerplay). The wicket part is about half of the variance of a batter's ball value (51%, the runs part 49%). That is the price of putting one wicket at about three boundaries. It is also why step 4 has to shrink small samples hard.

## Checks

The average value over all players is close to zero in every phase, innings, competition and bowler type:

| Group | Batters | Bowlers |
|---|---|---|
| Overs 1 to 6 | +0.004 | -0.003 |
| Overs 7 to 16 | +0.002 | -0.002 |
| Overs 17 to 20 | +0.005 | -0.004 |
| IPL | +0.002 | -0.002 |
| T20I | +0.002 | -0.003 |
| Other T20 | +0.024 | -0.007 |

These are all under 0.005 runs per ball, against a ball to ball spread of 2 to 3, except the batters in the 30 Other T20 matches (+0.024), which are only learned from and are not ranked.

By batting order the batters differ: order 1-2 is +0.029 per ball, order 3-4 +0.017, order 5-7 -0.005 and order 8-13 -0.143. I left this in on purpose. The model has no player information, so these gaps are real skill differences between batters in the same situation, not a role effect that the over and wickets down already remove. Step 4 compares each player with his own level.

## What the audit found

I checked steps 1 to 3 for leaks, overfitting and double counting.

Found and fixed:
1. The opponent rate leak described above (step 3).
2. The jump in the wicket cost at the phase edges described above (step 3).
3. In step 2 the share of each outcome in each over was counted on all matches, including the match being scored. It is now counted on the other 4 folds. The effect was negligible (the pressure table did not change except one overlap figure, 23.8% to 23.7%), but the rule is now the same everywhere: a match is never scored with anything learned from itself.

Checked and fine:
- No duplicate matches (same date and teams), no duplicate ball keys, no two matches with the same ball sequence.
- Bowler runs plus byes and leg byes equal the total runs (278,353 + 4,961 = 283,314). Bowler wickets exclude the run-outs, as intended.
- The 5 folds hold 173 or 174 matches each.
- The win probability model has no overfit: the Brier score on the training folds against the held out fold is 0.2175 against 0.2153 in the first innings and 0.1255 against 0.1203 in the second.
- Team averages are spread by real team quality and not by a flaw: for the 22 teams with 3,000 or more balls, the average batter value runs from -0.165 to +0.153 per ball and the average bowler value from -0.055 to +0.055. The model leaves the player's own team out on purpose, so a good team shows up as a positive number. Step 4 has to remember that a player in a strong team starts with a small head start in this table.

## Output

`outputs/balls_value.parquet` has one row per ball (200,961 rows) with the keys, the fold, the phase, the wicket cost, the four expected values, `batter_value` and `bowler_value`. It is not in git. Run `src/03_expected.py` to make it.

## Added after a review (Nov 15): the ground and the balls already faced

A review of the whole project found two things the expected outcome models did not know, and both moved names.

- The ground. Without it, the average batter value at the 13 IPL grounds with 3,000 or more balls ran from -0.18 to +0.12 per ball (spread 0.095), as big as the true spread between players, and two random halves of the matches agreed on it (0.60). So flat grounds were lifting their batters. The models now get the runs and wickets per ball of the ground, measured the same way as opponent strength.
- The balls the striker has already faced. A batter's first 10 balls averaged -0.08 and his later balls +0.08 to +0.11, so openers who bat long looked better than finishers who walk in late. The models now get the number of legal balls the striker has faced in the innings.
- While adding the ground I found that the training balls carried their own match inside the ground and opponent rates. The model then trusted the rates too much: on the held out matches, grounds and teams with a high rate scored about 0.03 runs per ball less than expected. Every training ball now gets rates from the other training folds only. The average error per ball is the same, and the expected runs of a match line up better with the real ones (slope 0.94 for batters, 0.98 for bowlers, against 0.86 before).

After the change (`outputs/03_checks.txt`, checks 5 and 6): the value left at the big IPL grounds runs from -0.10 to +0.04 (spread 0.039), every group of balls faced is within 0.01 of zero, and the average value is within about 0.01 of zero in every phase, innings, competition and bowler type. The share of variance explained by the runs models went from 0.019 to 0.029.