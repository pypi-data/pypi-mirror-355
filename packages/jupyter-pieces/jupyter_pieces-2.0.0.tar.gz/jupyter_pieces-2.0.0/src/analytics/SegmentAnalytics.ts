import { AnalyticsEnum } from './AnalyticsEnum';
import Constants from '../const';
import { GroupedTimestamp } from '@pieces.app/pieces-os-client';
import ConnectorSingleton from '../connection/connectorSingleton';
import { AppletAnalytics } from '../ui/views/shared/types/AppletAnalytics.enum';

class _SegmentAnalytics {
  // private client = new Analytics({ writeKey: 'gxiCvwZq0Wr3UCCNIa38DR0UPWXDo5SX' })

  public init() {
    const segmentInit = document.createElement('script');

    segmentInit.textContent = `
            !function(){var analytics=window.analytics=window.analytics||[];if(!analytics.initialize)if(analytics.invoked)window.console&&console.error&&console.error("Segment material included twice.");else{analytics.invoked=!0;analytics.methods=["trackSubmit","trackClick","trackLink","trackForm","pageview","identify","reset","group","track","ready","alias","debug","page","once","off","on","addSourceMiddleware","addIntegrationMiddleware","setAnonymousId","addDestinationMiddleware"];analytics.factory=function(e){return function(){var t=Array.prototype.slice.call(arguments);t.unshift(e);analytics.push(t);return analytics}};for(var e=0;e<analytics.methods.length;e++){var key=analytics.methods[e];analytics[key]=analytics.factory(key)}analytics.load=function(key,e){var t=document.createElement("script");t.type="text/javascript";t.async=!0;t.src="https://cdn.segment.com/analytics.js/v1/" + key + "/analytics.min.js";var n=document.getElementsByTagName("script")[0];n.parentNode.insertBefore(t,n);analytics._loadOptions=e};analytics._writeKey="6EJnxiU3blniIGkNS9uRtX3DcD72uzWS";;analytics.SNIPPET_VERSION="4.15.3";
            analytics.load("6EJnxiU3blniIGkNS9uRtX3DcD72uzWS");
            }}();
            `;

    document.head.appendChild(segmentInit);
  }

  public track({ event }: { event: AnalyticsEnum | AppletAnalytics }) {
    const config: ConnectorSingleton = ConnectorSingleton.getInstance();

    const d = new Date();
    const utcDate = new Date(
      Date.UTC(
        d.getUTCFullYear(),
        d.getUTCMonth(),
        d.getUTCDate(),
        d.getUTCHours(),
        d.getUTCMinutes(),
        d.getUTCSeconds(),
        d.getUTCMilliseconds()
      )
    );

    // Have to ignore since this is running in the DOM
    // @ts-ignore
    analytics.track(
      event,
      {
        userId: Constants.PIECES_USER_ID,
        timestamp: utcDate, // Get UTC date
        properties: {
          ...config.context,
        },
      },
      (error: any) => {
        if (error) {
        } else {
        }
      }
    );
  }

  public identify({
    traits,
  }: {
    traits: {
      id: string;
      email?: string;
      ip_address?: '{{auto}}';
      username?: string;
      extras?: {
        name?: string;
        picture?: string;
        created?: GroupedTimestamp;
        updated?: GroupedTimestamp;
      };
    };
  }) {
    const config: ConnectorSingleton = ConnectorSingleton.getInstance();

    const d = new Date();
    const utcDate = new Date(
      Date.UTC(
        d.getUTCFullYear(),
        d.getUTCMonth(),
        d.getUTCDate(),
        d.getUTCHours(),
        d.getUTCMinutes(),
        d.getUTCSeconds(),
        d.getUTCMilliseconds()
      )
    );

    // Have to ignore since this is running in the DOM
    // @ts-ignore
    analytics.identify(
      Constants.PIECES_USER_ID,
      {
        context: config.context,
        timestamp: utcDate, // Get UTC time
        ...traits,
      },
      (error: any) => {
        if (error) {
        } else {
        }
      }
    );
  }
}

export const SegmentAnalytics = new _SegmentAnalytics();
