# SupeRR Selector Season 2 - Round 1

My work for Round 1 of the Rajasthan Royals SupeRR Selector hackathon. The task is to rank the 10 best batters and the 10 best bowlers under pressure, using IPL and T20I ball by ball data from 2022 onwards.

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

Run the scripts in `src/` in order of their number. Each one reads the output of the one before it.

## Steps

| Step | Script | What it does | Status |
|---|---|---|---|
| 1 | `src/01_clean.py` | Cleans the ball by ball data and finds the match state before every ball | Done |
| 2 | `src/02_pressure.py` | Gives every ball a pressure score | Done |
| 3 | `src/03_expected.py` | Compares every ball with what an average player would do | Done |
| 4 | `src/04_player_curves.py` | Builds the player curves and the draft top 10s | Not started |
| 5 | `src/05_proof.py` | Tests if the rankings hold | Not started |
| 6 | `src/06_charts.py` | Draws the charts for the report | Not started |

## Folders

- `src/` has the scripts
- `outputs/` has the tables and check files made by the scripts
- `report/notes/` has one note per step with every decision and the reason for it
