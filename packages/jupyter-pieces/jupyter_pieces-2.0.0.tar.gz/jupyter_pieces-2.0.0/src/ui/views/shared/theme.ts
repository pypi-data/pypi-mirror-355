function cssColorToArgb(color: string) {
  if (color === 'white') color = '#FFFFFF';
  // Function to convert a component from 0-1 to 0-255
  function normalizeAlpha(a: number) {
    return Math.round(a * 255);
  }

  // Function to convert rgb/rgba string to ARGB number
  function rgbStringToArgb(r: number, g: number, b: number, a = 1) {
    const alpha = normalizeAlpha(a);
    return (alpha << 24) | (r << 16) | (g << 8) | b;
  }

  // Function to convert hex string to ARGB number
  function hexStringToArgb(hex: string) {
    hex = hex.replace(/^#/, '');
    if (hex.length === 6) {
      // #RRGGBB format
      return (
        (0xff << 24) |
        (parseInt(hex.slice(0, 2), 16) << 16) |
        (parseInt(hex.slice(2, 4), 16) << 8) |
        parseInt(hex.slice(4, 6), 16)
      );
    } else if (hex.length === 8) {
      // #AARRGGBB format
      return (
        (parseInt(hex.slice(0, 2), 16) << 24) |
        (parseInt(hex.slice(2, 4), 16) << 16) |
        (parseInt(hex.slice(4, 6), 16) << 8) |
        parseInt(hex.slice(6, 8), 16)
      );
    } else {
      throw new Error('Invalid hex color format');
    }
  }

  // Check if color is in rgb or rgba format
  const rgbMatch = color.match(
    /rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})(?:\s*,\s*(\d*(?:\.\d+)?))?\s*\)/
  );
  if (rgbMatch) {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const [_, r, g, b, a] = rgbMatch;
    return rgbStringToArgb(
      parseInt(r),
      parseInt(g),
      parseInt(b),
      a ? parseFloat(a) : 1
    );
  }

  // Check if color is in hex format
  const hexMatch = color.match(/^#([0-9a-fA-F]{6}|[0-9a-fA-F]{8})$/);
  if (hexMatch) {
    return hexStringToArgb(color);
  }

  throw new Error('Unsupported color format color: ' + color.length + color);
}

export default function getTheme() {
  const style = getComputedStyle(document.body);
  const darkMode =
    document.body.getAttribute('data-jp-theme-light') === 'false';
  try {
    const theme = {
      darkMode,
      error: cssColorToArgb(style.getPropertyValue('--pieces-text-error')),
      onPrimary: cssColorToArgb(style.getPropertyValue('--pieces-text-normal')),
      onSecondary: cssColorToArgb(
        style.getPropertyValue('--pieces-text-normal')
      ),
      onSurface: cssColorToArgb(style.getPropertyValue('--pieces-text-normal')),
      primary: cssColorToArgb(style.getPropertyValue('--pieces-text-normal')),
      primaryContainer: cssColorToArgb(
        style.getPropertyValue('--pieces-background-modifier-border-hover')
      ),
      scaffoldBackgroundColor: cssColorToArgb(
        style.getPropertyValue('--pieces-background-secondary')
      ),
      secondary: cssColorToArgb(
        style.getPropertyValue('--pieces-background-modifier-border')
      ),
      surface: cssColorToArgb(
        style.getPropertyValue('--pieces-interactive-normal')
      ),
    };

    return theme;
  } catch (e) {
    return { darkMode };
  }
}
