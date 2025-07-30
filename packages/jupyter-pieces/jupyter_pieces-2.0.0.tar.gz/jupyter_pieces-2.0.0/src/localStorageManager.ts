import Constants from './const';
import DevLogger from './dev/DevLogger';

let localStorageInitialized = false;
let storedData: { [key: string]: any } = {};

function initializeLocalStorage(reset = false): boolean {
  let success = true;

  if (reset) resetStorage();

  let tempData = localStorage.getItem(Constants.SETTINGS_KEY);
  if (tempData) {
    try {
      storedData = JSON.parse(tempData);
    } catch {
      DevLogger.error(`Unable to parse persistant Pieces' data...`);
      success = false;
    }
  } else {
    DevLogger.warn(`No persistant Pieces' data found`);
    success = false;
  }

  if (!success) resetStorage();
  localStorageInitialized = true;
  return success;
}

export function getStored(key?: string): any {
  if (!localStorageInitialized) initializeLocalStorage();

  if (!key) {
    return storedData;
  }
  return storedData[key];
}

export function setStored(newData: typeof storedData) {
  if (!localStorageInitialized) initializeLocalStorage();

  for (let key in newData) {
    storedData[key] = newData[key];
  }
  localStorage.setItem(Constants.SETTINGS_KEY, JSON.stringify(storedData));
}

export function resetStorage() {
  console.warn('Resetting persistant storage...');
  storedData = {};
  localStorage.setItem(Constants.SETTINGS_KEY, JSON.stringify(storedData));
}
