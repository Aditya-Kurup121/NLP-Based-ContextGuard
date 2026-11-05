"""Levenshtein edit distance algorithm and alignment matrix."""
from typing import List, Dict, Any, Tuple


def compute_levenshtein(s1: str, s2: str) -> Dict[str, Any]:
    """
    Computes Levenshtein edit distance between s1 and s2 using dynamic programming.
    Returns the distance, the dynamic programming matrix, and the sequence of edit operations.
    """
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                cost = 0
            else:
                cost = 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,       # deletion
                dp[i][j - 1] + 1,       # insertion
                dp[i - 1][j - 1] + cost # substitution
            )

    distance = dp[m][n]
    max_len = max(m, n)
    similarity = round(1.0 - (distance / max_len), 4) if max_len > 0 else 1.0

    # Backtrace optimal alignment
    i, j = m, n
    operations = []
    while i > 0 or j > 0:
        if i > 0 and j > 0 and s1[i - 1] == s2[j - 1]:
            operations.append({"op": "match", "char1": s1[i - 1], "char2": s2[j - 1], "cost": 0})
            i -= 1
            j -= 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + 1:
            operations.append({"op": "substitute", "char1": s1[i - 1], "char2": s2[j - 1], "cost": 1})
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            operations.append({"op": "delete", "char1": s1[i - 1], "char2": "-", "cost": 1})
            i -= 1
        else:
            operations.append({"op": "insert", "char1": "-", "char2": s2[j - 1], "cost": 1})
            j -= 1

    operations.reverse()

    return {
        "str1": s1,
        "str2": s2,
        "distance": distance,
        "similarity_ratio": similarity,
        "matrix": dp,
        "operations": operations,
        "header_x": ["ε"] + list(s2),
        "header_y": ["ε"] + list(s1),
    }

