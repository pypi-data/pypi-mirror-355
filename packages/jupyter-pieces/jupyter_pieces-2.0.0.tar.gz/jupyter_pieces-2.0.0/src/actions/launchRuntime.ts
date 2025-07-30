import ConnectorSingleton from "../connection/connectorSingleton";

/**
 * This is a simple connection function that will launch Runtime.(PiecesOS)
 *
 * This will just launch our custom URL scheme.
 *
 * TODO consider a better place to put this file (may need to consider a repo re-organization.)
 *
 */
export const launchRuntime: (wait?: boolean) => Promise<void> = async (
  wait?: boolean
) => {
  try {
    // Use the appropriate port number for Obsidian
    await fetch(`${ConnectorSingleton.getHost()}/.well-known/health`);
  } catch (error) {
    // We failed to connect to our PiecesOS because it is not open, so attempt to launch our custom URL scheme.
    window.open('pieces://launch', '_blank');

    if (wait) {
      // Wait a second or so before attempting to connect again.
      // Changing from 1 second to 3 fixes the error pop-up saying it can’t find PiecesOS when it is running.
      return new Promise((resolve) => setTimeout(resolve, 3000));
    }
  }
};
