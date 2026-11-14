# Step 4: player curves and the draft top 10s, decisions and why each one is safe

This note lists every choice made in `notebooks/04_player_curves.ipynb` and the numbers behind it. The full ranked lists are in `outputs/04_batters.csv` and `outputs/04_bowlers.csv`.

## Who is ranked

IPL and T20I balls only. The 30 Other T20 matches were used to train the models in steps 2 and 3, but their players are not ranked. Batters are measured on legal balls, bowlers on every delivery.

## Does pressure change an average player?

No. The average value per ball over all players stays within 0.03 runs of zero in every one of 10 pressure groups, for batters and bowlers. So the step 3 baseline is fair at every pressure level, and a player's clutch number is not shifted by a league-wide effect.

## High pressure

A ball is high pressure if its pressure score is 80 or more: the top fifth of all balls (19.8%). I tested cuts at 70 and 90 and the main finding does not change (see below).

## Level and clutch

For every player:

- Level: average value per ball over all his balls.
- Delta: his average on high pressure balls minus his average on his other balls.

Both are shrunk towards zero. A raw average is true skill plus luck. If true skill varies across players by tau squared and the luck in his n balls is s squared over n, the best guess of his skill is the raw number times tau squared over (tau squared plus s squared over n). The luck of a single ball is measured as the spread of each ball around the player's own average, pooled over all players. Tau squared is measured from the players with enough high pressure balls: the spread of their raw numbers minus their average luck. If it comes out at zero, the whole spread is luck, and every player is pulled all the way to zero.

Score = value expected on a high pressure ball = level + (share of his balls that are not high pressure) times shrunk delta. The share is there because his overall level already includes his high pressure balls.

Shrinkage in one sentence: a player's number is pulled towards the average by as much as it could be luck, so 100 balls get pulled hard and 2,000 balls barely move.

## The main finding

| | True spread of level | True spread of clutch | Raw spread of clutch | Luck in it |
|---|---|---|---|---|
| Batters (cut 80) | 0.108 | 0.000 | 0.216 | 0.228 |
| Bowlers (cut 80) | 0.077 | 0.062 | 0.211 | 0.202 |
| Batters (cut 70) | 0.119 | 0.000 | 0.230 | 0.232 |
| Bowlers (cut 70) | 0.087 | 0.060 | 0.221 | 0.212 |
| Batters (cut 90) | 0.076 | 0.000 | 0.195 | 0.226 |
| Bowlers (cut 90) | 0.077 | 0.064 | 0.216 | 0.207 |

All in runs per ball.

- Batters: the difference between how batters do under pressure and how they do otherwise is no bigger than luck would make it. I cannot find a clutch skill for batters in this data. The best guess of how a batter will do on a high pressure ball is his overall level, so the batter list is ranked on level. This is the outcome my plan said to expect if clutch is weak: lean on base level and say so.
- Bowlers: there is a real clutch spread, nearly as big as the spread in level, and it holds at every cut. It moves a few bowlers (Hazlewood and Rabada up, Bumrah down) without taking over the ranking.

Why I rank on level and clutch together: the brief asks who performs best under pressure, not who changes most. A great bowler who is a little worse under pressure can still be better under pressure than an average bowler who rises to it. Level plus clutch is exactly "how good on a high pressure ball".

## Eligibility

| Minimum high pressure balls | 5+ pressure matches | 10+ | 15+ |
|---|---|---|---|
| Batters 60 / 100 / 150 | 150 / 120 / 79 | 67 / 67 / 64 | 30 / 30 / 30 |
| Bowlers 60 / 120 / 180 | 153 / 102 / 69 | 85 / 85 / 69 | 53 / 53 / 53 |

A pressure match is a match where the player had 6 or more high pressure balls. My pick: 100 or more high pressure balls for batters, 120 or more for bowlers (they bowl more balls in a match), and 10 or more pressure matches, about one full season of tight finishes. The ball minimum barely changes who is in. The match minimum is the one that bites. This leaves 67 batters and 85 bowlers.

## Consistency

For every player: in his pressure matches, the share where his total value was above the average player. It is shown next to the score, but not added into it. Over 10 to 30 matches it is noisy, and adding it would need a weight I could not justify. Step 5 checks it.

## Draft top 10s

Batters: Abhishek Sharma, Suryakumar Yadav, Tim David, Heinrich Klaasen, Phil Salt, Rajat Patidar, Travis Head, Sai Sudharsan, Reeza Hendricks, Jos Buttler.

Bowlers: Josh Hazlewood, Matheesha Pathirana, Sunil Narine, Jasprit Bumrah, Kagiso Rabada, Nathan Ellis, Mitchell Santner, Varun Chakravarthy, Mohammad Nawaz, Bhuvneshwar Kumar.

## Checks on the lists

- No tilt to chasers: the top 10 batters have 55% of their balls in the first innings, against 53% for all eligible batters. Bowlers: 50% against 51%.
- No team dominates: Sunrisers Hyderabad have 3 of the top 10 batters, every other team 1 or 2. The value model leaves the player's own team out, so a strong team could give a small head start. Three SRH batters fits their real 2024 season, so I keep it and mention it.
- The batter score has a rank correlation of 1.00 with raw level (it is level), and 0.69 with the raw high pressure value. For bowlers it is 0.95 and 0.83.
- Surprising name: Rajat Patidar is 6th on level (0.295 per ball over 916 balls) but only 0.069 on his 132 high pressure balls, and above the average player in 3 of his 10 pressure matches. With batter clutch at zero, those balls are treated as luck. Step 5's split-half test checks whether that is right.

## Output

`outputs/04_batters.csv` and `outputs/04_bowlers.csv`: every eligible player, ranked, with his balls, high pressure balls, pressure matches, first innings share, raw and shrunk numbers, score and consistency.
