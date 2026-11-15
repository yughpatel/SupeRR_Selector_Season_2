# Step 6c : The report (PDF)
#
# Run from the project folder : python src/06_report.py
# Reads  : the tables and charts of steps 2 to 6 (outputs/ and report/charts/)
# Writes : report/superr_report.html and report/superr_report.pdf (the PDF is printed from the HTML with Edge or Chrome)
#
# The text is mine, written from the notes in report/notes/. The numbers in tables come from the csv files,
# the numbers inside sentences were copied from the check files and the notebooks and are listed in step6_report_decisions.md.

# Importing Libraries
import os
import subprocess
import pandas as pd

folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
output_folder = os.path.join(folder, "outputs")
report_folder = os.path.join(folder, "report")
html_path = os.path.join(report_folder, "superr_report.html")
pdf_path = os.path.join(report_folder, "superr_report.pdf")

# Loading Dataset
batters = pd.read_csv(os.path.join(output_folder, "05_batters.csv"), index_col=0)
bowlers = pd.read_csv(os.path.join(output_folder, "05_bowlers.csv"), index_col=0)
blend = pd.read_csv(os.path.join(output_folder, "05_blend.csv"), index_col=0)
rr_profile = pd.read_csv(os.path.join(output_folder, "06_rr_profile.csv"))


# One chart, as an image with a caption
def picture(path, caption, width="100%"):
    return f'<figure style="width:{width}"><img src="{path}"><figcaption>{caption}</figcaption></figure>'


# The 10 players of one list as a table : balls, pressure matches, share of them above the average player, level and top 10 share
def list_table(table, kind):
    rows = ""
    for rank, row in table.head(10).iterrows():
        rows += (f"<tr><td>{row['rank']}</td><td class='left'>{row['name']}</td><td>{row['balls']:,}</td>"
                 f"<td>{int(row['pressure_matches'])}</td><td>{row['beat_average']:.0%}</td>"
                 f"<td>{row['ipl_level']:+.3f}</td><td>{row['top10_share']:.0%}</td></tr>")
    return (f"<table class='numbers'><tr><th>#</th><th class='left'>{kind}</th><th>Balls</th><th>Pressure matches</th>"
            f"<th>Above average in</th><th>Value per ball</th><th>In top 10</th></tr>{rows}</table>")


# The fit table : one row per player, three short texts
def fit_table(table, texts):
    rows = ""
    for rank, row in table.head(10).iterrows():
        says, fit, watch = texts[row['name']]
        rows += (f"<tr><td class='name'><b>{row['rank']}. {row['name']}</b></td><td>{says}</td><td>{fit}</td><td>{watch}</td></tr>")
    return ("<table class='fit'><tr><th>Player</th><th>What the data says</th><th>How he could strengthen the Royals</th>"
            f"<th>Watch out</th></tr>{rows}</table>")


# Reading the Rajasthan Royals table : the gap and the luck band of one row
def rr(side, split):
    row = rr_profile[(rr_profile['side'] == side) & (rr_profile['split'] == split)].iloc[0]
    return row['gap'], 2 * row['rr_se']


