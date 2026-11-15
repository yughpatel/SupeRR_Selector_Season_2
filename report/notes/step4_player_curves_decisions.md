# Step 4: player curves and the draft top 10s, decisions and why each one is safe

This note lists every choice made in `notebooks/04_player_curves.ipynb` and the numbers behind it. The full ranked lists are in `outputs/04_batters.csv` and `outputs/04_bowlers.csv`.

## Who is ranked

IPL and T20I balls only. The 30 Other T20 matches were used to train the models in steps 2 and 3, but their players are not ranked. Batters are measured on legal balls, bowlers on every delivery.

## Does pressure change an average player?

No. The average value per ball over all players stays within 0.03 runs of zero in every one of 10 pressure groups, for batters and bowlers. So the step 3 baseline is fair at every pressure level, and a player's clutch number is not shifted by a league-wide effect.

## High pressure

A ball is high pressure if its pressure score is 80 or more: the top fifth of all balls (19.8%). I also tested cuts at 70 and 90 (see below).

## Level and clutch

For every player:

- Level: average value per ball over all his balls.
- Delta: his average on high pressure balls minus his average on his other balls.

Both are shrunk. A raw average is true skill plus luck. If true skill varies across players by tau squared and the luck in his average is L, the best guess of his skill is the average plus (raw minus average) times tau squared over (tau squared plus L). The level is pulled towards the average level of the pool (the players with enough high pressure balls: +0.057 for batters, +0.021 for bowlers), and the delta towards zero.

