import numpy as np

def align_by_levenshtein(gt, pred):
    m, n = len(gt), len(pred)
    dp = np.zeros((m + 1, n + 1), dtype=int)
    for i in range(m + 1): dp[i][0] = i
    for j in range(n + 1): dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if gt[i-1] == pred[j-1] else 1
            dp[i][j] = min(dp[i-1][j-1] + cost, dp[i-1][j] + 1, dp[i][j-1] + 1)
    aligned_gt, aligned_pred = [], []
    i, j = m, n
    while i > 0 or j > 0:
        if i > 0 and j > 0 and dp[i][j] == dp[i-1][j-1] + (0 if gt[i-1] == pred[j-1] else 1):
            aligned_gt.insert(0, gt[i-1])
            aligned_pred.insert(0, pred[j-1])
            i -= 1; j -= 1
        elif i > 0 and dp[i][j] == dp[i-1][j] + 1:
            aligned_gt.insert(0, gt[i-1])
            aligned_pred.insert(0, ' ')
            i -= 1
        else:
            aligned_gt.insert(0, ' ')
            aligned_pred.insert(0, pred[j-1])
            j -= 1
    return aligned_gt, aligned_pred
