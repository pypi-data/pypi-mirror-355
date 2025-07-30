export function calculateLevenshteinDistance(
  str1: string | string[],
  str2: string
): number {
  if (Array.isArray(str1)) {
    str1 = str1.join('\n');
  }

  const m = str1.length;
  const n = str2.length;

  if (Math.abs(m - n) > 2) {
    return Infinity; // Distance exceeds threshold, exit early
  }
  const dp: number[][] = [];

  for (let i = 0; i <= m; i++) {
    dp[i] = [i];
  }

  for (let j = 1; j <= n; j++) {
    dp[0][j] = j;
  }

  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (str1[i - 1] === str2[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1];
      } else {
        dp[i][j] = Math.min(
          dp[i - 1][j] + 1,
          dp[i][j - 1] + 1,
          dp[i - 1][j - 1] + 1 // substitution
        );
      }
    }
  }

  return dp[m][n];
}
