import { SegmentAnalytics } from './SegmentAnalytics';
import { AnalyticsEnum } from './AnalyticsEnum';
import ConnectorSingleton from '../connection/connectorSingleton';
import Constants from '../const';

export class Heartbeat {
  private readonly interval: number | undefined;
  private handler: NodeJS.Timeout | undefined;

  constructor(intervalInMinutes: number) {
    this.interval = intervalInMinutes * 1000 * 60; // Convert minutes to milliseconds
  }

  start(action: () => void) {
    if (this.interval === undefined) {
      throw new Error('Interval not set.');
    }
    this.handler = setInterval(action, this.interval);
  }

  stop() {
    if (this.handler) {
      clearInterval(this.handler);
      this.handler = undefined;
    } else {
      throw new Error("The heartbeat isn't running.");
    }
  }
}

// Checks the current state of the plugin from the user's POV
export const pluginActivityCheck = async () => {
  SegmentAnalytics.track({
    event: AnalyticsEnum.JUPYTER_HEARTBEAT,
  });

  SegmentAnalytics.track({
    event: Constants.PIECES_CURRENT_VIEW,
  });

  // TODO: Check if side panel is visible

  // Check if POS is running
  ConnectorSingleton.checkConnection({}).then((result) => {
    if (result === true) {
      SegmentAnalytics.track({
        event: AnalyticsEnum.JUPYTER_POS,
      });
    }
  });
};