batter_texts = {
    'Abhishek Sharma': (
        "Left-hand opener, strike rate 187. Overs 1 to 6: +0.40 per ball (1,501 balls). Against spin +0.55 (715 balls), against pace +0.24. +0.56 and +0.49 in 2025 and 2026.",
        "An attacking left-hand opener who is best against spin. The Royals' powerplay batting is already their strength, so he adds quality at the top more than he fixes a gap.",
        "Below zero in 2022 (-0.02) and 2023 (-0.29). His IPL balls alone give +0.17 and his T20I balls +0.54, so his value drops from 0.26 to 0.23 in IPL terms."),
    'Tim David': (
        "Finisher (usually bats 6). Overs 17 to 20: +0.39 (451 balls). Overs 7 to 16: +0.30 (698). Against pace +0.37, against spin +0.30. Above the average player in 14 of his 18 pressure matches.",
        "A finisher for overs 17 to 20, the phase where the Royals' batting is furthest below the other teams.",
        "The +0.65 in 2025 lifts his average, and he had +0.09 in 2023. Only 53% of his balls are IPL balls (+0.27 on those, +0.44 in T20Is)."),
    'Suryakumar Yadav': (
        "Bats 4. Overs 7 to 16: +0.31 (1,848 balls). Overs 17 to 20: +0.38 (246). Against pace +0.26 and spin +0.29. Above the average player in 20 of his 30 pressure matches.",
        "No weak phase and no weak bowler type. He covers overs 7 to 20, the stretch where the Royals' batting is below the other teams.",
        "+0.15 and +0.17 in 2024 and 2025 after +0.36 and +0.34 before, then +0.23 in 2026. He drops out of the top 10 when only 2025 and 2026 count."),
    'Heinrich Klaasen': (
        "Middle order (usually bats 5). Overs 7 to 16: +0.29 (1,016 balls). Overs 17 to 20: +0.17 (291). Against spin +0.49 (606 balls). Above the average player in 12 of his 14 pressure matches.",
        "A middle overs batter who attacks spin, which is where the Royals' batting is below the other teams (overs 7 to 16, and against spin).",
        "Only +0.08 against pace (802 balls). His T20I value (+0.04) is far below his IPL value (+0.29). Only 101 balls in the powerplay, so not an opener."),
    'Rajat Patidar': (
        "Bats 4, all 916 balls in the IPL. Overs 7 to 16: +0.30 (656 balls). Against spin +0.45 (349 balls), against pace +0.16. +0.46 in 2026 and +0.03 in 2025.",
        "A middle overs batter against spin, the other batting gap of the Royals.",
        "The smallest batter sample on the list. He was above the average player in 3 of his 10 pressure matches, the lowest share of the ten batters."),
    'Phil Salt': (
        "Opener. Overs 1 to 6: +0.27 (972 balls). Overs 7 to 16: +0.13. Between +0.21 and +0.32 in every year from 2022 to 2025. Above the average player in 13 of his 15 pressure matches.",
        "A powerplay opener. The Royals' powerplay batting is already strong, so he is cover for the top order and not a fix.",
        "0.00 in 2026 (252 balls). Only 44% of his balls are IPL balls (+0.13 on those), and he has 6 IPL pressure matches, just above the minimum of 5."),
    'Sai Sudharsan': (
        "Left-hand opener, all 1,674 balls in the IPL, strike rate 149 (the lowest of the ten). Overs 1 to 6: +0.21. Overs 7 to 16: +0.11. Out once in 33 balls. 24 pressure matches.",
        "A left-hand top order batter with a clean IPL record. His value comes from rarely getting out more than from boundaries.",
        "The slowest scorer of the ten, and -0.04 in overs 17 to 20 (98 balls). He drops out of the top 10 when a wicket costs less. Top 10 in 50% of the redraws."),
    'Mitchell Marsh': (
        "Opener. Overs 1 to 6: +0.26 (909 balls). Against pace +0.22, against spin +0.05 (585 balls). About zero from 2022 to 2024, then +0.30 and +0.22.",
        "A powerplay batter who hits pace. Both are already strengths of the Royals, so he adds little to their gaps.",
        "-0.22 in overs 17 to 20 (69 balls) and weak against spin. A close call: top 10 in 44% of the redraws."),
    'Nicholas Pooran': (
        "Left-hander, usually bats 4. Overs 1 to 6: +0.39 (390 balls). Overs 7 to 16: +0.08 (1,256). Overs 17 to 20: +0.11 (319). +0.31, +0.19 and +0.40 from 2023 to 2025.",
        "A left-hander for the middle order, but his middle overs number is ordinary. His best balls are in the powerplay.",
        "-0.28 in 2026 (182 balls). He drops out of the top 10 in 5 of the 7 changes of section 4, and he is in it in 35% of the redraws."),
    'Jos Buttler': (
        "Opener, the most balls of the ten (2,820). No weak phase: overs 1 to 6 +0.16, overs 7 to 16 +0.11, overs 17 to 20 +0.14. +0.24 and +0.18 in 2025 and 2026.",
        "A flexible top order batter who can bat in any phase.",
        "His IPL balls alone give only +0.03, against +0.31 in T20Is. He drops out of the top 10 in 5 of the 7 changes of section 4, and he is in it in 29% of the redraws."),
}

