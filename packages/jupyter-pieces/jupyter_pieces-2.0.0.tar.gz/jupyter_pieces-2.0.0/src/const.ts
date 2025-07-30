import { AnalyticsEnum } from './analytics/AnalyticsEnum';

export default class Constants {
  public static PLUGIN_VERSION = '1.13.0';
  public static PIECES_USER_ID = '';
  public static PIECES_CURRENT_VIEW:
    | AnalyticsEnum.JUPYTER_VIEW_MATERIAL_LIST
    | AnalyticsEnum.JUPYTER_VIEW_CHATBOT =
    AnalyticsEnum.JUPYTER_VIEW_MATERIAL_LIST;

  public static readonly DEFAULT_TAB: 'copilot' | 'drive' = 'copilot';
  public static readonly PIECES_LOGO = `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="20" height="20" viewBox="0 0 100 100" fill="currentColor" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M 41 1.601562 C 30.199219 4.601562 21.101562 12.101562 16.199219 22 L 13.5 27.5 L 13.199219 54.699219 L 12.898438 82 L 15.699219 87.199219 C 25.5 105.101562 51.101562 102.800781 57.300781 83.300781 C 58.199219 80.699219 59 77.398438 59.199219 76.101562 C 59.398438 74.398438 60.601562 73.300781 63.699219 72.101562 C 77.898438 66.601562 87 53.101562 87 37.5 C 87 28.699219 84.898438 22.398438 79.601562 15.199219 C 71.199219 3.699219 54.601562 -2.199219 41 1.601562 Z M 62.699219 11.800781 C 83.199219 22.300781 84.101562 51.5 64.199219 62.300781 L 59.199219 65 L 58.800781 52.5 C 58.398438 39 57.699219 37.101562 51.699219 32.601562 C 48 29.898438 40.199219 30 36.199219 32.898438 C 31.300781 36.300781 29.699219 41.101562 30.199219 50.398438 C 30.898438 62.898438 35.5 69.898438 45.601562 73.300781 C 48.800781 74.398438 49.5 75.199219 49.800781 77.601562 C 50.101562 81.300781 47 86.398438 42.800781 89.101562 C 40.300781 90.601562 38.300781 91 34.898438 90.699219 C 29.398438 90.199219 25.898438 87.898438 23 82.699219 C 20.898438 79 20.800781 78 21.199219 54.699219 C 21.5 31.699219 21.601562 30.300781 23.800781 25.800781 C 26.699219 20 34.601562 12.699219 40.300781 10.601562 C 46.199219 8.398438 57.199219 9 62.699219 11.800781 Z M 49 40.898438 C 50.101562 43.101562 50.398438 66 49.300781 66 C 47.5 66 42 61.898438 40.398438 59.5 C 38.199219 56.199219 37.800781 43.101562 39.898438 40.699219 C 41.800781 38.300781 47.699219 38.5 49 40.898438 Z M 49 40.898438 "/></svg>`;
  public static readonly PIECES_LOGO_ALT =
    'M 8.199219 0.320312 C 6.039062 0.921875 4.21875 2.421875 3.238281 4.398438 L 2.699219 5.5 L 2.640625 10.941406 L 2.578125 16.398438 L 3.140625 17.441406 C 5.101562 21.019531 10.21875 20.558594 11.460938 16.660156 C 11.640625 16.140625 11.800781 15.480469 11.839844 15.21875 C 11.878906 14.878906 12.121094 14.660156 12.738281 14.421875 C 15.578125 13.320312 17.398438 10.621094 17.398438 7.5 C 17.398438 5.738281 16.980469 4.480469 15.921875 3.039062 C 14.238281 0.738281 10.921875 -0.441406 8.199219 0.320312 Z M 12.539062 2.359375 C 16.640625 4.460938 16.820312 10.300781 12.839844 12.460938 L 11.839844 13 L 11.761719 10.5 C 11.679688 7.800781 11.539062 7.421875 10.339844 6.519531 C 9.601562 5.980469 8.039062 6 7.238281 6.578125 C 6.261719 7.261719 5.941406 8.21875 6.039062 10.078125 C 6.179688 12.578125 7.101562 13.980469 9.121094 14.660156 C 9.761719 14.878906 9.898438 15.039062 9.960938 15.519531 C 10.019531 16.261719 9.398438 17.28125 8.558594 17.820312 C 8.058594 18.121094 7.660156 18.199219 6.980469 18.140625 C 5.878906 18.039062 5.179688 17.578125 4.601562 16.539062 C 4.179688 15.800781 4.160156 15.601562 4.238281 10.941406 C 4.300781 6.339844 4.320312 6.058594 4.761719 5.160156 C 5.339844 4 6.921875 2.539062 8.058594 2.121094 C 9.238281 1.679688 11.441406 1.800781 12.539062 2.359375 Z M 9.800781 8.179688 C 10.019531 8.621094 10.078125 13.199219 9.859375 13.199219 C 9.5 13.199219 8.398438 12.378906 8.078125 11.898438 C 7.640625 11.238281 7.558594 8.621094 7.980469 8.140625 C 8.359375 7.660156 9.539062 7.699219 9.800781 8.179688 Z M 9.800781 8.179688';
  public static readonly REFRESH_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-refresh-cw"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>`;
  public static readonly CANCEL_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-x"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>`;
  public static readonly COPY_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-copy"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>`;
  public static readonly SHARE_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-share-2"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" x2="15.42" y1="13.51" y2="17.49"/><line x1="15.41" x2="8.59" y1="6.51" y2="10.49"/></svg>`;
  public static readonly DELETE_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-trash-2"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" x2="10" y1="11" y2="17"/><line x1="14" x2="14" y1="11" y2="17"/></svg>`;
  public static readonly EDIT_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-edit-3"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>`;
  public static readonly EXPAND_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-expand"><path d="m21 21-6-6m6 6v-4.8m0 4.8h-4.8"/><path d="M3 16.2V21m0 0h4.8M3 21l6-6"/><path d="M21 7.8V3m0 0h-4.8M21 3l-6 6"/><path d="M3 7.8V3m0 0h4.8M3 3l6 6"/></svg>`;
  public static readonly SAVE_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-save-all"><path d="M6 4a2 2 0 0 1 2-2h10l4 4v10.2a2 2 0 0 1-2 1.8H8a2 2 0 0 1-2-2Z"/><path d="M10 2v4h6"/><path d="M18 18v-7h-8v7"/><path d="M18 22H4a2 2 0 0 1-2-2V6"/></svg>`;
  public static readonly SAVE_ALL_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-save-all"><path d="M6 4a2 2 0 0 1 2-2h10l4 4v10.2a2 2 0 0 1-2 1.8H8a2 2 0 0 1-2-2Z"/><path d="M10 2v4h6"/><path d="M18 18v-7h-8v7"/><path d="M18 22H4a2 2 0 0 1-2-2V6"/></svg>`;
  public static readonly CODE_SVG = `<svg width="70" height="70" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
 	<path d="M27.96 8.26875L16.96 2.25C16.6661 2.0876 16.3358 2.00242 16 2.00242C15.6642 2.00242 15.3339 2.0876 15.04 2.25L4.04 8.27125C3.72586 8.44313 3.46363 8.6962 3.28069 9.00403C3.09775 9.31186 3.00081 9.66316 3 10.0212V21.9762C3.00081 22.3343 3.09775 22.6856 3.28069 22.9935C3.46363 23.3013 3.72586 23.5544 4.04 23.7262L15.04 29.7475C15.3339 29.9099 15.6642 29.9951 16 29.9951C16.3358 29.9951 16.6661 29.9099 16.96 29.7475L27.96 23.7262C28.2741 23.5544 28.5364 23.3013 28.7193 22.9935C28.9023 22.6856 28.9992 22.3343 29 21.9762V10.0225C28.9999 9.66378 28.9032 9.31169 28.7203 9.00314C28.5373 8.69459 28.2747 8.44094 27.96 8.26875ZM16 4L26.0425 9.5L22.3213 11.5375L12.2775 6.0375L16 4ZM16 15L5.9575 9.5L10.195 7.18L20.2375 12.68L16 15ZM5 11.25L15 16.7225V27.4463L5 21.9775V11.25ZM27 21.9725L17 27.4463V16.7275C21.6275 14.1954 21.5407 14.2441 27 11.25V21.9713V21.9725Z" fill="currentColor"/>
 	<path d="M23.2717 20.6605L24.589 17.9947L22.4496 16.6711" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
 	<path d="M20.7283 17.3396L19.411 20.0053L21.5503 21.3289" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
 	</svg>
 	`;
  public static readonly SETTINGS_ICON = `<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 0 24 24" width="24px" fill="currentColor"><path d="M0 0h24v24H0V0z" fill="none"/><path d="M19.43 12.98c.04-.32.07-.64.07-.98 0-.34-.03-.66-.07-.98l2.11-1.65c.19-.15.24-.42.12-.64l-2-3.46c-.09-.16-.26-.25-.44-.25-.06 0-.12.01-.17.03l-2.49 1c-.52-.4-1.08-.73-1.69-.98l-.38-2.65C14.46 2.18 14.25 2 14 2h-4c-.25 0-.46.18-.49.42l-.38 2.65c-.61.25-1.17.59-1.69.98l-2.49-1c-.06-.02-.12-.03-.18-.03-.17 0-.34.09-.43.25l-2 3.46c-.13.22-.07.49.12.64l2.11 1.65c-.04.32-.07.65-.07.98 0 .33.03.66.07.98l-2.11 1.65c-.19.15-.24.42-.12.64l2 3.46c.09.16.26.25.44.25.06 0 .12-.01.17-.03l2.49-1c.52.4 1.08.73 1.69.98l.38 2.65c.03.24.24.42.49.42h4c.25 0 .46-.18.49-.42l.38-2.65c.61-.25 1.17-.59 1.69-.98l2.49 1c.06.02.12.03.18.03.17 0 .34-.09.43-.25l2-3.46c.12-.22.07-.49-.12-.64l-2.11-1.65zm-1.98-1.71c.04.31.05.52.05.73 0 .21-.02.43-.05.73l-.14 1.13.89.7 1.08.84-.7 1.21-1.27-.51-1.04-.42-.9.68c-.43.32-.84.56-1.25.73l-1.06.43-.16 1.13-.2 1.35h-1.4l-.19-1.35-.16-1.13-1.06-.43c-.43-.18-.83-.41-1.23-.71l-.91-.7-1.06.43-1.27.51-.7-1.21 1.08-.84.89-.7-.14-1.13c-.03-.31-.05-.54-.05-.74s.02-.43.05-.73l.14-1.13-.89-.7-1.08-.84.7-1.21 1.27.51 1.04.42.9-.68c.43-.32.84-.56 1.25-.73l1.06-.43.16-1.13.2-1.35h1.39l.19 1.35.16 1.13 1.06.43c.43.18.83.41 1.23.71l.91.7 1.06-.43 1.27-.51.7 1.21-1.07.85-.89.7.14 1.13zM12 8c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4-1.79-4-4-4zm0 6c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2z"/></svg>`;
  public static readonly AI_SVG = `<svg width="90" height="100" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
    <path d="M11.452 12.4675C11.4704 12.0122 11.2159 11.6322 10.8836 11.6188C10.5514 11.6054 10.2671 11.9636 10.2487 12.419C10.2304 12.8743 10.4848 13.2543 10.8171 13.2677C11.1493 13.2811 11.4336 12.9229 11.452 12.4675Z" fill="currentColor"/>
    <path d="M14.7595 10.9541C14.7779 10.4988 14.5234 10.1188 14.1911 10.1054C13.8589 10.092 13.5746 10.4502 13.5562 10.9055C13.5379 11.3609 13.7923 11.7409 14.1246 11.7543C14.4568 11.7677 14.7411 11.4094 14.7595 10.9541Z" fill="currentColor"/>
    <path d="M16.6069 5.5297C16.6069 5.5297 16.5846 5.5297 16.5846 5.5074L11.0319 2.69758C10.6305 2.49688 10.1176 2.51918 9.76079 2.80908C9.56008 2.96518 9.35938 3.09898 9.11408 3.16588C9.35938 4.61539 9.69389 6.46631 9.78309 6.82311C9.82769 7.02381 9.84999 7.22451 9.84999 7.44751C9.84999 8.47332 9.24788 9.12003 8.48968 9.12003C7.73147 9.12003 7.12936 8.45102 7.12936 7.44751C7.12936 7.22451 7.15167 7.00151 7.21857 6.82311C7.30777 6.51091 7.61997 4.66 7.88757 3.18818C7.66457 3.09898 7.44157 2.98748 7.24087 2.83138C6.88406 2.54148 6.39346 2.49688 5.96976 2.71988L0.417017 5.5297C0.417017 5.5297 0.394716 5.5297 0.394716 5.552C0.238614 5.6412 0.149414 5.7973 0.149414 5.9534V13.201C0.149414 13.3794 0.238614 13.5355 0.394716 13.6247L8.26667 17.9955C8.28897 18.0178 8.31128 18.0178 8.33358 18.0178C8.35588 18.0178 8.35588 18.0401 8.37818 18.0401C8.42278 18.0401 8.46738 18.0624 8.48968 18.0624C8.53428 18.0624 8.57888 18.0624 8.60118 18.0401C8.62348 18.0401 8.62348 18.0401 8.64578 18.0178C8.66808 18.0178 8.69038 17.9955 8.71268 17.9955L16.5846 13.6247C16.7407 13.5355 16.8299 13.3794 16.8299 13.201V5.9534C16.8522 5.775 16.763 5.6189 16.6069 5.5297ZM1.10832 6.75621L8.02137 10.5918V16.7467L1.10832 12.9111V6.75621ZM15.8933 12.9111L8.98028 16.7467V10.5918L15.8933 6.75621V12.9111Z" fill="currentColor"/>
    <path d="M8.48997 2.27462C9.11809 2.27462 9.62728 1.76543 9.62728 1.13731C9.62728 0.50919 9.11809 0 8.48997 0C7.86185 0 7.35266 0.50919 7.35266 1.13731C7.35266 1.76543 7.86185 2.27462 8.48997 2.27462Z" fill="currentColor"/>
    <path d="M15.5803 0.578369H8.82335H8.44425H1.4197C-1.03332 0.578369 -0.00751388 2.56308 2.2225 2.56308C4.56402 2.56308 5.50063 1.55958 7.35154 1.60418C7.84214 1.60418 8.31045 1.60418 8.60035 1.60418C8.80105 1.60418 9.15785 1.60418 9.64846 1.60418C11.5217 1.55958 12.4583 2.56308 14.7775 2.56308C17.0075 2.56308 18.0333 0.578369 15.5803 0.578369Z" fill="currentColor"/>
    </svg>`;
  public static readonly SEND_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-send-horizontal"><path d="m3 3 3 9-3 9 19-9Z"/><path d="M6 12h16"/></svg>`;
  public static readonly USER_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-user-circle-2"><path d="M18 20a6 6 0 0 0-12 0"/><circle cx="12" cy="10" r="4"/><circle cx="12" cy="12" r="10"/></svg>`;
  public static readonly OPEN_ICON =
    '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-panel-right-open"><rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><line x1="15" x2="15" y1="3" y2="21"/><path d="m10 15-3-3 3-3"/></svg>';
  public static readonly STAR_ICON = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-star"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>`;
  public static readonly STICKY_NOTE_ICON = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-sticky-note"><path d="M15.5 3H5a2 2 0 0 0-2 2v14c0 1.1.9 2 2 2h14a2 2 0 0 0 2-2V8.5L15.5 3Z"/><path d="M15 3v6h6"/></svg>`;
  public static readonly COPILOT_BLACK = `<svg height="48px" viewBox="0 0 1784 643" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M321.407 133.742C255.032 133.742 199.425 183.363 191.256 248.467L191.07 250.425V250.798V251.172C190.606 254.063 190.42 256.954 190.328 259.939V443.031C190.328 479.221 219.198 508.695 255.125 509.254H256.331C292.35 509.254 321.685 480.247 322.242 444.151V434.357C270.627 429.6 230.988 386.509 230.153 334.463V295.382C230.802 259.193 260.509 230.279 296.528 230.838C331.711 231.398 360.118 259.939 360.768 295.382V390.146C414.425 373.357 452.672 323.271 452.672 264.882C452.579 192.504 393.816 133.742 321.407 133.742Z" fill="currentColor"/>
    <path d="M296.179 270.062H295.735C281.876 270.062 270.504 281.165 270.059 295.134V330.862C270.059 360.68 291.471 386.11 320.7 390.856L321.499 390.946V295.94C321.499 281.792 310.216 270.33 296.179 270.062Z" fill="currentColor"/>
    <path d="M321.5 0C143.936 0 0 143.936 0 321.5C0 499.064 143.936 643 321.5 643C499.064 643 643 499.064 643 321.5C643 143.936 499.064 0 321.5 0ZM363.35 428.482L361.133 429.036L360.579 429.129V441.785C360.579 497.863 316.142 543.778 260.064 545.626H258.401H256.646C199.921 545.626 153.729 500.173 152.805 443.541V441.785V261.45C152.805 256.738 153.082 252.119 153.729 247.407L153.821 246.576L154.098 244.451C164.353 162.505 233.365 99.8682 316.511 97.3738L319.006 97.2815H321.592C414.809 97.2815 490.38 172.575 490.38 265.515C490.287 343.395 436.889 409.82 363.35 428.482Z" fill="currentColor"/>
    <path d="M1585.97 443.811C1586.62 427.602 1577.56 414.074 1565.73 413.597C1553.9 413.119 1543.79 425.872 1543.13 442.082C1542.48 458.291 1551.53 471.818 1563.36 472.296C1575.19 472.773 1585.31 460.02 1585.97 443.811Z" fill="currentColor"/>
    <path d="M1703.74 389.948C1704.4 373.739 1695.34 360.211 1683.51 359.734C1671.68 359.256 1661.56 372.009 1660.91 388.218C1660.25 404.428 1669.31 417.955 1681.14 418.433C1692.97 418.91 1703.09 406.157 1703.74 389.948Z" fill="currentColor"/>
    <path d="M1769.51 196.847C1769.51 196.847 1768.72 196.847 1768.72 196.053L1571.04 96.0268C1556.75 88.8821 1538.5 89.6759 1525.79 99.9962C1518.65 105.553 1511.5 110.316 1502.77 112.698C1511.5 164.299 1523.41 230.19 1526.59 242.891C1528.18 250.036 1528.97 257.181 1528.97 265.119C1528.97 301.637 1507.53 324.659 1480.54 324.659C1453.55 324.659 1432.12 300.843 1432.12 265.119C1432.12 257.181 1432.91 249.242 1435.29 242.891C1438.47 231.777 1449.58 165.887 1459.11 113.492C1451.17 110.316 1443.23 106.347 1436.09 100.79C1423.39 90.4698 1405.92 88.8821 1390.84 96.8207L1193.17 196.847C1193.17 196.847 1192.37 196.847 1192.37 197.641C1186.81 200.817 1183.64 206.374 1183.64 211.931V469.936C1183.64 476.287 1186.81 481.844 1192.37 485.019L1472.6 640.616C1473.4 641.41 1474.19 641.41 1474.99 641.41C1475.78 641.41 1475.78 642.204 1476.57 642.204C1478.16 642.204 1479.75 642.998 1480.54 642.998C1482.13 642.998 1483.72 642.998 1484.51 642.204C1485.31 642.204 1485.31 642.204 1486.1 641.41C1486.89 641.41 1487.69 640.616 1488.48 640.616L1768.72 485.019C1774.27 481.844 1777.45 476.287 1777.45 469.936V211.931C1778.24 205.58 1775.07 200.023 1769.51 196.847ZM1217.78 240.51L1463.87 377.054V596.16L1217.78 459.616V240.51ZM1744.11 459.616L1498.01 596.16V377.054L1744.11 240.51V459.616Z" fill="currentColor"/>
    <path d="M1480.52 80.9739C1502.88 80.9739 1521.01 62.8473 1521.01 40.487C1521.01 18.1266 1502.88 0 1480.52 0C1458.16 0 1440.03 18.1266 1440.03 40.487C1440.03 62.8473 1458.16 80.9739 1480.52 80.9739Z" fill="currentColor"/>
    <path d="M1732.96 20.634H1492.42H1478.93H1228.86C1141.54 20.634 1178.05 91.2878 1257.44 91.2878C1340.79 91.2878 1374.14 55.5639 1440.03 57.1517C1457.49 57.1517 1474.16 57.1517 1484.48 57.1517C1491.63 57.1517 1504.33 57.1517 1521.8 57.1517C1588.48 55.5639 1621.82 91.2878 1704.38 91.2878C1783.77 91.2878 1820.29 20.634 1732.96 20.634Z" fill="currentColor"/>
    <path fill-rule="evenodd" clip-rule="evenodd" d="M854.029 259.703C858.681 255.05 866.225 255.05 870.878 259.703L974.052 362.877C978.704 367.529 978.704 375.073 974.052 379.726C969.399 384.378 961.855 384.378 957.203 379.726L854.029 276.552C849.376 271.899 849.376 264.355 854.029 259.703Z" fill="currentColor"/>
    <path fill-rule="evenodd" clip-rule="evenodd" d="M852.616 378.839C847.963 374.187 847.963 366.643 852.616 361.99L955.79 258.816C960.443 254.164 967.986 254.164 972.639 258.816C977.292 263.469 977.292 271.013 972.639 275.665L869.465 378.839C864.812 383.492 857.269 383.492 852.616 378.839Z" fill="currentColor"/>
    </svg>`;
  public static readonly COPILOT_WHITE = `<svg width="1784" height="643" viewBox="0 0 1784 643" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M321.407 133.742C255.032 133.742 199.425 183.363 191.256 248.466L191.07 250.425V250.798V251.171C190.606 254.063 190.42 256.954 190.328 259.939V443.031C190.328 479.221 219.198 508.695 255.125 509.254H256.331C292.35 509.254 321.685 480.247 322.242 444.151V434.357C270.627 429.6 230.988 386.509 230.153 334.463V295.382C230.802 259.193 260.509 230.278 296.528 230.838C331.711 231.398 360.118 259.939 360.768 295.382V390.146C414.425 373.357 452.672 323.27 452.672 264.882C452.579 192.503 393.816 133.742 321.407 133.742Z" fill="#181818"/>
    <path d="M296.179 270.062H295.735C281.876 270.062 270.504 281.165 270.059 295.134V330.862C270.059 360.68 291.471 386.11 320.7 390.856L321.499 390.946V295.94C321.499 281.792 310.216 270.33 296.179 270.062Z" fill="#181818"/>
    <path d="M321.5 0C143.936 0 0 143.936 0 321.5C0 499.064 143.936 643 321.5 643C499.064 643 643 499.064 643 321.5C643 143.936 499.064 0 321.5 0ZM363.35 428.482L361.133 429.036L360.579 429.129V441.785C360.579 497.863 316.142 543.778 260.064 545.626H258.401H256.646C199.921 545.626 153.729 500.173 152.805 443.541V441.785V261.45C152.805 256.738 153.082 252.119 153.729 247.407L153.821 246.576L154.098 244.451C164.353 162.505 233.365 99.8682 316.511 97.3738L319.006 97.2815H321.592C414.809 97.2815 490.38 172.575 490.38 265.515C490.287 343.395 436.889 409.82 363.35 428.482Z" fill="#181818"/>
    <path d="M1585.97 443.811C1586.62 427.602 1577.56 414.074 1565.73 413.597C1553.9 413.119 1543.79 425.872 1543.13 442.082C1542.48 458.291 1551.53 471.818 1563.36 472.296C1575.19 472.773 1585.31 460.02 1585.97 443.811Z" fill="#181818"/>
    <path d="M1703.74 389.948C1704.4 373.739 1695.34 360.211 1683.51 359.734C1671.68 359.256 1661.56 372.009 1660.91 388.218C1660.25 404.428 1669.31 417.955 1681.14 418.433C1692.97 418.91 1703.09 406.157 1703.74 389.948Z" fill="#181818"/>
    <path d="M1769.51 196.847C1769.51 196.847 1768.72 196.847 1768.72 196.053L1571.04 96.0268C1556.75 88.8821 1538.5 89.6759 1525.79 99.9962C1518.65 105.553 1511.5 110.316 1502.77 112.698C1511.5 164.299 1523.41 230.19 1526.59 242.891C1528.18 250.036 1528.97 257.181 1528.97 265.119C1528.97 301.637 1507.53 324.659 1480.54 324.659C1453.55 324.659 1432.12 300.843 1432.12 265.119C1432.12 257.181 1432.91 249.242 1435.29 242.891C1438.47 231.777 1449.58 165.887 1459.11 113.492C1451.17 110.316 1443.23 106.347 1436.09 100.79C1423.39 90.4698 1405.92 88.8821 1390.84 96.8207L1193.17 196.847C1193.17 196.847 1192.37 196.847 1192.37 197.641C1186.81 200.817 1183.64 206.374 1183.64 211.931V469.936C1183.64 476.287 1186.81 481.844 1192.37 485.019L1472.6 640.616C1473.4 641.41 1474.19 641.41 1474.99 641.41C1475.78 641.41 1475.78 642.204 1476.57 642.204C1478.16 642.204 1479.75 642.998 1480.54 642.998C1482.13 642.998 1483.72 642.998 1484.51 642.204C1485.31 642.204 1485.31 642.204 1486.1 641.41C1486.89 641.41 1487.69 640.616 1488.48 640.616L1768.72 485.019C1774.27 481.844 1777.45 476.287 1777.45 469.936V211.931C1778.24 205.58 1775.07 200.023 1769.51 196.847ZM1217.78 240.51L1463.87 377.054V596.16L1217.78 459.616V240.51ZM1744.11 459.616L1498.01 596.16V377.054L1744.11 240.51V459.616Z" fill="#181818"/>
    <path d="M1480.52 80.9739C1502.88 80.9739 1521.01 62.8473 1521.01 40.487C1521.01 18.1266 1502.88 0 1480.52 0C1458.16 0 1440.03 18.1266 1440.03 40.487C1440.03 62.8473 1458.16 80.9739 1480.52 80.9739Z" fill="#181818"/>
    <path d="M1732.96 20.6343H1492.42H1478.93H1228.86C1141.54 20.6343 1178.05 91.288 1257.44 91.288C1340.79 91.288 1374.14 55.5642 1440.03 57.1519C1457.49 57.1519 1474.16 57.1519 1484.48 57.1519C1491.63 57.1519 1504.33 57.1519 1521.8 57.1519C1588.48 55.5642 1621.82 91.288 1704.38 91.288C1783.77 91.288 1820.29 20.6343 1732.96 20.6343Z" fill="#181818"/>
    <path fill-rule="evenodd" clip-rule="evenodd" d="M854.029 259.702C858.681 255.05 866.225 255.05 870.878 259.702L974.052 362.876C978.704 367.529 978.704 375.073 974.052 379.725C969.399 384.378 961.855 384.378 957.203 379.725L854.029 276.551C849.376 271.899 849.376 264.355 854.029 259.702Z" fill="#181818"/>
    <path fill-rule="evenodd" clip-rule="evenodd" d="M852.616 378.84C847.963 374.187 847.963 366.643 852.616 361.991L955.79 258.817C960.443 254.164 967.986 254.164 972.639 258.817C977.292 263.469 977.292 271.013 972.639 275.666L869.465 378.84C864.812 383.492 857.269 383.492 852.616 378.84Z" fill="#181818"/>
    </svg>`;
  public static readonly ENRICH_ICON =
    '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-sparkles"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/><path d="M5 3v4"/><path d="M19 17v4"/><path d="M3 5h4"/><path d="M17 19h4"/></svg>';

