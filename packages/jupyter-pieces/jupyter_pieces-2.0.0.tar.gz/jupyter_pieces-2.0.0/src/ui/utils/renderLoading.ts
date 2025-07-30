export function renderLoading(
  contentEl: Document,
  location = ''
): HTMLDivElement {
  const loading = contentEl.createElement('div');
  loading.classList.add(`${location}bouncing-loader`);
  const loading1 = contentEl.createElement('div');
  const loading2 = contentEl.createElement('div');
  const loading3 = contentEl.createElement('div');

  loading.appendChild(loading1);
  loading.appendChild(loading2);
  loading.appendChild(loading3);

  return loading;
}
