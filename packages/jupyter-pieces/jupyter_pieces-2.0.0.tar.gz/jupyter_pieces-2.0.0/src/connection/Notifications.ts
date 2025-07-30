import { Notification } from '@jupyterlab/apputils';
import * as Sentry from '@sentry/browser';
import {
  NotificationAction,
  NotificationActionTypeEnum,
} from '../ui/views/shared/types/NotificationParameters';

type ActionHandler = (event: MouseEvent) => void | Promise<void>;

export default class Notifications {
  private static instance: Notifications;
  private actionHandlers: Map<NotificationActionTypeEnum, ActionHandler> = new Map();

  private constructor() {
    /* */
  }

  public static getInstance(): Notifications {
    if (!Notifications.instance) {
      Notifications.instance = new Notifications();
    }

    return Notifications.instance;
  }

  /**
   * Register a handler for a specific notification action type
   */
  public registerActionHandler(type: NotificationActionTypeEnum, handler: ActionHandler): void {
    this.actionHandlers.set(type, handler);
  }

  /**
   * Unregister a handler for a specific notification action type
   */
  public unregisterActionHandler(type: NotificationActionTypeEnum): void {
    this.actionHandlers.delete(type);
  }

  private buildActions(actions?: NotificationAction<NotificationActionTypeEnum>[]): 
    { label: string; callback: (event: MouseEvent) => void; displayType?: 'accent' }[] {
    if (!actions) return [];

    return actions.reduce((acc, action) => {
      if (action.type === NotificationActionTypeEnum.OPEN_LINK) {
        const actiontype =
          action as NotificationAction<NotificationActionTypeEnum.OPEN_LINK>;
        acc.push({
          label: action.title,
          callback: (event: MouseEvent) => {
            window.open(actiontype.params.url);
          },
        });
      } else if (action.type === NotificationActionTypeEnum.SIGN_IN) {
        const handler = this.actionHandlers.get(NotificationActionTypeEnum.SIGN_IN);
        if (handler) {
          acc.push({
            label: action.title,
            callback: handler,
            displayType: 'accent',
          });
        }
      }
      return acc;
    }, [] as { label: string; callback: (event: MouseEvent) => void; displayType?: 'accent' }[]);
  }

  public information({
    message,
    actions,
  }: {
    message: string;
    actions?: NotificationAction<NotificationActionTypeEnum>[];
  }) {
    Notification?.info(message, {
      autoClose: 3000,
      actions: this.buildActions(actions),
    });
  }

  public error({
    message,
    sendToSentry,
    actions,
  }: {
    message: string;
    sendToSentry?: boolean;
    actions?: NotificationAction<NotificationActionTypeEnum>[];
  }) {
    Notification.error(message, {
      autoClose: 3000,
      actions: this.buildActions(actions),
    });
    if (sendToSentry) {
      Sentry.captureException(message);
    }
  }
}
