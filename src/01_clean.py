"""
Step 1: clean the ball-by-ball data and build the match state before every ball.

Run from the project folder:   python src/01_clean.py
Reads:   ball_by_ball.csv, matches.csv, competitions.csv
Writes:  outputs/balls_clean.parquet   one row per delivery, with the state before it
         outputs/01_checks.txt         the checks that tell us the table can be trusted

Three things in the raw data need care:
1. Super overs (innings 3 and 4) are in the file. We drop them.
2. The file does not say how many runs came from byes, leg-byes or extra runs on a wide.
   We infer them from whether the batters swapped ends (see infer_extras).
3. Some matches were shortened by rain, so an innings is not always 120 balls.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

# Dismissals that the bowler gets credit for. A run-out or "retired out" is a
# team wicket, but it is not the bowler's skill.
BOWLER_WICKETS = {"Caught", "Bowled", "LBW", "Stump", "Hit Wicket"}
# "Overstep" is a front-foot no-ball. "other" behaves exactly like a no-ball in the
# data (never a legal ball, batter can score off it), so we treat it as one.
NOBALL_TYPES = {"Overstep", "other"}

KEY = ["match_id", "innings"]


def load_balls() -> pd.DataFrame:
    b = pd.read_csv(ROOT / "ball_by_ball.csv", low_memory=False)
    b = b[b["innings"] <= 2].copy()                      # drop super overs
    b = b.sort_values(KEY + ["innings_ball_num"]).reset_index(drop=True)
    b = b.rename(columns={"overid": "over", "runs": "bat_runs"})
    et = b["extras_type"].fillna("none")
    b["is_wide"] = et.eq("wide")
    b["is_noball"] = et.isin(NOBALL_TYPES)
    b["is_bye"] = et.eq("byes")
    b["is_legbye"] = et.eq("legbyes")
    # A wide or a no-ball has to be bowled again, so it is not a legal ball.
    # The single "Penalty" row is not a delivery at all.
    b["legal"] = ~(b["is_wide"] | b["is_noball"] | et.eq("Penalty"))
    return b


def infer_extras(b: pd.DataFrame) -> pd.DataFrame:
    """Work out the runs from extras, which the raw file does not record.

    Idea: when batters run an odd number of runs they swap ends, so the other
    batter faces the next ball. We can see who faced the next ball, so we know
    if the number of runs was odd or even. (At the end of an over the bowling
    end changes, so the logic flips.) On normal balls this rule is right 99.9%
    of the time, which is our proof that it works.

    Odd  -> we assume 1 run  (3 is very rare)
    Even -> on a bye or leg-bye it cannot be 0, so we assume 4 (a boundary).
            On a wide it means no extra run beyond the 1-run penalty.
    """
    g = b.groupby(KEY, sort=False)
    next_striker = g["striker_id"].shift(-1)
    same_over = g["over"].shift(-1).eq(b["over"])
    swapped = next_striker.eq(b["non_striker_id"])
    stayed = next_striker.eq(b["striker_id"])
    crossed = pd.Series(np.where(same_over, swapped, stayed), index=b.index)
    # We cannot tell on the last ball of an innings or when a wicket brings in a
    # new batter. There we fall back to the smallest possible number.
    known = next_striker.notna() & ~b["is_wicket"] & (swapped | stayed)
    b["crossed"] = crossed & known
    b["crossed_known"] = known

    extras = np.zeros(len(b), dtype=int)
    bye_like = b["is_bye"] | b["is_legbye"]
    extras = np.where(bye_like, np.where(known & ~b["crossed"], 4, 1), extras)
    extras = np.where(b["is_wide"], 1 + b["crossed"].astype(int), extras)
    # On a no-ball: 1 penalty run, plus extras_2_runs (byes run on the no-ball).
    extras = np.where(b["is_noball"], 1 + b["extras_2_runs"], extras)
    b["extras_runs"] = extras
    b["total_runs"] = b["bat_runs"] + b["extras_runs"]
    # Runs charged to the bowler: runs off the bat, all wide runs, and the
    # no-ball penalty. Byes and leg-byes are not the bowler's fault.
    b["bowler_runs"] = (
        b["bat_runs"] + np.where(b["is_wide"], b["extras_runs"], 0) + b["is_noball"].astype(int)
    )
    return b


def add_wicket_credit(b: pd.DataFrame) -> pd.DataFrame:
    b["bowler_wicket"] = b["is_wicket"] & b["dismissal_type"].isin(BOWLER_WICKETS)
    # Who got out? Usually the striker. In a run-out it can be the non-striker.
    out_id = b["dismissed_player_id"].where(b["is_wicket"])
    b["striker_out"] = b["is_wicket"] & (out_id.isna() | out_id.eq(b["striker_id"]))
    return b


def add_state(b: pd.DataFrame) -> pd.DataFrame:
    """State BEFORE each ball: score, wickets down, legal balls bowled."""
    g = b.groupby(KEY, sort=False)
    b["score_before"] = g["total_runs"].cumsum() - b["total_runs"]
    b["wickets_before"] = g["is_wicket"].cumsum() - b["is_wicket"].astype(int)
    b["balls_bowled"] = g["legal"].cumsum() - b["legal"].astype(int)
    return b


def load_matches() -> pd.DataFrame:
    m = pd.read_csv(ROOT / "matches.csv")
    c = pd.read_csv(ROOT / "competitions.csv")
    m = m.merge(c, on="comp_id", how="left")
    # Three groups: IPL, T20 internationals, and two smaller "A team" events.
    m["comp_group"] = np.select(
        [m["comp_name"].str.startswith("IPL"), m["match_format"].eq("T20I")],
        ["IPL", "T20I"],
        default="Other T20",
    )
    res = m["result"].fillna("")
    m["margin_runs"] = res.str.extract(r"(\d+)\s*[Rr]uns?")[0].astype(float)
    m["margin_wkts"] = res.str.extract(r"(\d+)\s*(?:[Ww]ickets?|[Ww]kts?)")[0].astype(float)
    m["tied"] = res.str.contains(r"[Tt]ied|[Ss]uper [Oo]ver|Eliminator")
    m["has_winner"] = m["win_team_id"].gt(0) & ~m["tied"]
    # Rain: the revised columns hold the number of balls each innings was cut to.
    m["max_balls_1"] = m["first_inn_revised_overs"].fillna(120)
    m["max_balls_2"] = m["second_inn_revised_overs"].fillna(m["max_balls_1"])
    return m


def add_targets(b: pd.DataFrame, m: pd.DataFrame) -> pd.DataFrame:
    """Give every second-innings ball the target the chasing team needed.

    Our rebuilt totals can be off by a few runs (see infer_extras), so the
    target is tied to the official result:
    - chasing team lost by N runs -> target = their final score + N + 1
    - chasing team won            -> target = first-innings score + 1, kept inside
                                     the range that makes the last ball the winning one
    - rain matches use the official revised target when the first rule cannot apply
    """
    inn = (
        b.groupby(KEY)
        .agg(
            final=("total_runs", "sum"),
            legal=("legal", "sum"),
            wkts=("is_wicket", "sum"),
            last_runs=("total_runs", "last"),
            bat_team=("batting_team_id", "first"),
        )
        .reset_index()
    )
    w = inn.pivot(index="match_id", columns="innings")
    w.columns = [f"{a}_{i}" for a, i in w.columns]
    w = w.reset_index().merge(m, on="match_id", how="left")

    first_target = w["revised_target"].fillna(w["final_1"] + 1)
    inn2_done = w["legal_2"].eq(w["max_balls_2"]) | w["wkts_2"].eq(10)
    chase_won = w["has_winner"] & w["win_team_id"].eq(w["bat_team_2"])
    # A few rain matches were stopped mid-chase and the chasing team won "by runs"
    # because it was ahead of the DLS par score. It never reached a target, so
    # we do not fit one to its last ball.
    par_win = chase_won & w["margin_runs"].notna()
    chase_won = chase_won & ~par_win
    chase_lost = w["has_winner"] & w["win_team_id"].eq(w["bat_team_1"])

    target = first_target.copy()
    rule = pd.Series("first innings + 1", index=w.index)
    use_margin = chase_lost & inn2_done & w["margin_runs"].notna()
    target[use_margin] = w["final_2"] + w["margin_runs"] + 1
    rule[use_margin] = "result margin"
    lo = w["final_2"] - w["last_runs_2"] + 1          # last ball must be needed
    hi = w["final_2"]                                  # and must reach the target
    target[chase_won] = first_target.clip(lower=lo, upper=hi)[chase_won]
    rule[chase_won] = "first innings + 1, fitted to the win"
    tie = w["tied"] & w["final_2"].notna()
    target[tie] = w["final_2"] + 1
    rule[tie] = "tie"
    rule[w["revised_target"].notna() & ~use_margin & ~chase_won] = "official revised target"

    w["target"] = target.where(w["final_2"].notna())
    w["target_rule"] = rule.where(w["final_2"].notna())
    # An innings is complete if it used all its balls, lost 10 wickets, or won the chase.
    w["inn1_complete"] = w["legal_1"].eq(w["max_balls_1"]) | w["wkts_1"].eq(10)
    w["inn2_complete"] = inn2_done | chase_won
    # A match is "clean" when it has a winner and both innings ran their full
    # course. Step 2 trains the win-probability model only on clean matches.
    w["clean_match"] = (w["has_winner"] & w["inn1_complete"] & w["inn2_complete"] & ~par_win).fillna(False)

    keep = [
        "match_id", "comp_id", "comp_name", "comp_group", "season", "match_date", "stage",
        "knock_out", "venue_id", "win_team_id", "has_winner", "tied", "result",
        "max_balls_1", "max_balls_2", "target", "target_rule", "inn1_complete",
        "inn2_complete", "clean_match", "final_1", "final_2", "margin_runs", "margin_wkts",
    ]
    b = b.merge(w[keep], on="match_id", how="left")
    b["max_balls"] = np.where(b["innings"].eq(1), b["max_balls_1"], b["max_balls_2"])
    b["balls_left"] = b["max_balls"] - b["balls_bowled"]
    b["wickets_left"] = 10 - b["wickets_before"]
    b["target"] = b["target"].where(b["innings"].eq(2))
    b["runs_needed"] = b["target"] - b["score_before"]
    # Run rates per over. Guard against dividing by zero on the first ball.
    b["run_rate"] = (b["score_before"] / b["balls_bowled"].where(b["balls_bowled"] > 0) * 6).fillna(0)
    b["required_rate"] = b["runs_needed"] / b["balls_left"].where(b["balls_left"] > 0) * 6
    # 1 if the batting team won the match, 0 if it lost, empty if no winner.
    b["batting_won"] = np.where(
        b["has_winner"], b["win_team_id"].eq(b["batting_team_id"]).astype(float), np.nan
    )
    return b.drop(columns=["max_balls_1", "max_balls_2"]), w


def write_checks(b: pd.DataFrame, w: pd.DataFrame) -> None:
    lines = []
    say = lines.append
    say("STEP 1 CHECKS")
    say(f"balls kept: {len(b):,}   matches: {b['match_id'].nunique()}   innings: {b.groupby(KEY).ngroups}")
    say(f"by competition group (matches): {b.groupby('comp_group')['match_id'].nunique().to_dict()}")
    say(f"matches with a clear winner: {int(w['has_winner'].sum())}   ties: {int(w['tied'].sum())}"
        f"   no winner: {int((~w['has_winner'] & ~w['tied']).sum())}")
    say("")
    say("1. Does the swap-ends rule work? Share of normal balls where the next striker matches the runs scored:")
    n = b[b["crossed_known"] & ~(b["is_wide"] | b["is_noball"] | b["is_bye"] | b["is_legbye"])]
    ok = (n["crossed"] == (n["bat_runs"] % 2 == 1)).mean()
    say(f"   {ok:.4%} of {len(n):,} balls")
    say("")
    say("2. Do rebuilt totals match official results? Matches won by runs, no rain, both innings complete:")
    t = w[w["has_winner"] & w["margin_runs"].notna() & w["revised_target"].isna()
          & w["first_inn_revised_overs"].isna() & w["second_inn_revised_overs"].isna()
          & w["inn1_complete"] & w["inn2_complete"] & w["win_team_id"].eq(w["bat_team_1"])]
    err = (t["final_1"] - t["final_2"]) - t["margin_runs"]
    say(f"   matches: {len(t)}   exact: {(err == 0).mean():.1%}   within 2 runs: {(err.abs() <= 2).mean():.1%}"
        f"   within 4 runs: {(err.abs() <= 4).mean():.1%}   worst: {int(err.abs().max())}")
    raw = b.assign(r=b["bat_runs"] + (b["is_wide"] | b["is_noball"])).groupby(KEY)["r"].sum().unstack()
    raw_err = (raw.loc[t["match_id"], 1].values - raw.loc[t["match_id"], 2].values) - t["margin_runs"].values
    say(f"   without the inferred extras only {np.mean(raw_err == 0):.1%} are exact, so the inference helps")
    say("")
    say("3. Winner agrees with the type of margin:")
    a = w[w["has_winner"] & w["margin_wkts"].notna() & w["margin_runs"].isna()]
    say(f"   'won by wickets' and the winner batted second: {(a['win_team_id'] == a['bat_team_2']).mean():.1%} of {len(a)}")
    a = w[w["clean_match"] & w["margin_runs"].notna() & w["margin_wkts"].isna()]
    say(f"   'won by runs' and the winner batted first:      {(a['win_team_id'] == a['bat_team_1']).mean():.1%} of {len(a)}")
    a = w[w["has_winner"] & w["margin_wkts"].notna() & w["margin_runs"].isna() & w["revised_target"].isna()]
    say(f"   wickets in hand at the end equals the stated margin: {((10 - a['wkts_2']) == a['margin_wkts']).mean():.1%}")
    say("")
    say("4. Innings limits:")
    g = b.groupby(KEY).agg(legal=("legal", "sum"), wk=("is_wicket", "sum"), mx=("max_balls", "first"))
    say(f"   innings with more legal balls than allowed: {int((g['legal'] > g['mx']).sum())}"
        f"   more than 10 wickets: {int((g['wk'] > 10).sum())}")
    say(f"   first innings that stop early in the data (rain or missing balls): {int((~w['inn1_complete']).sum())}")
    say(f"   matches with no second innings in the data: {int(w['final_2'].isna().sum())}")
    say("")
    say("5. Chases: runs needed must be above 0 before every ball and reach 0 or less on a winning last ball.")
    c = b[b["innings"].eq(2) & b["clean_match"]]
    say(f"   balls where runs needed was already 0 or less: {int((c['runs_needed'] <= 0).sum())}")
    say(f"   matches with a winner where the chase stops early (rain or missing balls): "
        f"{int((w['has_winner'] & ~w['inn2_complete'] & w['final_2'].notna()).sum())}")
    say(f"   clean matches (winner, both innings complete): {int(w['clean_match'].sum())}")
    say(f"   how each target was set: {w['target_rule'].value_counts().to_dict()}")
    say("")
    say("6. Missing values in the columns later steps use:")
    for col in ["score_before", "wickets_before", "balls_left", "pace_or_spin", "striker_id", "bowler_id"]:
        say(f"   {col}: {int(b[col].isna().sum())}")
    (OUT / "01_checks.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


def main() -> None:
    b = load_balls()
    b = infer_extras(b)
    b = add_wicket_credit(b)
    b = add_state(b)
    m = load_matches()
    b, w = add_targets(b, m)
    b.to_parquet(OUT / "balls_clean.parquet", index=False)
    write_checks(b, w)
    print(f"\nSaved {len(b):,} rows and {b.shape[1]} columns to outputs/balls_clean.parquet")


if __name__ == "__main__":
    main()
