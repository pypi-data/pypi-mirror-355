/* eslint-disable @typescript-eslint/no-explicit-any */

class DevLogger {
  private static shouldLog: boolean = process.env.NODE_ENV === 'development';

  static log(message: string, ...optionalParams: any[]): void {
    if (this.shouldLog) {
      console.log(message, ...optionalParams);
    }
  }

  static error(message: string, ...optionalParams: any[]): void {
    if (this.shouldLog) {
      console.error(message, ...optionalParams);
    }
  }

  static warn(message: string, ...optionalParams: any[]): void {
    if (this.shouldLog) {
      console.warn(message, ...optionalParams);
    }
  }

  static info(message: string, ...optionalParams: any[]): void {
    if (this.shouldLog) {
      console.info(message, ...optionalParams);
    }
  }

  static table(tabularData: any, properties?: string[]): void {
    if (this.shouldLog) {
      console.table(tabularData, properties);
    }
  }

  static skip() {
    // Intentially do nothing if skip() is pre-chained
    return {
      log: (message: string, ...optionalParams: any[]): void => {},
      error: (message: string, ...optionalParams: any[]): void => {},
      warn: (message: string, ...optionalParams: any[]): void => {},
      info: (message: string, ...optionalParams: any[]): void => {},
      table: (tabularData: any, properties?: string[]): void => {},
    };
  }
}

export default DevLogger;

// Usage:
// DevLogger.log('something'); // Will log in development mode
// DevLogger.error('something'); // Will log in development mode
// DevLogger.skip().log('something'); // Will not log in any mode
