# Step 5: do the rankings hold? Tests, results and what each one means

This note lists every test in `notebooks/05_proof.ipynb`, the numbers it gave and what I take from them. Step 4 ranked both lists on level (value per ball over all balls, shrunk). This step tries to break that ranking, then locks the final lists. The final lists, ranked in IPL terms with a confidence number for every player, are in `outputs/05_batters.csv` and `outputs/05_bowlers.csv`.

## How the tests are built

I add the balls up once to one row per player per match. Every test is then a different way of adding those rows up: one half of the matches, one competition, or the matches drawn again with repeats. Before any test I check that these rows give back the step 4 numbers. They do: the same 57 batters and 62 bowlers, the same top 10s, and the level and consistency of every player to the fourth decimal.

All tests split or draw whole matches, never single balls, because balls of one match share the pitch and the conditions.

## Test 1: split-half

I split the matches into two random halves 100 times. In every split each ranked player is measured in both halves, and I take the correlation between the halves over the ranked players.

| | Batters | Bowlers |
|---|---|---|
| Level | 0.36 | 0.20 |
| High pressure value | -0.04 | 0.21 |
| Clutch (high pressure balls minus his other balls) | -0.24 | 0.07 |
| Clutch, pressure from the rule index | -0.04 | 0.01 |
| Consistency | 0.08 | 0.27 |

The spread from split to split is about 0.09 for every number.

- Level comes back in the other half. It is above 0 in 100% of the splits for batters and 98% for bowlers.
- Clutch does not. To see how far from 0 chance alone can take it, I shuffled inside every player which of his balls are called high pressure (30 times, as in step 4) and ran the same split-half. The shuffled numbers run from -0.26 to +0.23 for batters and from -0.24 to +0.25 for bowlers. The real bowler number (+0.07) is in the middle of that. The real batter number (-0.24) is at the low end: only 3% of the shuffles are as low.
- A negative number cannot be a skill. It says a batter who looked clutch in one half looked the opposite in the other. It is the same fact as step 4's "true spread of clutch 0.000" seen a second way: the clutch numbers of batters are spread out even a little less than luck alone would give. I read it as chance at the edge and have no cricket reason for it.
- This answers the Rajat Patidar question from step 4. His low value on 132 high pressure balls is treated as luck, and the test says that is right.
- Consistency (share of pressure matches above the average player) comes back for bowlers (0.27) and hardly for batters (0.08). It stays next to the rank and out of the score, as decided in step 4.

## Test 1b: level, high pressure balls or a blend?

Score = w times level + (1 - w) times high pressure value, built in one half. Target = the high pressure value in the other half. 100 splits, both directions, so 200 tries.

| Weight on level | Batters | Bowlers |
|---|---|---|
| 0.0 (high pressure balls only) | -0.04 | 0.21 |
| 0.5 | 0.06 | 0.24 |
| 0.7 | 0.12 | 0.24 |
| 1.0 (level only) | 0.21 | 0.22 |