  public static readonly SAVE_ALL_ICON = `<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-save-all"><path d="M6 4a2 2 0 0 1 2-2h10l4 4v10.2a2 2 0 0 1-2 1.8H8a2 2 0 0 1-2-2Z"/><path d="M10 2v4h6"/><path d="M18 18v-7h-8v7"/><path d="M18 22H4a2 2 0 0 1-2-2V6"/></svg>`;
  public static readonly PLUS_ICON = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-plus"><path d="M5 12h14"/><path d="M12 5v14"/></svg>`;
  public static readonly FILTER_ICON = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-filter"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>`;
  public static readonly META_SVG =
    '<svg id="Layer_1" data-name="Layer 1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 287.56 191"><defs><style>.cls-1{fill:#0081fb;}.cls-2{fill:url(#linear-gradient);}.cls-3{fill:url(#linear-gradient-2);}</style><linearGradient id="linear-gradient" x1="62.34" y1="101.45" x2="260.34" y2="91.45" gradientTransform="matrix(1, 0, 0, -1, 0, 192)" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#0064e1"/><stop offset="0.4" stop-color="#0064e1"/><stop offset="0.83" stop-color="#0073ee"/><stop offset="1" stop-color="#0082fb"/></linearGradient><linearGradient id="linear-gradient-2" x1="41.42" y1="53" x2="41.42" y2="126" gradientTransform="matrix(1, 0, 0, -1, 0, 192)" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#0082fb"/><stop offset="1" stop-color="#0064e0"/></linearGradient></defs><title>facebook-meta</title><path class="cls-1" d="M31.06,126c0,11,2.41,19.41,5.56,24.51A19,19,0,0,0,53.19,160c8.1,0,15.51-2,29.79-21.76,11.44-15.83,24.92-38,34-52l15.36-23.6c10.67-16.39,23-34.61,37.18-47C181.07,5.6,193.54,0,206.09,0c21.07,0,41.14,12.21,56.5,35.11,16.81,25.08,25,56.67,25,89.27,0,19.38-3.82,33.62-10.32,44.87C271,180.13,258.72,191,238.13,191V160c17.63,0,22-16.2,22-34.74,0-26.42-6.16-55.74-19.73-76.69-9.63-14.86-22.11-23.94-35.84-23.94-14.85,0-26.8,11.2-40.23,31.17-7.14,10.61-14.47,23.54-22.7,38.13l-9.06,16c-18.2,32.27-22.81,39.62-31.91,51.75C84.74,183,71.12,191,53.19,191c-21.27,0-34.72-9.21-43-23.09C3.34,156.6,0,141.76,0,124.85Z"/><path class="cls-2" d="M24.49,37.3C38.73,15.35,59.28,0,82.85,0c13.65,0,27.22,4,41.39,15.61,15.5,12.65,32,33.48,52.63,67.81l7.39,12.32c17.84,29.72,28,45,33.93,52.22,7.64,9.26,13,12,19.94,12,17.63,0,22-16.2,22-34.74l27.4-.86c0,19.38-3.82,33.62-10.32,44.87C271,180.13,258.72,191,238.13,191c-12.8,0-24.14-2.78-36.68-14.61-9.64-9.08-20.91-25.21-29.58-39.71L146.08,93.6c-12.94-21.62-24.81-37.74-31.68-45C107,40.71,97.51,31.23,82.35,31.23c-12.27,0-22.69,8.61-31.41,21.78Z"/><path class="cls-3" d="M82.35,31.23c-12.27,0-22.69,8.61-31.41,21.78C38.61,71.62,31.06,99.34,31.06,126c0,11,2.41,19.41,5.56,24.51L10.14,167.91C3.34,156.6,0,141.76,0,124.85,0,94.1,8.44,62.05,24.49,37.3,38.73,15.35,59.28,0,82.85,0Z"/></svg>';
  public static readonly OPENAI_SVG = `<?xml version="1.0" encoding="UTF-8"?>
  <svg width="256px" height="260px" viewBox="0 0 256 260" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" preserveAspectRatio="xMidYMid">
      <title>OpenAI</title>
      <g>
          <path d="M239.183914,106.202783 C245.054304,88.5242096 243.02228,69.1733805 233.607599,53.0998864 C219.451678,28.4588021 190.999703,15.7836129 163.213007,21.739505 C147.554077,4.32145883 123.794909,-3.42398554 100.87901,1.41873898 C77.9631105,6.26146349 59.3690093,22.9572536 52.0959621,45.2214219 C33.8436494,48.9644867 18.0901721,60.392749 8.86672513,76.5818033 C-5.443491,101.182962 -2.19544431,132.215255 16.8986662,153.320094 C11.0060865,170.990656 13.0197283,190.343991 22.4238231,206.422991 C36.5975553,231.072344 65.0680342,243.746566 92.8695738,237.783372 C105.235639,251.708249 123.001113,259.630942 141.623968,259.52692 C170.105359,259.552169 195.337611,241.165718 204.037777,214.045661 C222.28734,210.296356 238.038489,198.869783 247.267014,182.68528 C261.404453,158.127515 258.142494,127.262775 239.183914,106.202783 L239.183914,106.202783 Z M141.623968,242.541207 C130.255682,242.559177 119.243876,238.574642 110.519381,231.286197 L112.054146,230.416496 L163.724595,200.590881 C166.340648,199.056444 167.954321,196.256818 167.970781,193.224005 L167.970781,120.373788 L189.815614,133.010026 C190.034132,133.121423 190.186235,133.330564 190.224885,133.572774 L190.224885,193.940229 C190.168603,220.758427 168.442166,242.484864 141.623968,242.541207 Z M37.1575749,197.93062 C31.456498,188.086359 29.4094818,176.546984 31.3766237,165.342426 L32.9113895,166.263285 L84.6329973,196.088901 C87.2389349,197.618207 90.4682717,197.618207 93.0742093,196.088901 L156.255402,159.663793 L156.255402,184.885111 C156.243557,185.149771 156.111725,185.394602 155.89729,185.550176 L103.561776,215.733903 C80.3054953,229.131632 50.5924954,221.165435 37.1575749,197.93062 Z M23.5493181,85.3811273 C29.2899861,75.4733097 38.3511911,67.9162648 49.1287482,64.0478825 L49.1287482,125.438515 C49.0891492,128.459425 50.6965386,131.262556 53.3237748,132.754232 L116.198014,169.025864 L94.3531808,181.662102 C94.1132325,181.789434 93.8257461,181.789434 93.5857979,181.662102 L41.3526015,151.529534 C18.1419426,138.076098 10.1817681,108.385562 23.5493181,85.125333 L23.5493181,85.3811273 Z M203.0146,127.075598 L139.935725,90.4458545 L161.7294,77.8607748 C161.969348,77.7334434 162.256834,77.7334434 162.496783,77.8607748 L214.729979,108.044502 C231.032329,117.451747 240.437294,135.426109 238.871504,154.182739 C237.305714,172.939368 225.050719,189.105572 207.414262,195.67963 L207.414262,134.288998 C207.322521,131.276867 205.650697,128.535853 203.0146,127.075598 Z M224.757116,94.3850867 L223.22235,93.4642272 L171.60306,63.3828173 C168.981293,61.8443751 165.732456,61.8443751 163.110689,63.3828173 L99.9806554,99.8079259 L99.9806554,74.5866077 C99.9533004,74.3254088 100.071095,74.0701869 100.287609,73.9215426 L152.520805,43.7889738 C168.863098,34.3743518 189.174256,35.2529043 204.642579,46.0434841 C220.110903,56.8340638 227.949269,75.5923959 224.757116,94.1804513 L224.757116,94.3850867 Z M88.0606409,139.097931 L66.2158076,126.512851 C65.9950399,126.379091 65.8450965,126.154176 65.8065367,125.898945 L65.8065367,65.684966 C65.8314495,46.8285367 76.7500605,29.6846032 93.8270852,21.6883055 C110.90411,13.6920079 131.063833,16.2835462 145.5632,28.338998 L144.028434,29.2086986 L92.3579852,59.0343142 C89.7419327,60.5687513 88.1282597,63.3683767 88.1117998,66.4011901 L88.0606409,139.097931 Z M99.9294965,113.5185 L128.06687,97.3011417 L156.255402,113.5185 L156.255402,145.953218 L128.169187,162.170577 L99.9806554,145.953218 L99.9294965,113.5185 Z" fill="currentColor"></path>
      </g>
  </svg>
  `;
  public static readonly CHECK_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-check"><polyline points="20 6 9 17 4 12"/></svg>`;
  public static readonly CLOUD_SVG =
    '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-cloud"><path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/></svg>';
  public static readonly LAPTOP_SVG =
    '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-laptop"><path d="M20 16V7a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v9m16 0H4m16 0 1.28 2.55a1 1 0 0 1-.9 1.45H3.62a1 1 0 0 1-.9-1.45L4 16"/></svg>';
  public static readonly DOWNLOAD_SVG =
    '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-download"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/></svg>';
  public static readonly PLUG_SVG =
    '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-plug"><path d="M12 22v-5"/><path d="M9 8V2"/><path d="M15 8V2"/><path d="M18 8v5a4 4 0 0 1-4 4h-4a4 4 0 0 1-4-4V8Z"/></svg>';
  public static readonly PALM2_SVG = `<svg version="1.1" id="Standard_product_icon__x28_1:1_x29_"
    xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px" width="192px" height="192px"
    viewBox="0 0 192 192" enable-background="new 0 0 192 192" xml:space="preserve">
  <symbol  id="material_x5F_product_x5F_standard_x5F_icon_x5F_keylines_00000077318920148093339210000006245950728745084294_" viewBox="-96 -96 192 192">
   <g opacity="0.4">
     <defs>
       <path id="SVGID_1_" opacity="0.4" d="M-96,96V-96H96V96H-96z"/>
     </defs>
     <clipPath id="SVGID_00000071517564283228984050000017848131202901217410_">
       <use xlink:href="#SVGID_1_"  overflow="visible"/>
     </clipPath>
     <g clip-path="url(#SVGID_00000071517564283228984050000017848131202901217410_)">
       <g>
         <path d="M95.75,95.75v-191.5h-191.5v191.5H95.75 M96,96H-96V-96H96V96L96,96z"/>
       </g>
       <circle fill="none" stroke="#000000" stroke-width="0.25" stroke-miterlimit="10" cx="0" cy="0" r="64"/>
     </g>
     
       <circle clip-path="url(#SVGID_00000071517564283228984050000017848131202901217410_)" fill="none" stroke="#000000" stroke-width="0.25" stroke-miterlimit="10" cx="0" cy="0" r="88"/>
     
       <path clip-path="url(#SVGID_00000071517564283228984050000017848131202901217410_)" fill="none" stroke="#000000" stroke-width="0.25" stroke-miterlimit="10" d="
       M64,76H-64c-6.6,0-12-5.4-12-12V-64c0-6.6,5.4-12,12-12H64c6.6,0,12,5.4,12,12V64C76,70.6,70.6,76,64,76z"/>
     
       <path clip-path="url(#SVGID_00000071517564283228984050000017848131202901217410_)" fill="none" stroke="#000000" stroke-width="0.25" stroke-miterlimit="10" d="
       M52,88H-52c-6.6,0-12-5.4-12-12V-76c0-6.6,5.4-12,12-12H52c6.6,0,12,5.4,12,12V76C64,82.6,58.6,88,52,88z"/>
     
       <path clip-path="url(#SVGID_00000071517564283228984050000017848131202901217410_)" fill="none" stroke="#000000" stroke-width="0.25" stroke-miterlimit="10" d="
       M76,64H-76c-6.6,0-12-5.4-12-12V-52c0-6.6,5.4-12,12-12H76c6.6,0,12,5.4,12,12V52C88,58.6,82.6,64,76,64z"/>
   </g>
  </symbol>
  <rect id="bounding_box_1_" display="none" fill="none" width="192" height="192"/>
  <g id="art_layer">
   <g>
     <path fill="#F9AB00" d="M96,181.92L96,181.92c6.63,0,12-5.37,12-12v-104H84v104C84,176.55,89.37,181.92,96,181.92z"/>
     <g>
       <path fill="#5BB974" d="M143.81,103.87C130.87,90.94,111.54,88.32,96,96l51.37,51.37c2.12,2.12,5.77,1.28,6.67-1.57
         C158.56,131.49,155.15,115.22,143.81,103.87z"/>
     </g>
     <g>
       <path fill="#129EAF" d="M48.19,103.87C61.13,90.94,80.46,88.32,96,96l-51.37,51.37c-2.12,2.12-5.77,1.28-6.67-1.57
         C33.44,131.49,36.85,115.22,48.19,103.87z"/>
     </g>
     <g>
       <path fill="#AF5CF7" d="M140,64c-20.44,0-37.79,13.4-44,32h81.24c3.33,0,5.55-3.52,4.04-6.49C173.56,74.36,157.98,64,140,64z"/>
     </g>
     <g>
       <path fill="#FF8BCB" d="M104.49,42.26C90.03,56.72,87.24,78.45,96,96l57.45-57.45c2.36-2.36,1.44-6.42-1.73-7.45
         C135.54,25.85,117.2,29.55,104.49,42.26z"/>
     </g>
     <g>
       <path fill="#FA7B17" d="M87.51,42.26C101.97,56.72,104.76,78.45,96,96L38.55,38.55c-2.36-2.36-1.44-6.42,1.73-7.45
         C56.46,25.85,74.8,29.55,87.51,42.26z"/>
     </g>
     <g>
       <g>
         <path fill="#4285F4" d="M52,64c20.44,0,37.79,13.4,44,32H14.76c-3.33,0-5.55-3.52-4.04-6.49C18.44,74.36,34.02,64,52,64z"/>
       </g>
     </g>
   </g>
  </g>
  <g id="keylines" display="none">
   
     <use xlink:href="#material_x5F_product_x5F_standard_x5F_icon_x5F_keylines_00000077318920148093339210000006245950728745084294_"  width="192" height="192" id="material_x5F_product_x5F_standard_x5F_icon_x5F_keylines" x="-96" y="-96" transform="matrix(1 0 0 -1 96 96)" display="inline" overflow="visible"/>
  </g>
  </svg>
  `;

