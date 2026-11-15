# Step 6: the report, decisions and where every number comes from

The report is `report/superr_report.pdf` (9 pages, A4). It is printed from `report/superr_report.html` by `src/06_report.py` with Edge or Chrome. `src/06_facts.py` makes the per player and Royals tables, `src/06_charts.py` draws the charts in `report/charts/`.

## Choices

- PDF, not slides. The submission page accepts a PDF or a PPT. The report has to carry a method, tests and 20 player texts, which reads better as a document. Page 1 is a stand alone summary with the main chart in case a judge only reads that.
- Order follows the submission page. Methodology (sections 1 to 5), the most reliable players (page 1 and section 4), then how each player could strengthen the Royals (section 6). Section 5 holds the limitations, including the ones that weaken my own result.
- Fit uses only what the data can say. Retention, who reaches the auction, prices, overseas slots, age, fitness, keeping and fielding are not in the data, so the report says that and defines "fit" as two things: where the player's own numbers are strong, and where the Royals' numbers show room.
- The Royals' numbers are IPL 2025 and 2026 only. That is 30 matches and 3,382 balls batted and 3,691 bowled, the most recent two seasons and the ones an auction looks at. They are compared with the other nine teams over the same two seasons, because the value model is not centred on zero for 2025 and 2026 (the other teams average +0.07 as batters). The gap to the other teams is the fair number.
- Luck bands on every Royals number. I show 2 standard errors, taken from the ball values. Balls of one match are not independent, so the true band is about 10% wider. Only the powerplay batting gap (+0.32 against a band of 0.24) is clearly bigger than luck. The report says everything else is a hint, and it uses "if those gaps are real" and "if they are luck" in the same paragraph.
- Player numbers by phase, type, innings, competition and year are plain averages with the balls behind them. They are not shrunk. The ranking itself is shrunk. I say this under the Royals chart, and splits with fewer than about 300 balls are called hints.
- No claim about who is on the Royals roster. `outputs/06_rr_players.csv` lists who batted or bowled 60 or more balls for the Royals in IPL 2026. I did not use it in the text, because the data does not say who stays.
- No name, no team claims for players. The `team` column in the final lists is the team a player played most for in the data, so I do not print it.

## Where the numbers in the text come from

| Numbers | Source |
|---|---|
| 200,961 balls, 867 matches (367 IPL, 470 T20I, 30 other T20), 812 clean matches | `outputs/01_checks.txt` |
| Brier 0.178 against 0.250, 70% calibration, biggest gap 2.6 points, first innings 0.223, second 0.129, 92.1 / 36.3 / 13.1 | `report/notes/step2_pressure_decisions.md`, `outputs/02_checks.txt` |
| 3 signals, runs 0.10 to 0.23 lower, t 7 to 23 | `report/notes/step2_pressure_decisions.md` |
| Wicket cost 18.2, 7.6, 1.9; value within 0.006 of zero; error gap under 0.02 | `outputs/03_checks.txt` |
| True spread 0.103 and 0.072, match factor 1.1, 67 and 85 eligible, 57 and 62 ranked | `report/notes/step4_player_curves_decisions.md` |
| Shuffle test 0.05, 90% below 0.10, 0.000 and 0.057, planted skill 0.104 | `report/notes/step4_player_curves_decisions.md` |
| Split half, blend table, 196 of 200, rank confidence, T20I gap 0.10 and 0.04, test table | `outputs/05_splithalf.csv`, `outputs/05_blend.csv`, `outputs/05_batters.csv`, `outputs/05_bowlers.csv`, `report/notes/step5_proof_decisions.md` |
| Player texts | `outputs/06_batter_facts.csv`, `outputs/06_bowler_facts.csv` |
| Royals gaps | `outputs/06_rr_profile.csv` (the script stops if a gap in the text differs from this file) |

## What I checked

- `06_facts.py`: the phase, innings, competition and year splits of every player add up to his balls, and his value over all balls equals his raw level in step 4 (largest gap 0.00005).
- `06_report.py`: every player of the final lists has a text, and the eight Royals numbers quoted in the paragraphs match `06_rr_profile.csv` (it stops otherwise).
- I read all 9 pages after printing and compared the numbers in the 20 player texts with the facts tables. One sentence was wrong and is fixed: it said Narine and Rashid Khan have the best economies, but Bumrah (7.18) is better than Rashid (7.41). Another quoted the leak correlation (-0.67) as a correlation with the result, which I cannot back up, so the number is out.
- The chart of value by year had dark numbers on dark cells, now white.
- A full review before submission found four things, all handled. (1) I recomputed batting runs, fours, sixes, legal balls and bowler wickets for four players straight from the raw csv files. Runs match exactly (Abhishek Sharma 4,178, Klaasen 2,348), Bumrah's 85 wickets match, and the small gaps are explained: oversteps are not counted as legal balls in step 1, and Narine's extra 2 wickets and 3 balls were in super overs, which step 1 drops. The 30 Royals matches in IPL 2025 and 2026 match `matches.csv`. (2) The ranking had never been tested against my own choices, so test 5 in the step 5 notebook ranks again with other wicket prices and other years. The lists move by 1 to 3 names and the report now says which players never drop. (3) The value favours scoring above the going rate, so players who rarely get out (Kohli, 17th) are ranked lower than a reader might expect. That is now a limitation. (4) Every number in the 20 player texts was checked against the facts tables by script. Only a year and one Royals gap, which the report script already asserts, were not in them.
- Rerunning notebooks 4 and 5 from top to bottom and the three step 6 scripts gives byte identical csv files (12 files compared).
- The notebook `05_proof.ipynb` got one small cell that saves the split half and blend tables for the charts (`outputs/05_splithalf.csv`, `outputs/05_blend.csv`). The tests and results are unchanged.

## Not done yet

- Step 7: read the report once from start to finish, check that the Unstop dropdown picks match the report in the same order, submit.