L is the spread of a single ball (around the player's own average, pooled over all players) divided by his number of balls, times one factor for the fact that balls in the same match are not independent: they share the pitch, the conditions and the opposition. The factor is luck measured match by match divided by luck measured ball by ball, averaged over the pool: 1.12 for batter level and 1.10 for bowler level. For the delta it is about 1.0, because a good pitch lifts a player's high pressure balls and his other balls of that match together, so that part of the luck cancels in the difference. Tau squared is the spread of the pool's raw numbers minus their average luck. If it comes out at zero, the whole spread is luck.

Score = value expected on a high pressure ball = level + (share of his balls that are not high pressure) times shrunk delta, if the clutch spread passes the test below. If it does not, the score is the level.

Shrinkage in one sentence: a player's number is pulled towards the average by as much as it could be luck, so 100 balls get pulled hard and 2,000 balls barely move.

## The main finding

| | True spread of level | True spread of clutch | Raw spread of clutch | Luck in it |
|---|---|---|---|---|
| Batters (cut 80) | 0.103 | 0.000 | 0.216 | 0.227 |
| Bowlers (cut 80) | 0.072 | 0.057 | 0.211 | 0.203 |
| Batters (cut 70) | 0.109 | 0.000 | 0.230 | 0.238 |
| Bowlers (cut 70) | 0.079 | 0.037 | 0.221 | 0.217 |
| Batters (cut 90) | 0.076 | 0.000 | 0.195 | 0.208 |
| Bowlers (cut 90) | 0.073 | 0.000 | 0.216 | 0.216 |

All in runs per ball.

Two tests of the method itself decide what these numbers mean:

1. No clutch on purpose. Inside every player I shuffle which of his balls are called high pressure, 30 times. Nobody can have a clutch skill then, so whatever spread the method finds is noise. The shuffles give 0.054 on average for batters and 0.051 for bowlers, and 90% of them are below 0.10. The real numbers are 0.000 for batters and 0.057 for bowlers. Half of the shuffles are as big as the real bowler number.
2. Known clutch on purpose. I add a made up clutch skill with a spread of 0.10 to the high pressure balls. The method finds 0.104 on average for bowlers (0.056 to 0.149) and 0.053 for batters (0.000 to 0.106).

What this says:

- Neither batters nor bowlers show a clutch spread above the noise. I use clutch only if the real spread is above 90% of the shuffles, so clutch is set to zero for both, and both lists are ranked on level.
- I cannot say clutch does not exist. The data can only see a clutch spread of about 0.10 runs per ball or more, which is as big as the whole spread in level. A smaller clutch skill could be there and this data could not show it. That goes in the limitations.
- The best guess of how a player does on a high pressure ball is then his overall level, measured against an average player in the same situations. This is the outcome my plan said to expect if clutch is weak: lean on base level and say so.

## Eligibility

| Minimum high pressure balls | 5+ pressure matches | 10+ | 15+ |
|---|---|---|---|
| Batters 60 / 100 / 150 | 150 / 120 / 79 | 67 / 67 / 64 | 30 / 30 / 30 |
| Bowlers 60 / 120 / 180 | 153 / 102 / 69 | 85 / 85 / 69 | 53 / 53 / 53 |

A pressure match is a match where the player had 6 or more high pressure balls. My pick: 100 or more high pressure balls for batters, 120 or more for bowlers (they bowl more balls in a match), and 10 or more pressure matches, about one full season of tight finishes. The ball minimum barely changes who is in. The match minimum is the one that bites. This leaves 67 batters and 85 bowlers.

IPL rule: the submission page asks how each player could strengthen the Rajasthan Royals at the IPL 2027 auction, so the list must hold players an IPL team can sign. A player must also have a real IPL sample: half of the ball minimum (50 high pressure balls for batters, 60 for bowlers) and 5 or more pressure matches in the IPL itself. His T20I balls still count as evidence. This is a rule on the data and not on nationality, but it removes every player with no IPL record since 2022, which includes all the Pakistan players. It leaves out 10 batters (the best are Reeza Hendricks, Glenn Phillips, Mohammad Rizwan) and 23 bowlers (Blessing Muzarabani, Haris Rauf, Mohammad Nawaz), and 57 batters and 62 bowlers stay.

## Consistency

For every player: in his pressure matches, the share where his total value was above the average player. It is shown next to the score, but not added into it. Over 10 to 30 matches it is noisy, and adding it would need a weight I could not justify. Step 5 checks it.

## Draft top 10s

Batters: Abhishek Sharma, Suryakumar Yadav, Tim David, Heinrich Klaasen, Phil Salt, Rajat Patidar, Travis Head, Sai Sudharsan, Jos Buttler, Mitchell Marsh.

Bowlers: Jasprit Bumrah, Josh Hazlewood, Matheesha Pathirana, Nathan Ellis, Sunil Narine, Bhuvneshwar Kumar, Varun Chakravarthy, Mohsin Khan, Mustafizur Rahman, Rashid Khan.

## Checks on the lists

- No tilt to chasers: the top 10 batters have 55% of their balls in the first innings, against 52% for all eligible batters. Bowlers: 52% against 51%.
- No team dominates: Sunrisers Hyderabad have 3 of the top 10 batters, every other team 1 or 2. The value model leaves the player's own team out, so a strong team could give a small head start. Three SRH batters fits their real 2024 season, so I keep it and mention it.
- The batter score has a rank correlation of 1.00 with raw level (it is shrunk level), and 0.70 with the raw high pressure value. For bowlers it is 0.99 and 0.73.
- Cricket sense: among the eligible players the score has a rank correlation of +0.74 with strike rate and +0.70 with batting average for batters, and -0.69 with economy for bowlers. The top 10 batters all strike at 149 to 187.
- Surprising name: Rajat Patidar is 6th on level (0.295 per ball over 916 balls) but only 0.069 on his 132 high pressure balls, and above the average player in 3 of his 10 pressure matches. With clutch at zero, those balls are treated as luck. Step 5's split-half test checks whether that is right.
- Form over time: the value is an average over 2022 to 2026 with every year counted the same. Some top 10 players are lower in the last two seasons (Travis Head -0.06 and +0.03 per ball in 2025 and 2026 after +0.51 in 2024, Hazlewood, Bumrah and Varun Chakravarthy slightly below zero in 2026). For an auction this matters, so the report shows each player's value by season.

## Verification

What I checked after building the step:

- Steps 1 to 3 rerun in a fresh virtual environment from `requirements.txt` (pandas 3.1.1) give exactly the same tables and check files. This caught one bug: I had removed scikit-learn from `requirements.txt`, but LightGBM's `LGBMClassifier` and `LGBMRegressor` need it, so steps 2 and 3 failed in a clean install. It is back in, with a comment saying why.
- I recomputed balls, high pressure balls, raw level, raw high pressure value, pressure matches and consistency by hand for Abhishek Sharma, Rajat Patidar and Josh Hazlewood. All match the notebook exactly.
- Fixed: the first version measured luck ball by ball, as if every ball were independent. Balls in the same match are not, so that luck was about 10% too small and made bowler clutch look bigger and steadier than it is (about 0.06 at every cut, against 0.046 at the cut of 80 and 0 at 70 and 90 now). The factor above fixes it. Measuring each player's own luck match by match was worse: from 10 to 30 matches it is too noisy and swapped 1 or 2 names in each top 10 by itself. With the single factor the top 10s have the same 20 players as before, in a slightly different order.
- Fixed in a later check: the shuffle and made up clutch tests above were added because the method had never been tested on a case with a known answer. They showed two things. The bowler clutch (0.046 then, 0.057 now) is no bigger than what shuffled labels give, so it is noise and is no longer used. That takes Kagiso Rabada and Mitchell Santner out of the bowler top 10, who were there on that noise, and brings in Mohsin Khan and Rashid Khan. And the luck in the delta did not allow for the luck that high pressure and other balls of the same match share, which is fixed.
- Fixed in the same check: the level was pulled towards zero, but the spread was measured around the pool average. It is now pulled towards the pool average, which is the correct pair. The batter top 10 does not change.

## Output

`outputs/04_batters.csv` and `outputs/04_bowlers.csv`: every eligible player, ranked, with his balls, high pressure balls, pressure matches, first innings share, raw and shrunk numbers, score and consistency.

## Rerun after the step 3 change (Nov 15)

Step 3 now knows the ground and the balls a batter has already faced. The numbers above are from the first version. After the change:

- True spread of level 0.094 for batters and 0.075 for bowlers. Clutch spread 0.000 for batters and 0.048 for bowlers, against shuffles that average 0.055 and 0.049 (90% below 0.10). Clutch is still set to zero for both. The planted clutch of 0.10 is found at 0.099 for bowlers and 0.068 for batters.
- Draft batters: Abhishek Sharma, Tim David, Suryakumar Yadav, Klaasen, Salt, Patidar, Marsh, Pooran, Buttler, Sudharsan. Travis Head (an opener who batted a lot on flat grounds) left, Nicholas Pooran came in.
- Draft bowlers: Bumrah, Hazlewood, Ellis, Narine, Bhuvneshwar Kumar, Chakravarthy, Pathirana, Mustafizur, Rashid Khan, Santner. Mohsin Khan left, Mitchell Santner came in.
- No team has more than two players in either list now.
- The final lists in IPL terms are made in step 5.