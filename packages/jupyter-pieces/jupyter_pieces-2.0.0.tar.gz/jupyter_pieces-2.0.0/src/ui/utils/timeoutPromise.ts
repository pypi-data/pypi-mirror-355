export const timeoutPromise = (duration: number) =>
  new Promise((resolver) => setTimeout(resolver, duration));
