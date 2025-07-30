import ConnectorSingleton from "../connection/connectorSingleton";
import DevLogger from "../dev/DevLogger";

export default class BrowserUrl {
  /**
   * Wraps a URL with additional query parameters based on the current connector state
   * @param url - Base URL to launch
   * @returns The modified URL with appended parameters
   */
  public static appendParams(url: string): string {
    const connector = ConnectorSingleton.getInstance();

    if (!connector.context || !connector.context.os) {
      DevLogger.log('No OS information in API Context');
      return url;
    }

    const urlObj = new URL(url);
    const searchParams = urlObj.searchParams;

    // add os ID param
    searchParams.set('os', connector.context.os);

    // add user ID param, if authenticated
    if (connector.context.user?.id) {
      searchParams.set('user', connector.context.user.id);
    }

    const urlWithParams = urlObj.toString();

    return urlWithParams;
  }

  /**
   * Wraps a URL with additional query parameters based on the current connector state and launches in browser
   * @param url - Base URL to launch
   * @returns The modified URL with appended parameters
   */
  public static launch(url: string) {
    const urlWithParams = this.appendParams(url);

    window.open(urlWithParams, '_blank');
  }
}