bowler_texts = {
    'Jasprit Bumrah': (
        "Right-arm fast. Overs 17 to 20: +0.41 (495 balls). Overs 7 to 16: +0.27. Overs 1 to 6: +0.18. Against left-handers +0.43 (542 balls), right-handers +0.20. Economy 7.18, a wicket every 20 balls.",
        "The best fit for the two weaker spots of the Royals' bowling: overs 17 to 20 and left-handers.",
        "-0.01 in 2026 (474 balls). Above the average player in 11 of his 25 pressure matches."),
    'Josh Hazlewood': (
        "Right-arm fast-medium. Overs 1 to 6: +0.36 (808 balls). Overs 7 to 16: +0.13. Overs 17 to 20: +0.05 (371). Against left-handers +0.30. A wicket every 15 balls.",
        "A new ball wicket taker and an option against left-handers. The Royals' powerplay bowling is already above the other teams, so he adds to a strength.",
        "Weak at the death (+0.05), economy 8.28, and +0.01 in 2026."),
    'Sunil Narine': (
        "Off-spin, all 1,553 balls in the IPL. Economy 6.87, the lowest of the ten. Overs 7 to 16: +0.21 (1,243 balls). Left-handers +0.18, right-handers +0.19.",
        "Control in the middle overs against both hands.",
        "The fewest wickets of the ten (one per 24 balls), so he drops out when a wicket costs twice as much. Overs 1 to 6: -0.07 (210 balls)."),
    'Bhuvneshwar Kumar': (
        "Right-arm medium. Overs 1 to 6: +0.24 (1,373 balls). Overs 17 to 20: +0.13 (635). Overs 7 to 16: -0.14 (306). Right-handers +0.20, left-handers +0.09.",
        "A new ball and death bowler, with more balls in those phases than anyone else on the list. He never drops out in the 7 changes of section 4.",
        "-0.07 in 2024 and -0.05 in 2025, then +0.33 in 2026. Above the average player in 13 of his 31 pressure matches, the lowest share of the ten bowlers."),
    'Nathan Ellis': (
        "Right-arm medium. Overs 1 to 6: +0.51 (272 balls). Overs 7 to 16: +0.22 (367). Overs 17 to 20: +0.06 (320). Against left-handers +0.32 (341 balls).",
        "A new ball and left-hander option.",
        "A thin IPL record: 34% of his balls and exactly the minimum of 5 IPL pressure matches. Only 66 balls in 2026. He is out of the list on IPL balls alone."),
    'Varun Chakravarthy': (
        "Leg-spin. Overs 7 to 16: +0.17 (1,655 balls). Overs 1 to 6: +0.23 (361). Overs 17 to 20: -0.11 (166). Right-handers +0.21, left-handers +0.06. A wicket every 15.8 balls.",
        "A middle overs wicket taker.",
        "Weak against left-handers, the weaker side of the Royals' bowling too. -0.06 in 2026 (422 balls)."),
    'Matheesha Pathirana': (
        "Right-arm fast. Overs 17 to 20: +0.32 (488 balls). Overs 7 to 16: +0.12 (710). A wicket every 13.8 balls, the best of the ten, at an economy of 8.69. Above the average player in 14 of his 17 pressure matches.",
        "A death bowler who takes wickets, for the phase where the Royals' bowling is furthest below the other teams.",
        "-0.09 in 2025 and only 109 balls in 2026. Only 81 balls in the powerplay."),
    'Rashid Khan': (
        "Leg-spin, the most balls of any bowler (2,780). Overs 7 to 16: +0.14 (2,174 balls). Left-handers +0.28 (955 balls), right-handers +0.03. Economy 7.41.",
        "Middle overs control, and an answer to left-handers.",
        "His IPL balls alone give +0.06, against +0.22 in T20Is. About zero against right-handers. He drops out in 5 of the 7 changes of section 4 and is in the top 10 in 29% of the redraws."),
    'Kuldeep Yadav': (
        "Left-arm wrist spin. Overs 7 to 16: +0.12 (1,775 balls). Overs 17 to 20: +0.20 (172). The same +0.12 against right and left-handers. A wicket every 16 balls.",
        "A left-arm wrist spinner for the middle overs, a type of bowler the rest of the list does not have.",
        "-0.27 in 2026 (344 balls). His IPL balls alone give +0.08, against +0.24 in T20Is. He drops out in 5 of the 7 changes of section 4 and is in the top 10 in 29% of the redraws."),
    'Trent Boult': (
        "Left-arm fast-medium, 88% of his balls in the IPL. Overs 1 to 6: +0.21 (993 balls). Overs 7 to 16: -0.01. Overs 17 to 20: -0.03 (271). +0.46 in 2023.",
        "A left-arm new ball bowler. The Royals' powerplay bowling is already above the other teams.",
        "-0.65 in 2026, on 107 balls. Nothing after the powerplay. He drops out in 5 of the 7 changes of section 4, and Mohsin Khan (11th) is level with him."),
}

# Checks : every player of both lists has a text, and the numbers of the tables below are the ones I read from the notebooks
assert set(batter_texts) == set(batters.head(10)['name']), "a batter has no text"
assert set(bowler_texts) == set(bowlers.head(10)['name']), "a bowler has no text"

# The gaps I quote in the text, read from the profile
powerplay_gap, powerplay_band = rr('batting', 'overs 1-6')
checks = [round(powerplay_gap, 2) == 0.25, round(powerplay_band, 2) == 0.24,
          round(rr('batting', 'overs 7-16')[0], 2) == -0.07, round(rr('batting', 'overs 17-20')[0], 2) == -0.10,
          round(rr('batting', 'against Spin')[0], 2) == -0.09, round(rr('bowling', 'overs 1-6')[0], 2) == 0.10,
          round(rr('bowling', 'overs 17-20')[0], 2) == -0.05, round(rr('bowling', 'to LHB')[0], 2) == -0.05,
          round(rr('bowling', 'overs 7-16')[0], 2) == -0.02, round(rr('batting', 'high pressure')[0], 2) == 0.15,
          round(rr('bowling', 'high pressure')[0], 2) == 0.12, round(rr('bowling', 'all balls')[0], 2) == 0.01]
assert all(checks), f"a Royals number in the text does not match 06_rr_profile.csv: {checks}"

blend_rows = ""
for weight, label in [(0.0, "0.0 (high pressure balls only)"), (0.5, "0.5"), (0.7, "0.7"), (1.0, "1.0 (level only)")]:
    blend_rows += (f"<tr><td class='left'>{label}</td><td>{blend.loc[weight, 'batters average']:+.2f}</td>"
                   f"<td>{blend.loc[weight, 'bowlers average']:+.2f}</td></tr>")

