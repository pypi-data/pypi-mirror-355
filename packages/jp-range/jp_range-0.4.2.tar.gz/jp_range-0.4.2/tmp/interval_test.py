import pandas as pd
import numpy as np

df = pd.DataFrame(
    {
        "id": ["A", "B", "C", "D", "E"],
        "range": [
            pd.Interval(0, 5, closed="both"),   # [0, 5]
            pd.Interval(3, 8, closed="both"),   # [3, 8]
            pd.Interval(8, 10, closed="right"), # (8, 10]
            pd.Interval(15, 20, closed="both"), # [15, 20]
            pd.Interval(float("-inf"), 2, closed="left"), # (-∞, 2]
        ],
        "sample_value": [1, 4, 9, 18, -3],
    }
)

# ------------------------------------------------------
# ② あるスカラー値 x が区間に「含まれる」行を抽出 (∈)
# ------------------------------------------------------
x = 4
rows_containing_x = df[df["range"].apply(lambda iv: x in iv)]
print("x を含む行:\n", rows_containing_x, "\n")

# ------------------------------------------------------
# ③ スカラー値 x が区間に「含まれない」行を抽出 (¬∈)
# ------------------------------------------------------
rows_not_containing_x = df[~df["range"].apply(lambda iv: x in iv)]
print("x を含まない行:\n", rows_not_containing_x, "\n")

# ------------------------------------------------------------
# ④ 指定 Interval と「重なる（overlaps）」行を抽出 (∩ ≠ ∅)
# ------------------------------------------------------------
query_iv = pd.Interval(2, 6, closed="both")   # [2, 6]
rows_overlapping = df[df["range"].apply(lambda iv: iv.overlaps(query_iv))]
print("query_iv と重なる行:\n", rows_overlapping, "\n")

# ------------------------------------------------------------
# ⑤ 指定 Interval と「重ならない」行を抽出 (∩ ＝ ∅)
# ------------------------------------------------------------
rows_non_overlapping = df[~df["range"].apply(lambda iv: iv.overlaps(query_iv))]
print("query_iv と重ならない行:\n", rows_non_overlapping, "\n")
