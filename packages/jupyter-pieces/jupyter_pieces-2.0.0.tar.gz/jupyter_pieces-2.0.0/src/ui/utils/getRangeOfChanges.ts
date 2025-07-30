//@ts-nocheck
/*
	Calculates the indexes for each language
	 - incoming is a sorted list of snippets by their language
	 - we use this to figure out which range of indexes associate with each language
*/
export function getRangeOfChanges<returnedMaterial>(
  array: returnedMaterial[]
): [number, number][] {
  const ranges: [number, number][] = [];

  let start = 0;
  let currentElement = array[0];

  for (let i = 1; i < array.length; i++) {
    if (array[i].language !== currentElement.language) {
      if (
        (currentElement.language === 'text' && array[i].language === 'txt') ||
        (currentElement.language === 'yaml' && array[i].language === 'yml')
      ) {
        continue;
      }
      ranges.push([start, i - 1]);
      start = i;
      currentElement = array[i];
    }
  }

  if (start <= array.length - 1) {
    ranges.push([start, array.length - 1]);
  }
  return ranges;
}