style = """
@page { size: A4; margin: 13mm 14mm 15mm 14mm; @bottom-right { content: counter(page); font: 8pt 'Segoe UI', sans-serif; color: #777; } }
* { box-sizing: border-box; }
body { font: 9.6pt/1.42 'Segoe UI', Calibri, Arial, sans-serif; color: #222; margin: 0; }
h1 { font-size: 21pt; line-height: 1.15; margin: 0 0 3px 0; color: #1d2b53; }
h2 { font-size: 13.5pt; margin: 16px 0 5px 0; color: #d6246e; border-bottom: 1.5px solid #d6246e; padding-bottom: 2px; break-after: avoid; }
h3 { font-size: 10.5pt; margin: 10px 0 3px 0; color: #254aa5; break-after: avoid; }
p { margin: 4px 0 6px 0; }
ul { margin: 3px 0 6px 0; padding-left: 18px; }
li { margin-bottom: 2.5px; }
.sub { color: #555; font-size: 10.5pt; margin-bottom: 8px; }
.three { display: flex; gap: 8px; margin: 6px 0 4px 0; }
.three div { flex: 1; background: #f5f6fa; border-left: 3px solid #254aa5; padding: 5px 8px; font-size: 9pt; }
.three b { color: #1d2b53; }
.box { background: #fdf1f6; border-left: 3px solid #d6246e; padding: 5px 9px; margin: 6px 0; }
figure { margin: 6px auto; text-align: center; break-inside: avoid; }
figure img { width: 100%; }
figcaption { font-size: 8.3pt; color: #555; margin-top: 1px; }
.row { display: flex; gap: 12px; align-items: flex-start; }
.row > * { flex: 1; }
table { border-collapse: collapse; width: 100%; font-size: 8.6pt; margin: 5px 0 8px 0; }
th { background: #1d2b53; color: white; padding: 3px 5px; text-align: right; font-weight: 600; }
td { padding: 2.5px 5px; border-bottom: 1px solid #e1e3ea; text-align: right; }
.left { text-align: left !important; }
table.fit th, table.fit td { text-align: left; vertical-align: top; font-size: 8.1pt; line-height: 1.32; padding: 3px 5px; }
table.fit td.name { white-space: nowrap; }
table.fit tr { break-inside: avoid; }
.two { display: flex; gap: 14px; }
.two > div { flex: 1; }
.small { font-size: 8.4pt; color: #555; }
code { font: 8.4pt Consolas, monospace; background: #f0f1f5; padding: 0 3px; }
"""

parts = []
parts.append(f"<html><head><meta charset='utf-8'><title>Who holds up when the match is on the line?</title><style>{style}</style></head><body>")

# ---------- Page 1 : summary
parts.append("<h1>Who holds up when the match is on the line?</h1>")
parts.append("<div class='sub'>Ten batters and ten bowlers for the Rajasthan Royals at the IPL 2027 auction. SupeRR Selector Season 2, Round 1.</div>")
parts.append("""<p>I ranked players on how much better than an average player they are, ball by ball, in the same match situation. The data is 200,961 balls from 867 matches
since 2022: 367 IPL, 470 T20I and 30 other T20 matches that only helped to train the models. I rank a player on all his balls and not only the tense ones. The tense balls alone
told me nothing about batters in the other half of the matches, and no more than the overall level for bowlers (section 4). I could not find a separate clutch skill in this data.</p>""")
parts.append("""<div class='three'>
<div><b>Pressure.</b> For every ball, how far the chance of winning is expected to move on the next ball. A ball is high pressure if it is in the top fifth of all balls (score 80 or more).</div>
<div><b>Performance.</b> What happened on the ball minus what an average player would have done in the same situation: over, wickets, innings, balls already faced, pace or spin, competition, opponent and ground. Wickets count as runs.</div>
<div><b>Ranking.</b> Value per ball over all balls, small samples pulled towards the average, only players with a real IPL record, and T20I balls adjusted to IPL terms.</div>
</div>""")
parts.append(picture("charts/01_final_lists.png", "The two final lists. Bar = runs per ball above an average player, in IPL terms. Percentage = share of 1,000 redraws of the matches in which the player is in the top 10."))
parts.append("""<div class='two'><div>
<h3>What the tests say</h3>
<ul>
<li>A player's overall level comes back in the other half of the matches (correlation 0.32 for batters, 0.20 for bowlers). A clutch number does not (-0.23 and +0.07), and shuffled labels give anything from -0.25 to +0.24.</li>
<li>The top 5 batters are in the top 10 in 90% or more of 1,000 redraws of the matches, and the top 3 bowlers in 78% or more. Places 7 to 10 of the batters and 6 to 10 of the bowlers are close calls.</li>
<li>Abhishek Sharma, Tim David, Klaasen and Patidar (batters) and Bumrah and Bhuvneshwar Kumar (bowlers) stay in the top 10 under every one of seven changes to my own choices (the price of a wicket, the seasons used, no shrinking). Places 9 and 10 of both lists drop out in most of them.</li>
<li>Looking forward is hard: a level built on 2022 to 2025 predicts 2026 only weakly (0.04 for batters, 0.23 for bowlers). Section 4 says what that means.</li>
</ul></div><div>
<h3>For the Rajasthan Royals</h3>
<ul>
<li>In IPL 2025 and 2026 the Royals batted far better than the other teams in the powerplay (+0.25 per ball, just outside what luck alone gives) and below them in overs 7 to 20 and against spin. Those are hints, not results.</li>
<li>Their bowling was level with the other teams overall, above them in the powerplay and a little below in overs 17 to 20 and against left-handers, also hints.</li>
<li>Section 6 says player by player where each of the 20 would fit, and what to watch.</li>
</ul></div></div>""")

