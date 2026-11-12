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

Result: the average expected value matches the average actual value to the third decimal for runs (1.394 against 1.394 for batters) and for wickets. The models explain only about 2.7% of the ball to ball variation in runs. That is normal, because one ball is mostly luck. What matters is that the average is right in every situation, and check 3 below shows that.

## Opponent strength

I first used each team's share of matches won. It did not line up with runs, so I dropped it. Now the opponent is described by two rates taken from all its other matches: runs per delivery (given or scored) and wickets per delivery (taken or lost). The match being scored is left out, so a big innings in that match cannot raise the baseline it is compared with. A team with few balls is pulled towards the competition average, as if it had 600 extra balls at that average.

Inside the T20I group, batters score 1.302 per ball against teams that usually give the fewest runs, 1.328 against the middle group and 1.397 against teams that usually give the most. The model expects 1.298, 1.333 and 1.396, so it follows the pattern. Inside the IPL the gaps are tiny and the pattern is not clean, which is expected when ten teams play each other all season.

## What a wicket costs

For each phase I fitted a straight line on the first innings of complete innings: runs scored from this ball to the end of the innings against balls bowled and wickets already lost. The wicket coefficient, with the sign flipped, is the cost of one more wicket.

| Phase | Runs a wicket costs |
|---|---|
| Overs 1 to 6 | 11.8 |
| Overs 7 to 16 | 6.6 |
| Overs 17 to 20 | 1.9 |

Early wickets cost a lot because a whole innings is left to bat with one batter fewer. Late wickets cost little because few balls remain. Only first innings are used, since a chase stops as soon as the target is reached. The same cost is used for both innings. A team that loses wickets also tends to be weaker, so the cost may be a little too high. It is the same for every player, so it does not favour anyone.

## Value of a ball

- Batter: (runs off the bat minus expected runs) minus the wicket cost times (got out minus expected chance of getting out). Legal balls only.
- Bowler: (expected runs minus runs charged) plus the wicket cost times (took a wicket minus expected chance of a wicket). All deliveries, so wides and no-balls count against the bowler.

A single ball with a wicket is worth about 11 runs in the powerplay, so single ball values are very spread out (standard deviation about 3.3 in the powerplay). This is why step 4 has to shrink small samples.

## Checks

The average value over all players is close to zero in every phase, innings, competition and bowler type:

| Group | Batters | Bowlers |
|---|---|---|
| Overs 1 to 6 | +0.007 | -0.006 |
| Overs 7 to 16 | +0.002 | -0.003 |
| Overs 17 to 20 | +0.004 | -0.007 |
| IPL | +0.005 | -0.008 |
| T20I | +0.004 | -0.003 |
| Other T20 | -0.007 | +0.014 |

These are all under 0.015 runs per ball, against a ball to ball spread of 2 to 3.

By batting order the batters differ: order 1-2 is +0.026 per ball, order 3-4 +0.016, order 5-7 +0.004 and order 8-13 -0.142. I left this in on purpose. The model has no player information, so these gaps are real skill differences between batters in the same situation, not a role effect that the over and wickets down already remove. Step 4 compares each player with his own level.

## Output

`outputs/balls_value.parquet` has one row per ball (200,961 rows) with the keys, the fold, the phase, the wicket cost, the four expected values, `batter_value` and `bowler_value`. It is not in git. Run `src/03_expected.py` to make it.
