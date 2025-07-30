import { SHA256 } from 'crypto-js';

export const sha256 = (input: string): string => {
  const hash = SHA256(input).toString();
  return hash;
};