# ---------- Section 1
parts.append("<h2>1. How I define pressure</h2>")
parts.append("""<p>Two balls with the same score can carry very different pressure. Needing 12 off 6 balls with 8 wickets down is tense on every ball. Needing 12 off 60 balls decides nothing yet,
so the score alone cannot tell the two apart. I measured pressure from the chance of winning, in three steps.</p>""")
parts.append("<div class='row'><div>")
parts.append("""<p>First, win probability. One LightGBM model for each innings gives the chance that the batting team wins, from the score or the runs needed, wickets in hand, balls left and the competition.
I forced it to follow cricket logic: more wickets, more balls or more runs never lower the chance. I trained it on 812 clean matches in 5 groups, and every match is scored by a model that never saw it.
The Brier score is 0.178 (0.250 for always saying the base rate). When the model says 70%, the team wins about 70% of the time, and the biggest gap in any of 10 buckets is 2.6 points.</p>
<p>Second, leverage. For each of the 8 results of the next ball (0 to 6 runs, or a wicket) I take the change in win probability and weight it by how often that result happens in that over of that innings.
My first version used win chance after a four minus win chance after a wicket. It said a wicket on the first ball is worth 10.9 points, which is a guess, because almost no match
reaches those states. I replaced it.</p>
<p>Third, the pressure score: leverage as a percentile over all balls, 0 to 100. High pressure means 80 or more, which is 19.8% of balls.</p>""")
parts.append("</div><div>")
parts.append(picture("../outputs/02_calibration.png", "Win probability model: predicted against actual win rate, in 10 buckets of balls the model had not seen.", "78%"))
parts.append("""<table class='numbers'><tr><th class='left'>Spot check</th><th>Average pressure</th></tr>
<tr><td class='left'>Last over of a close chase (1 to 12 needed)</td><td>92.1</td></tr>
<tr><td class='left'>First over of the first innings</td><td>36.3</td></tr>
<tr><td class='left'>One sided chase (win chance above 95% or below 5%)</td><td>13.1</td></tr></table>""")
parts.append("</div></div>")
parts.append("""<p>The scoreboard also misses some things, so I tested four: 3 or more dot balls in a row, 2 or more wickets in the last 18 balls, a batter in his first 10 balls and a knockout match.
With the match state held fixed, the first three lower the runs per ball by 0.10 to 0.23 (t between 7 and 23). The knockout match changes nothing. I keep the three as flags in the data,
but I do not add them to the pressure score. I cannot tell whether the cause is pressure or just a bowler on a roll or a hard pitch. As a backup I also built a plain rule based index
(required rate against what the batters can manage, and how late it is). It agrees with the score only loosely, and I use it in section 4 to see whether the lists depend on my definition.</p>""")

# ---------- Section 2
parts.append("<h2>2. How I measure performance</h2>")
parts.append("""<p>A raw strike rate or economy is unfair, because an opener and a death bowler face different situations. So every ball gets a value: what happened minus what an average player would have done in the same situation.</p>
<ul>
<li>Four LightGBM models (runs and wicket chance, one pair for the batter side and one for the bowler side) use only the over, wickets down, innings, pace or spin, competition, how many balls the striker has already faced, the strength of the opponent and the ground.
They never see a player name. Opponent and ground strength are measured on other matches only, never the match being scored. My first version also counted the match being scored, which leaked the result into the feature. My own audit caught it and I fixed it.</li>
<li>The ground and the balls faced were added after a review. Without the ground, the average batter value at the 13 big IPL grounds ran from -0.18 to +0.12 per ball, as big as the spread between players; now it runs from -0.10 to +0.04. Without balls faced, a batter's first 10 balls averaged -0.08 and his later balls +0.08 to +0.11, so openers who bat long were flattered over finishers; now every group is within 0.01 of zero.</li>
<li>Wickets are counted as runs. A wicket costs the batting team a different number of runs depending on when it falls: 18.2 runs on ball 1 of an IPL innings, 7.6 on ball 60, 1.9 on ball 110. I measured a smooth curve from the data for each competition, so the value of a ball is in runs whether it was a boundary or a wicket.</li>
<li>The value of a ball for a batter is runs above expected, minus the cost of a wicket if he got out more than expected. For a bowler it is runs saved, plus the cost of a wicket if he took one. Batters are measured on legal balls and bowlers on every delivery.</li>
<li>Checks: the average value over all players is within about 0.01 runs per ball of zero in every phase, in both innings, for IPL and for T20I, and for pace and for spin. The models score about the same on training and held out matches (the gap in error is under 0.04). Match by match, when the model expects 0.1 more runs per ball, there are 0.094 more. And an average player stays within 0.03 of zero in every one of 10 pressure groups (chart below), so a player's number is not shifted by pressure itself.</li>
</ul>""")
parts.append(picture("charts/03_pressure_effect.png", "Average value per ball of all players, by pressure score of the ball. The bars show 2 standard errors. Pressure does not change an average player.", "80%"))