- Batters: every bit of weight on the high pressure balls makes the prediction worse. Level alone is the best weight in 196 of 200 tries.
- Bowlers: the best blend (0.7) beats level by 0.02 and the spread is 0.10. The best weight jumps around: level alone in 46 tries, high pressure balls alone in 36, the rest in between. A blend of 0.7 would also swap 4 of the 10 names, two of them the players step 4 took out as noise picks.
- Decision: both lists stay ranked on level. The numbers are low because the target is noisy (half of a player's high pressure balls), not because level is a weak measure.

What I cannot claim: for bowlers the high pressure balls alone predict as well as the level does, with a fifth of the balls. That hints at something real in how bowlers handle pressure, but neither this test nor the shuffle test of step 4 can separate it from chance.

## Test 2: IPL against T20I

- A player's IPL level and his T20I level agree only loosely: correlation 0.32 for batters (37 players with 300 or more balls in both) and 0.48 for bowlers (31 players). Each is measured on half the balls, so I expected something near the split-half numbers, and that is what it is.
- T20I balls are easier. The same player is 0.10 runs per ball better in T20Is than in the IPL as a batter (give or take 0.03) and 0.04 as a bowler (give or take 0.03). The value model knows the competition and the strength of the opponent, but the average T20I player it compares with is weaker than the average IPL player.
- That could lift players with many T20I balls, so I took the gap off every T20I ball and ranked again. Both top 10s keep the same 10 names. The order moves by one or two places: Klaasen goes from 4th to 2nd, Patidar passes Salt, Sudharsan passes Head, Narine passes Ellis and Rashid Khan passes Mustafizur.
- On IPL balls alone 8 of 10 batters stay (Jos Buttler and Mitchell Marsh out, Shreyas Iyer and Shubman Gill in) and 7 of 10 bowlers (Nathan Ellis, Mustafizur Rahman and Rashid Khan out, Prasidh Krishna, Kagiso Rabada and Trent Boult in). The rank correlation with my score is 0.90 for both.
- Ellis (34% IPL balls) and Mustafizur (32%) are the two players who lean most on T20I balls. The report says so in their auction notes.

Decision: the final lists are ranked in IPL terms, with the gap taken off every T20I ball. The lists are for an IPL auction, so a player's T20I balls should count at what they are worth in the IPL. The names are the same either way, so this is a choice of order, not of players. The correction is one number for all players, which is the simplest fix that the data supports; a player who is much better or worse in T20Is than the average gap is not corrected for that.

## Test 3: the rule index

The lists are ranked on level, and the level does not use the pressure score. Pressure only decides who has enough high pressure balls and pressure matches to be ranked. I picked the top fifth of balls with the simple rule index of step 2 and built the lists again. The two definitions are very different ball by ball: only 7% of all balls are high in both.

- Bowlers: all 10 stay.
- Batters: 7 stay. Abhishek Sharma, Rajat Patidar and Travis Head go, and Andre Russell, Tilak Varma and Shreyas Iyer come in. The three who go are not ranked lower, they are not ranked at all: under the rule index they have 9, 9 and 5 pressure matches against the minimum of 10.
- The value on high pressure balls itself agrees only loosely under the two definitions (rank correlation 0.45 for batters, 0.49 for bowlers). That is one more reason not to rank on the high pressure balls alone: that number depends on how pressure is defined, the level does not.

## Test 4: eligibility

My pick was 100 (batters) or 120 (bowlers) high pressure balls and 10 pressure matches, half of both in the IPL.

- The ball minimum hardly matters. From 60 to 150 for batters only Rajat Patidar drops out at 150 (he has 132). From 72 to 180 for bowlers nothing changes.
- The match minimum matters for batters. With 5 matches, Vaibhav Sooryavanshi and Andre Russell come in for Buttler and Marsh. With 15 matches only 27 batters are ranked, and Klaasen, Salt and Patidar are not among them.
- Bowlers keep 10 of 10 at 5 and 10 matches and 9 of 10 at 15 (Nathan Ellis has 13).

I keep 10 matches. Sooryavanshi is the name to mention: he is a Rajasthan Royals player and would be in the list with a lower minimum, but under 10 pressure matches I cannot tell him from a hot streak.

## Final lists and rank confidence

The final lists are ranked on the level in IPL terms (test 2). Then I draw the same number of matches again with repeats, 1,000 times, and rank the players again every time. The ranked players, the pool and the T20I gap stay fixed, so this shows only how far luck in the matches moves a rank.

| Rank | Batter | Step 4 rank | In the top 10 | | Bowler | Step 4 rank | In the top 10 |
|---|---|---|---|---|---|---|---|
| 1 | Abhishek Sharma | 1 | 97% | | Jasprit Bumrah | 1 | 94% |
| 2 | Heinrich Klaasen | 4 | 98% | | Josh Hazlewood | 2 | 78% |
| 3 | Suryakumar Yadav | 2 | 94% | | Matheesha Pathirana | 3 | 85% |
| 4 | Tim David | 3 | 89% | | Sunil Narine | 5 | 74% |
| 5 | Rajat Patidar | 6 | 87% | | Nathan Ellis | 4 | 71% |
| 6 | Phil Salt | 5 | 68% | | Bhuvneshwar Kumar | 6 | 50% |
| 7 | Sai Sudharsan | 8 | 70% | | Varun Chakravarthy | 7 | 45% |
| 8 | Travis Head | 7 | 52% | | Mohsin Khan | 8 | 60% |
| 9 | Jos Buttler | 9 | 32% | | Rashid Khan | 10 | 30% |
| 10 | Mitchell Marsh | 10 | 33% | | Mustafizur Rahman | 9 | 36% |

Closest outside: David Warner 24%, Cameron Green 25%, Shubman Gill 16% for batters. Kagiso Rabada 31%, Lockie Ferguson 37%, Krunal Pandya 28% for bowlers.

- "In the top 10 in 97% of the draws" means: if the same players had played a different but similar set of matches, he would still be in the top 10 in 97 of 100 cases.
- The first 7 batters and the first 5 bowlers are firm. The last places are close calls between about 8 players, and the report says so.
- Ferguson has a higher share than Rashid Khan although his level is lower. He has fewer balls (1,138 against 2,780), so his rank swings more in both directions. The list is ranked on the best guess of the level, not on the swing.
- No batter outside the top 10 has a higher share than the ninth and tenth batters (the best is Cameron Green at 25%, against 32% and 33%). For bowlers, Ferguson (37%) and Rabada (31%) are level with the ninth and tenth (30% and 36%).

## The lists are locked

Batters: Abhishek Sharma, Heinrich Klaasen, Suryakumar Yadav, Tim David, Rajat Patidar, Phil Salt, Sai Sudharsan, Travis Head, Jos Buttler, Mitchell Marsh.

Bowlers: Jasprit Bumrah, Josh Hazlewood, Matheesha Pathirana, Sunil Narine, Nathan Ellis, Bhuvneshwar Kumar, Varun Chakravarthy, Mohsin Khan, Rashid Khan, Mustafizur Rahman.

## What goes in the limitations

- Clutch as its own skill does not show in this data, for batters or bowlers. The lists rank the players who are best against an average player in the same situations, and that is the best guess of who is best under pressure.
- Places 8 to 10 of the batters and 6 to 10 of the bowlers are close calls.
- T20I balls are easier than IPL balls by 0.04 to 0.10 runs per ball. The final lists take one average gap off every T20I ball. The names do not change with or without it.
- The batter list depends on the minimum of 10 pressure matches.

## Output

`outputs/05_batters.csv` and `outputs/05_bowlers.csv`: the final lists, every ranked player in the final order. `rank` is the final rank and `step4_rank` the rank from step 4. `ipl_level` is the level in IPL terms that the final rank uses. `top10_share` is the share of the 1,000 draws with the player in the top 10, `place_median` is his middle place, and 90% of the draws put him between `place_low` and `place_high`. The other columns come from step 4.
