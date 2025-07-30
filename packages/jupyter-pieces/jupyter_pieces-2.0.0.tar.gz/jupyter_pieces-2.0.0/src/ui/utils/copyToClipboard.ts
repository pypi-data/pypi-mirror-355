import { SegmentAnalytics } from '../../analytics/SegmentAnalytics';
import { AnalyticsEnum } from '../../analytics/AnalyticsEnum';

export default async function copyToClipboard(text: string): Promise<void> {
  try {
    await navigator.clipboard.writeText(text);

    SegmentAnalytics.track({
      event: AnalyticsEnum.JUPYTER_INSERT,
    });
  } catch (err) {
    console.error('Error in copying text: ', err);
  }
}