  /*
        ----------------
        |   Views   |
        ----------------
        View types for different views
    */
  public static readonly PIECES_ONBOARDING_VIEW_TYPE = 'pieces-onboarding';
  public static readonly PIECES_EXPANDED_MATERIAL_VIEW_TYPE =
    'pieces-expanded-material';
  public static readonly PIECES_MATERIAL_LIST_VIEW_TYPE =
    'pieces-material-list';

  /*
        ----------------
        |   SETTINGS   |
        ----------------
        Front end text within the Pieces plugin settings tab
    */
  public static readonly SETTINGS_KEY = 'jupyter_pieces:storage';
  public static readonly CLOUD_SELECT = 'Cloud Capabilities';
  public static readonly CLOUD_SELECT_DESC =
    "Select if you'd like to utilize cloud only, local only, or a blend of both.";
  public static readonly PORT_PROMPT = 'Pieces server port:';
  public static readonly PORT_DESCRIPTION = "Pieces' default port is 1000.";
  public static readonly SHOW_TUTORIAL = 'Show Plugin Usage Tutorials';
  public static readonly LOGIN_TITLE = 'Sign in';
  public static readonly LOGIN_DESC =
    'Start generating shareable links for your code materials';
  public static readonly LOGOUT_TITLE = 'Logout';
  public static readonly LOGOUT_DESC =
    'You will no longer have the ability to generate shareable links or share via GitHub Gist.';
  public static readonly TOGGLE_AUTOOPEN =
    'Auto-Open Pieces List on Material Save';
  public static readonly TOGGLE_AUTOOPEN_DESC =
    'Automatically open the Pieces material list view when saving a material.';
  public static readonly TOGGLE_AUTODISCOVER =
    'Auto-Discover materials from your vault';
  public static readonly TOGGLE_AUTODISCOVER_DESC =
    'Automatically discover materials from your vault when opening Pieces.';