# ---------- Section 3
parts.append("<h2>3. How I compare players fairly</h2>")
parts.append("""<ul>
<li>A player's level is his average value per ball. A raw average is skill plus luck, so I pull every player towards the average of the pool by as much as luck could explain. The amount is estimated from the data: the true spread between players is about 0.09 runs per ball for batters and 0.08 for bowlers, while one ball has a spread above 2 runs.
So 100 balls get pulled hard and 2,000 balls barely move. One lucky over cannot put anyone at rank 1. Balls from the same match are not independent (same pitch, same opponent), and I allow for that by raising the luck by up to about 10%.</li>
<li>To be eligible a batter needs at least 100 high pressure balls (a bowler 120, because bowlers bowl more balls per match) and at least 10 pressure matches, meaning matches with 6 or more high pressure balls. That is about one full season of tight finishes. It leaves 67 batters and 85 bowlers.</li>
<li>The report is for an IPL auction, so a player also needs a real IPL sample: half the ball minimum and 5 pressure matches in the IPL itself. His T20I balls still count as evidence. 57 batters and 62 bowlers stay. The rule is on the data, not on nationality, but it removes everyone with no IPL record since 2022, which includes the Pakistan players on the dropdown.</li>
<li>T20I balls are easier: the same player is 0.08 runs per ball better in T20Is than in the IPL as a batter (40 players with 300 or more balls in both) and 0.04 as a bowler (36 players). The final lists take that average gap off every T20I ball. It keeps the same 10 batters, and swaps two bowlers: Kuldeep Yadav and Trent Boult in, Mustafizur Rahman and Mitchell Santner out.</li>
</ul>""")
parts.append(picture("charts/06_ipl_vs_t20i.png", "The same player in the IPL and in T20Is. Most points are above the line, and the two agree only loosely (correlation 0.30 and 0.52), as they should when each is measured on half the balls.", "82%"))

