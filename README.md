# SupeRR Selector Season 2 - Round 1

My work for Round 1 of the Rajasthan Royals SupeRR Selector hackathon. The task is to rank the 10 best batters and the 10 best bowlers under pressure, using IPL and T20I ball by ball data from 2022 onwards.

## Final lists

Ranked on value per ball above an average player in the same situation (over, wickets, innings, balls already faced, pace or spin, competition, opponent and ground), with small samples pulled towards the average (for bowlers, runs saved and wickets are pulled apart, because wickets are mostly luck) and T20I balls adjusted to IPL terms. Only players with a real IPL sample are ranked, because the lists are for the IPL 2027 auction. "In top 10" is the share of 1,000 redraws of the matches in which the player stays in the top 10.

| # | Batter | In top 10 | Bowler | In top 10 |
|---|---|---|---|---|
| 1 | Abhishek Sharma | 97% | Jasprit Bumrah | 100% |
| 2 | Tim David | 97% | Sunil Narine | 98% |
| 3 | Suryakumar Yadav | 98% | Nathan Ellis | 85% |
| 4 | Heinrich Klaasen | 95% | Matheesha Pathirana | 72% |
| 5 | Rajat Patidar | 89% | Mustafizur Rahman | 75% |
| 6 | Phil Salt | 68% | Josh Hazlewood | 60% |
| 7 | Sai Sudharsan | 52% | Bhuvneshwar Kumar | 60% |
| 8 | Mitchell Marsh | 46% | Varun Chakravarthy | 39% |
| 9 | Nicholas Pooran | 38% | Rashid Khan | 40% |
| 10 | Jos Buttler | 35% | Mitchell Santner | 37% |

The full ranked lists are in `outputs/05_batters.csv` and `outputs/05_bowlers.csv`, and the reasons and tests are in `report/superr_report.pdf`. I found no clutch skill beyond a player's overall level in this data, so the lists rank on level. The players who stay in the top 10 under every change I tried are Abhishek Sharma, Tim David, Klaasen, Patidar, Bumrah, Narine and Ellis. The last places of both lists are close calls.

## Data

The raw data is not in this repo. Put these files from the competition in the project folder before running anything:

- `ball_by_ball.csv`
- `matches.csv`
- `competitions.csv`
- `teams.csv`
- `playing_eleven.csv`
- `competition_team_player_mapping.csv`

## How to run

```
pip install -r requirements.txt
python src/01_clean.py
python src/02_pressure.py
python src/03_expected.py
```

Then run `notebooks/04_player_curves.ipynb` and `notebooks/05_proof.ipynb` from top to bottom (PyCharm or Jupyter).

Then the report:

```
python src/06_facts.py
python src/06_charts.py
python src/06_report.py
```

`06_report.py` prints the PDF with Edge or Chrome, so one of them has to be installed. The result is `report/superr_report.pdf`.

Run the steps in order of their number. Each one reads the output of the ones before it.

## Steps

| Step | Script | What it does | Status |
|---|---|---|---|
| 1 | `src/01_clean.py` | Cleans the ball by ball data and finds the match state before every ball | Done |
| 2 | `src/02_pressure.py` | Gives every ball a pressure score | Done |
| 3 | `src/03_expected.py` | Compares every ball with what an average player would do | Done |
| 4 | `notebooks/04_player_curves.ipynb` | Builds the player curves and the draft top 10s | Done |
| 5 | `notebooks/05_proof.ipynb` | Tests if the rankings hold | Done |
| 6 | `src/06_facts.py`, `src/06_charts.py`, `src/06_report.py` | Makes the player and Royals tables, draws the charts and prints the report PDF | Done |

## Folders

- `src/` has the scripts
- `notebooks/` has the notebooks
- `outputs/` has the tables and check files made by the scripts
- `report/notes/` has one note per step with every decision and the reason for it
- `report/` also has the final report (`superr_report.pdf`, built from `superr_report.html`) and its charts in `report/charts/`