  /*
      ---------------------
      |   SAVE MATERIALS   |
      ---------------------
      notification text for saving a piece
    */
  public static readonly NO_SAVE_SELECTION =
    'Make sure you select some text before you save a material';
  public static readonly NO_SELECTION_SAVE =
    'Make sure to select some materials before you try to save';
  public static readonly SAVE_SUCCESS = 'Success saving to Pieces';
  public static readonly SAVE_FAIL = 'Failed Saving to Pieces';
  public static readonly SAVE_EXISTS = 'Material already exists in Pieces';
  public static readonly NO_ACTIVE_CELL = 'No active cell found';
  public static readonly NO_CODE_CELL = 'No active code cell found';

  /*
        ------------------------
        |   SIGNIN / SIGNOUT   |
        ------------------------
        notification text for Pieces login / logout
    */
  public static readonly SIGNIN_SUCCESS = 'Successfully signed in!';
  public static readonly SIGNIN_FAIL = 'Unable to sign in.';
  public static readonly SIGNOUT_SUCCESS = 'Successfully signed out.';
  public static readonly SIGNOUT_FAIL = 'Unable to sign out.';
  public static readonly CONNECTION_FAIL =
    'Failed to connect to PiecesOS. Please check that PiecesOS is installed and running.';

  /*
        ----------------------
        |   MATERIAL DELETE   |
        ----------------------
        notification text for material deletions
    */
  public static readonly MATERIAL_DELETE_SUCCESS =
    'Your Material Was Successfully Deleted!';
  public static readonly MATERIAL_IS_DELETED =
    'Material has already been deleted.';
  public static readonly MATERIAL_DELETE_FAILURE =
    'Failed to delete material. Please ensure that PiecesOS is up-to-date, installed and running. If the problem persists please reach out to support at support.';

