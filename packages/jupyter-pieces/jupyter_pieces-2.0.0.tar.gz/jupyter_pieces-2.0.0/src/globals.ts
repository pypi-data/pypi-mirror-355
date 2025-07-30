import { ElementMap } from './models/ElementMap';
declare global {
  interface HTMLElement {
    createEl<T extends keyof ElementMap>(type: T): ElementMap[T];
    createDiv(className?: string): HTMLDivElement;
    addClasses(classNames: string[]): void;
    addClass(className: string): void;
    setText(text: string): void;
    empty(): void;
  }

  interface Array<T> {
    remove<T>(element: T): void;
  }
}