# ---------- Section 4
parts.append("<h2>4. Evidence for the top 10s</h2>")
parts.append("<h3>Is there a clutch skill?</h3>")
parts.append("""<p>Clutch = a player's value on high pressure balls minus his value on his other balls. I tested whether the method can find it, and whether it is there.</p>
<ul>
<li>First I took clutch away on purpose. Inside every player I shuffled which of his balls count as high pressure, 30 times. Nobody can have a clutch skill then, and the method still finds a spread of about 0.05 runs per ball (90% of the shuffles are below 0.10). The real spread is 0.000 for batters and 0.048 for bowlers. Half of the shuffles beat the real bowler number.</li>
<li>Then I put clutch in on purpose: I added a made up clutch skill (spread 0.10) to the high pressure balls. The method finds 0.099 for bowlers and 0.068 for batters.</li>
<li>Third, I split the matches into two random halves 100 times and measured every player in both.</li>
</ul>""")
parts.append(picture("charts/04_split_half.png", "Correlation between the two halves over the ranked players. A number that is a skill must come back; level does, clutch does not.", "80%"))
parts.append("""<p>So with this data I cannot say a separate clutch skill exists, for batters or for bowlers. I cannot say it does not exist either: the data only sees a clutch spread of about 0.10 runs per ball or more, which is as big as the whole spread in level. What I can say is that the best guess of how a player does on a high pressure ball is his overall level.
That is why the lists are ranked on level. A player who looks great on his high pressure balls alone is mostly lucky: for batters, that number in one half does not predict it in the other (-0.11).</p>
<h3>Level, high pressure balls, or a mix?</h3>""")
parts.append("<div class='row'><div>")
parts.append("""<p>I built a score in one half of the matches, as <i>w</i> times level plus (1 - <i>w</i>) times the value on high pressure balls, and checked how well it predicts the high pressure value in the other half (200 tries).
For batters every bit of weight on the high pressure balls makes it worse, and level alone is best in 197 of 200 tries. For bowlers a mix of 0.7 scores 0.24 against 0.22 for level alone, but the spread from split to split is 0.10 and the best weight jumps around,
so I do not move off level.</p>""")
parts.append("</div><div>")
parts.append(f"""<table class='numbers'><tr><th class='left'>Weight on level (<i>w</i>)</th><th>Batters</th><th>Bowlers</th></tr>{blend_rows}</table>
<div class='small'>Correlation with the high pressure value in the other half, average of 200 tries.</div>""")
parts.append("</div></div>")
parts.append("<h3>Do the lists hold?</h3>")
parts.append("""<table class='numbers'><tr><th class='left'>Test</th><th>Batters: of my top 10 stay</th><th>Bowlers: of my top 10 stay</th></tr>
<tr><td class='left'>T20I balls not adjusted (the step 4 order)</td><td>10</td><td>8 (Mustafizur and Santner in, Kuldeep and Boult out)</td></tr>
<tr><td class='left'>IPL balls only</td><td>7 (Iyer, Head and Gill in; Salt, Marsh and Buttler out)</td><td>7 (Prasidh, Mohsin and Rabada in; Ellis, Rashid and Kuldeep out)</td></tr>
<tr><td class='left'>High pressure balls picked with the rule based index</td><td>8 (Abhishek and Patidar have fewer than 10 pressure matches under it)</td><td>10</td></tr>
<tr><td class='left'>Ball minimum 60 to 150 (batters) or 72 to 180 (bowlers), 10 pressure matches</td><td>9 or 10</td><td>9 or 10</td></tr>
<tr><td class='left'>5 pressure matches instead of 10</td><td>8 (Sooryavanshi and Russell in)</td><td>10</td></tr>
<tr><td class='left'>15 pressure matches instead of 10</td><td>7 (Klaasen, Patidar and Salt not ranked)</td><td>9 (Ellis out)</td></tr>
<tr><td class='left'>Price of a wicket times 0 (runs only) / 0.5 / 1.5 / 2</td><td>7 / 8 / 9 / 7</td><td>6 / 8 / 9 / 7</td></tr>
<tr><td class='left'>Only the seasons 2024 to 2026 / only 2025 to 2026</td><td>8 / 6 (Pooran and Buttler out in both)</td><td>7 / 5 (Rashid, Kuldeep and Boult out in both)</td></tr></table>
<p>Over the last seven changes (wicket price, seasons, and no shrinking) the batters who never drop out are Abhishek Sharma, Tim David, Klaasen and Patidar. Buttler and Pooran drop out in 5 of 7, Sudharsan, Marsh and Salt in 2, and Suryakumar Yadav in 1.
Among the bowlers Bumrah and Bhuvneshwar Kumar never drop out, Rashid Khan, Kuldeep Yadav and Boult drop out in 5 of 7, and the others in 1. I treat the players who never drop as the firmest picks, and places 9 and 10 of both lists as good but replaceable.</p>
<h3>Does the past predict the next season?</h3>
<p>An auction buys the next season, and every test above mixes the years. So I built the level from the years up to 2025 only and compared it with each player's level in 2026 (about 40 players per list with 150 or more balls in 2026).
For batters the level from 2022 to 2025 predicts 2026 at 0.04, from 2024 and 2025 at 0.11, and from 2025 alone at 0.24. For bowlers it is 0.23, -0.01 and 0.04. With one season and 40 players these numbers move by about 0.15 on luck alone, so they do not pick a better window.
They do say that one T20 season is very noisy, and that a five year level is a weak forecast for batters. I keep the five year level, because the shorter windows are no better for bowlers, and I show every player's form by year in section 6.</p>""")
parts.append(picture("charts/05_rank_confidence.png", "How often each player is in the top 10 when I draw the same number of matches again 1,000 times with repeats and rank again. The first 5 batters and the first 3 bowlers are firm.", "88%"))
parts.append("""<p>Mohsin Khan (50% of the redraws) and Mustafizur Rahman (32%) are the closest bowlers outside the list, level with or above the 8th to 10th bowler. Among batters Head (37%) and Stoinis (36%) are level with places 9 and 10. I also show for every player the share of his pressure matches in which he beat the average player.
It comes back in the other half for bowlers (0.26) and not for batters (0.02), so I show it but I do not put it into the score.</p>""")
parts.append(list_table(batters, "Batter"))
parts.append(list_table(bowlers, "Bowler"))
parts.append("<div class='small'>Pressure matches = matches with 6 or more high pressure balls. Above average in = the share of those matches in which his total value beat the average player. Value per ball is in IPL terms.</div>")

# ---------- Section 5
parts.append("<h2>5. Reliability and limitations</h2>")
parts.append("""<ul>
<li>The lists are the players who are best against an average player in the same situations, which is the best guess of who is best under pressure. A clutch skill smaller than about 0.10 runs per ball could exist and this data could not show it.</li>
<li>Places 7 to 10 of the batters and 6 to 10 of the bowlers could change with a different set of matches. Travis Head, Marcus Stoinis (batters) and Mohsin Khan, Mustafizur Rahman (bowlers) are the nearest alternatives.</li>
<li>The value depends on what a wicket costs, which is my own estimate. Players who score fast and get out more often gain when wickets are cheap, and players who rarely get out gain when they are dear: Virat Kohli is 22nd among the batters, and he enters the top 10 when a wicket costs one and a half or two times as much, or when I use only the recent seasons.</li>
<li>The value is an average over 2022 to 2026 with every year counted the same, and it is a weak forecast of the next season (section 4). Some players are lower lately: Pooran (-0.28 in 2026), Salt (0.00), Kuldeep Yadav (-0.27), Boult (-0.65 on 107 balls), Chakravarthy (-0.06), Bumrah (-0.01). Section 6 shows every player by year.</li>
<li>The win probability model does not know team strength or the ground, and the first innings is weak (Brier 0.223, against 0.129 in the second innings), which is normal because nobody knows the result at ball 1. A batter who mostly bats first gets fewer high pressure balls, because first innings balls are compared with chase balls (3.6% of first innings balls score above 90, against 17.1% in the second).</li>
<li>The T20I adjustment is one average gap for every player. Nathan Ellis (34% IPL balls) and Phil Salt (44%) lean the most on T20I balls.</li>
<li>Some samples are small: Patidar has 916 balls and Ellis has 5 IPL pressure matches. The batter list depends on the minimum of 10 pressure matches (section 4).</li>
<li>The value model does not know a player's own team strength, so a strong team could give a small head start. No team has more than two players in either list.</li>
<li>The data does not say who is retained or in the auction, what anyone costs, who fills the overseas slots, or anyone's age, fitness, wicketkeeping and fielding. It also ignores what batters do when they bowl. Section 6 uses only what the ball by ball data can say.</li>
</ul>""")