  /*
        ---------------------------------
        |  CLOUD CONNECT / DISCONNECT   |
        ---------------------------------
        notification text for cloud handling
    */
  public static readonly LOGIN_TO_POS_CLOUD =
    'Please sign into PiecesOS in order to connect to Pieces cloud.';
  public static readonly CLOUD_CONNECT_FAIL =
    'Unable to connect to Pieces cloud, please wait a minute an try again.';
  public static readonly CLOUD_CONNECT_SUCCESS =
    'Successfully connected to Pieces cloud.';
  public static readonly CLOUD_CONNECT_INPROG =
    'Pieces cloud is still connecting please try again later.';
  public static readonly CLOUD_DISCONNECT_ALR =
    'Already disconnected from Pieces cloud.';
  public static readonly CLOUD_DISCONNECT_SUCCESS =
    'Successfully disconnected from Pieces cloud.';
  public static readonly CLOUD_DISCONNECT_FAIL =
    'Failed to disconnect from Pieces cloud, please try again.';
  public static readonly CORE_PLATFORM_MSG =
    'Pieces for Developers ⎸ Core Platform runs offline and on-device to power our IDE and Browser extensions.';
  public static readonly LOGIN_TO_POS = 'Please sign into PiecesOS';
  public static readonly LINK_GEN_SUCCESS = 'Shareable Link Generated!';
  public static readonly LINK_GEN_COPY = 'Shareable link copied to clipboard!';
  public static readonly LINK_GEN_FAIL =
    'Failed to generate link. Please ensure that PiecesOS is up-to-date, installed and running. If the problem persists please reach out to support.';

