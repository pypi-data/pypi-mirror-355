/*
  In this environment, the rest of this file will run as a script.
  In other environments, it may be required to add these prototype extensions into a function, and run that function.

  If one of these prototypes returns `this` then you can chain the function calls one after another i.e:

  element.createDiv()
    .addClass('hello')
    .setText('world');
*/

export function createEl<K extends keyof HTMLElementTagNameMap>(
	parent: Element,
	tagName: K
): HTMLElementTagNameMap[K] {
	const el = document.createElement(tagName);
	parent.appendChild(el);
	return el;
}

export function addClass(el: Element, className: string) {
	el.classList.add(className);
}

export function addClasses(el: Element, classNames: string[]) {
	el.classList.add(...classNames);
}

export function createDiv(parent: Element, className?: string): HTMLDivElement {
	const el = createEl(parent, 'div');
	if (className) addClass(el, className);
	return el;
}

export function setText(el: HTMLElement, text: string) {
	el.innerText = text;
	return el;
}

export function emptyEl(el: HTMLElement) {
	el.innerHTML = '';
}
