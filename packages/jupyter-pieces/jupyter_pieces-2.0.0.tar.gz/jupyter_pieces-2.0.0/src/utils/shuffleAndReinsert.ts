import { shuffle } from './shuffle';

export const shuffleAndReinsert = <returnedMaterial>(
  array: returnedMaterial[]
): returnedMaterial[] => {
  const elementsToTake = Math.min(5, array.length); // Take up to five elements or the length of the array, whichever is smaller
  const takenElements = shuffle(array.splice(0, elementsToTake)); // Take the first few elements from the array
  takenElements.concat(array); // Concatenate the shuffled elements with the rest of the array
  return takenElements;
};