  /*
        -----------------------
        |   SEARCH MATERIALS   |
        -----------------------
    */
  public static readonly SEARCH_SUCCESS = 'Material search success!';
  public static readonly SEARCH_FAILURE =
    'Something went wrong while searching for your materials, if the issue persists please reach out to support.';

  /*
        -----------------------------------
        |   TEXT FOR POS DOWNLOAD MODAL   |
        -----------------------------------
        This is shown in the 'download-pos-modal'
        if we are not able to contact POS on their machine
    */
  public static readonly INSTALL_TEXT =
    'Please download, install, and run our core dependency to use Pieces for Jupyter lab:';
  public static readonly PIECES_ONDEVICE_COPY =
    'Pieces for Developers | Core Platform runs offline and on-device to power our IDE and Browser Extensions';

  /*
    -----------------------------------
    |   TEXT FOR ExpandView Problem   |
    -----------------------------------
    This is shown in the 'general text view'
    if we are not able to expand their material
    */
  public static readonly EXPAND_ERROR =
    'Error expanding material, check the `Material ID` and try again.';

  /*
        ------------------------------
        |   TEXT FOR WELCOME MODAL   |
        ------------------------------
        This is shown within 'onboarding-modal'
        if it is the first time the user is loading the extension
    */

  public static readonly WELCOME_TEXT = 'Welcome to Pieces for Developers!';
  public static readonly SAVE_INSERT_SEARCH =
    'Save, insert, and search your materials.';

