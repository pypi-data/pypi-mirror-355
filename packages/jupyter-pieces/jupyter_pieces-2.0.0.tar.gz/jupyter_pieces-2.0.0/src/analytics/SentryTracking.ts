import * as Sentry from '@sentry/browser';
import { BrowserTracing } from '@sentry-internal/tracing';
import ConnectorSingleton from '../connection/connectorSingleton';
import Constants from '../const';
import { SegmentAnalytics } from './SegmentAnalytics';

class _SentryTracking {
  private dsn =
    'https://c6adfef82af84ef1a9c74a1e0f3f3aa4@o552351.ingest.sentry.io/4505233984454656';

  public init() {
    const config: ConnectorSingleton = ConnectorSingleton.getInstance();
    Sentry.init({
      dsn: this.dsn,
      integrations: [new BrowserTracing()],
      release: Constants.PLUGIN_VERSION,
      // Set tracesSampleRate to 1.0 to capture 100%
      // of transactions for performance monitoring.
      // We recommend adjusting this value in production
      tracesSampleRate: 0.2,
      environment: 'production',
    });

    Sentry.configureScope(async function (scope) {
      try {
        config.context = await config.api.connect({
          seededConnectorConnection: config.seeded,
        });
      } catch (error) {
        /* */
      }
      if (config.context?.application?.id) {
        scope.setTag('application_id', config.context.application.id);
        scope.setTag('application_name', 'JUPYTER');
        scope.setUser({
          ip_address: '{{auto}}',
          context: config.context,
        });
      }

      try {
        const user = (await config.userApi.userSnapshot()).user;

        if (user) {
          Constants.PIECES_USER_ID = user.id;

          scope.setUser({
            id: Constants.PIECES_USER_ID,
            email: user.email,
            ip_address: '{{auto}}',
            username: user.username,
            extras: {
              name: user.name,
              picture: user.picture,
              created: user.created,
              updated: user.updated,
            },
            context: config.context,
          });

          SegmentAnalytics.identify({
            traits: {
              id: Constants.PIECES_USER_ID,
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
        }
      } catch (error) {
        console.log(`Error in sentry ${error}`);
        scope.setUser({
          ip_address: '{{auto}}',
          context: config.context,
        });
      }
    });
  }

  public async update() {
    const config: ConnectorSingleton = ConnectorSingleton.getInstance();

    const user = (await config.userApi.userSnapshot()).user;

    if (user) {
      Sentry.setUser({
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
    }
  }

  public async close() {
    await Sentry.close(2000);
  }
}

export const SentryTracking = new _SentryTracking();
