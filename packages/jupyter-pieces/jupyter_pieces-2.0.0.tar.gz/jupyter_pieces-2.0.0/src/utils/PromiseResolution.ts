export const PromiseResolution: {
  <T>(): {
    resolver: { (args: T): T | void };
    rejector: { (args: T): T | void };
    promise: Promise<T>;
  };
} = <T>() => {
  let resolver!: { (args: T): T | void };
  let rejector!: { (args: T): T | void };

  const promise: Promise<T> = new Promise<T>(
    (resolve: { (args: T): T | void }) => {
      resolver = (args: T) => resolve(args);
      rejector = (args: T) => resolve(args);
    }
  );
  return {
    promise,
    resolver,
    rejector,
  };
};