  // Saving materials
  public static readonly SAVE_MATERIAL = 'Save a material';
  public static readonly SAVE_EXPLANATION =
    'Select the material you would like to save to Pieces, right click, and click the "Save to Pieces" button';
  public static readonly SAVE_SHORTCUT_EX =
    'Or you can use the keyboard shortcut: MOD + SHIFT + P';

  // Viewing Materials
  public static readonly VIEW_MATERIALS = 'Viewing your Materials';
  public static readonly VIEW_MATERIAL_EXPLANATION =
    'In order to view your saved materials, just click on the "Pieces" icon on your ribbon bar.';

  // Inserting Materials
  public static readonly INSERT_MATERIAL = 'Insert a material';
  public static readonly INSERT_MATERIAL_EXPLANATION =
    'In order to insert a material, navigate to the material in your Pieces Drive, click the "copy material" button, and paste it into your editor';

  // Searching Materials
  public static readonly SEARCH_MATERIAL = 'Search for a Material';
  public static readonly SEARCH_MATERIAL_EXPLANATION =
    'To search for a material, navigate to the material in your Pieces Drive, and type your query into the search box. Once you are done, click the "X" and it will clear your search.';

  /*
		|------------------|
		|	UPDATE ASSET   |
		|------------------|
	*/
  public static readonly RECLASSIFY_SUCCESS =
    'Material Successfully Reclassified';
  public static readonly RECLASSIFY_FAILURE =
    'Error Reclassifying material, please try again... or contact support.';
  public static readonly UPDATE_SUCCESS = 'Material successfully updated';
  public static readonly UPDATE_FAILURE =
    'Error updating material, please try again... or contact support.';
  public static readonly UPDATE_CODE_SUCCESS = 'Material successfully updated';
  public static readonly UPDATE_CODE_FAILURE =
    'Error updating material, please try again... or contact support.';

  /*
		|------------------|
		|	COPY TO CLIP   |
		|------------------|
	*/

  public static readonly COPY_SUCCESS = 'Material copied to clipboard';

  /*
        |--------------------|
        | MATERIAL DISCOVERY  |
        |--------------------|
    */

  public static readonly DISCOVERY_SUCCESS = 'Material Discovery Complete!';
  public static readonly DISCOVERY_FAILURE =
    'Something went wrong with Material Discovery, are you sure PiecesOS is installed, running, and up to date?';
}