# ---------- Section 6
parts.append("<h2>6. How each player could strengthen the Rajasthan Royals at the IPL 2027 auction</h2>")
parts.append("""<p>The data cannot tell me who the Royals keep, who reaches the auction or what anyone costs. So "fit" here means two things: where a player's own numbers are strong, and where the Royals' own numbers show room.
For the second I compare the Royals in IPL 2025 and 2026 (30 matches) with the other nine teams, using the same value per ball.</p>""")
parts.append(picture("charts/08_rr_profile.png", "Royals value per ball minus the other teams, IPL 2025 and 2026. Right = better. The black line is how far luck alone can move the number (2 standard errors).", "88%"))
parts.append("""<p>Reading the chart: only the Royals' powerplay batting (+0.25, against a luck band of 0.24) is outside what luck alone gives, and only just. Everything else is inside the band, so it points a direction and nothing more. Batting: below the other teams in overs 7 to 16 (-0.07),
overs 17 to 20 (-0.10) and against spin (-0.09). Bowling: level with the other teams overall (+0.01), above them in the powerplay (+0.10), and below in overs 7 to 16 (-0.02), overs 17 to 20 (-0.05) and to left-handers (-0.05). On high pressure balls the Royals batted +0.15 above the other teams and bowled +0.12 above them, again inside the band.
If those gaps are real, the best matches are middle and late overs batters who attack spin, and bowlers for overs 17 to 20 and for left-handers. If they are luck, the 20 players are still the ones with the best record against an average player.</p>
<p>In every row the numbers are plain averages with the balls behind them, not shrunk, so a split with fewer than about 300 balls is a hint. The by year chart after the tables shows the form of each player.</p>""")
parts.append("<h3>Batters</h3>")
parts.append(fit_table(batters, batter_texts))
parts.append("<h3>Bowlers</h3>")
parts.append(fit_table(bowlers, bowler_texts))
parts.append("""<p>Putting it together: for the batting gaps, Tim David, Suryakumar Yadav, Klaasen and Patidar are the ones whose numbers are strongest in overs 7 to 20 and against spin, and three of them never drop out of the list. Abhishek Sharma, Salt, Sudharsan, Marsh and Buttler are openers, which is the Royals' strength already, so they are choices for quality and depth. Pooran's middle overs number is ordinary.
For the bowling gaps, Bumrah and Pathirana are the strongest in overs 17 to 20, and Bumrah, Ellis, Hazlewood and Rashid Khan are the strongest against left-handers. Narine, Chakravarthy, Rashid Khan and Kuldeep Yadav are the middle overs bowlers, and Narine (6.87) and Bumrah (7.18) have the best economies.
The biggest cautions are the 2026 seasons of Pooran, Kuldeep Yadav and Boult, and the thin IPL sample of Ellis.</p>""")
parts.append(picture("charts/07_value_by_year.png", "Value per ball by year. A year with fewer than 100 balls is blank. 2026 is the IPL season only. The last two years matter most for the IPL 2027 auction.", "96%"))

# ---------- Reproduce
parts.append("<h2>Reproducing this</h2>")
parts.append("""<p>The code, the notebooks and one note per step with every decision are in the repository folder. Put the six competition csv files in the project folder, then run in order:
<code>python src/01_clean.py</code>, <code>python src/02_pressure.py</code>, <code>python src/03_expected.py</code>, the notebooks <code>notebooks/04_player_curves.ipynb</code> and <code>notebooks/05_proof.ipynb</code>, then
<code>python src/06_facts.py</code>, <code>python src/06_charts.py</code> and <code>python src/06_report.py</code>. Every step is seeded, and I checked that a rerun gives the same tables.
The decisions and their reasons are in <code>report/notes/</code>. Tools: pandas, LightGBM, matplotlib.</p>""")
parts.append("</body></html>")

with open(html_path, "w", encoding="utf-8") as file:
    file.write("\n".join(parts))
print("html written:", html_path)

# Printing the PDF from the HTML with Edge or Chrome (whichever is installed)
browsers = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"]
browser = next(path for path in browsers if os.path.exists(path))
subprocess.run([browser, "--headless", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={pdf_path}", "file:///" + html_path.replace("\\", "/")],
               check=True, capture_output=True, timeout=180)
print("pdf written:", pdf_path, round(os.path.getsize(pdf_path) / 1024), "KB")
