export function truncateAfterNewline(str: string | string[]): string {
  if (Array.isArray(str)) {
    str = str[0];
  }
  const newlineIndex = str.indexOf('\n');
  if (newlineIndex !== -1) {
    return str.substring(0, newlineIndex);
  } else {
    return str;
  }
}
