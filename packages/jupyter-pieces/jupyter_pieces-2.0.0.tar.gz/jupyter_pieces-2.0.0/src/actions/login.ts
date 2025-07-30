import { UserProfile } from '@pieces.app/pieces-os-client';
import ConnectorSingleton from '../connection/connectorSingleton';
import Notifications from '../connection/Notifications';
import Constants from '../const';
import * as Sentry from '@sentry/browser';
import { SegmentAnalytics } from '../analytics/SegmentAnalytics';
import { AnalyticsEnum } from '../analytics/AnalyticsEnum';

const notifications: Notifications = Notifications.getInstance();
const config: ConnectorSingleton = ConnectorSingleton.getInstance();

// TODO need to add notification handling
export const login = async (): Promise<boolean> => {
  try {
    let user = (await config.userApi.userSnapshot()).user;

    if (!user) {
      user = await config.osApi.signIntoOS();
    }

    notifications.information({ message: Constants.SIGNIN_SUCCESS });

    Sentry.configureScope(async function (scope) {
      let user: UserProfile | undefined;

      if (user) {
        scope.setUser({
          id: user.id,
          email: user.email,
          ip_address: '{{auto}}',
          username: user.username,
          extras: {
            name: user.name,
            picture: user.picture,
            created: user.created,
            updated: user.updated,
          },
        });

        SegmentAnalytics.identify({
          traits: {
            id: user.id,
            email: user.email,
            ip_address: '{{auto}}',
            username: user.username,
            extras: {
              name: user.name,
              picture: user.picture,
              created: user.created,
              updated: user.updated,
            },
          },
        });

        SegmentAnalytics.track({
          event: AnalyticsEnum.JUPYTER_USER_LOGIN,
        });
      }
    });

    return true;
  } catch (error) {
    notifications.error({ message: Constants.SIGNIN_FAIL });
    return false;
  }
};

// TODO need to add notification handling
export const logout = async (): Promise<boolean> => {
  try {
    const user = (await config.userApi.userSnapshot()).user;

    if (user) {
      await config.osApi.signOutOfOS();
      notifications.information({ message: Constants.SIGNOUT_SUCCESS });

      SegmentAnalytics.track({
        event: AnalyticsEnum.JUPYTER_USER_LOGOUT,
      });

      Sentry.setUser(null);

      return true;
    } else {
      notifications.error({ message: Constants.SIGNOUT_FAIL });
      return false;
    }
  } catch (error) {
    return false;
  }
};
