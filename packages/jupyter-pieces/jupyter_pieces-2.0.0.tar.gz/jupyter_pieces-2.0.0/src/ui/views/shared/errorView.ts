import { Applet } from './applet';
import { createDiv, createEl } from './globals';
import getTheme from './theme';
import { DownloadState, POSDownloader } from './downloader';

export const showErrorView = (title: string, container: HTMLDivElement) => {
  const containerId = container.id;
  if (document.getElementById(`${containerId}-error-view`)) {
    return;
  }
  const errorViewContainer = createDiv(container);
  errorViewContainer.classList.add(
    'flex',
    'flex-col',
    'w-full',
    'h-full',
    'py-10',
    'px-4',
    'text-center',
    'text-[var(--pieces-text-muted)]',
    'justify-center'
  );
  errorViewContainer.id = `${containerId}-error-view`;

  const darkMode = getTheme().darkMode;

  const imgDiv = createDiv(errorViewContainer);
  imgDiv.classList.add('flex', 'justify-center');
  const img = createEl(imgDiv, 'div');
  img.classList.add(
    darkMode ? 'guy-asleep-dm' : 'guy-asleep-lm',
    'h-32',
    'w-32',
    'bg-contain',
    'bg-no-repeat'
  );

  const loadTxtContainer = createDiv(errorViewContainer);
  loadTxtContainer.classList.add('px-2', 'text-lg', 'font-bold');

  const loadTxtP = createEl(loadTxtContainer, 'p');
  loadTxtP.classList.add('m-0');
  loadTxtP.innerText = title;

  const expText = createDiv(errorViewContainer);
  expText.classList.add('pt-4', 'px-2', 'font-semibold', 'break-words');
  expText.innerHTML =
    'Please make sure that PiecesOS is running and up to date to use Pieces! If the issue persists, please ';

  const contactSupportBtn = createEl(expText, 'a');
  contactSupportBtn.classList.add('underline', 'cursor-pointer');
  contactSupportBtn.onclick = () => {
    window.open(
      'https://getpieces.typeform.com/to/mCjBSIjF#page=jupyter-plugin'
    );
  };
  contactSupportBtn.innerText = 'contact support';

  const launchBtnDiv = createDiv(errorViewContainer);
  launchBtnDiv.classList.add(
    'pt-4',
    'flex-row',
    'gap-2',
    'flex',
    'justify-center'
  );

  const launchBtn = createEl(launchBtnDiv, 'button');
  launchBtn.classList.add(
    'p-2',
    'rounded',
    'shadow-sm',
    'shadow-[var(--pieces-background-modifier-box-shadow)]',
    'w-fit',
    'cursor-pointer'
  );
  launchBtn.innerText = 'Launch';
  launchBtn.onclick = () => {
    Applet.launchPos();
  };

  const installBtn = createEl(launchBtnDiv, 'button');
  installBtn.classList.add(
    'p-2',
    'rounded',
    'shadow-sm',
    'shadow-[var(--pieces-background-modifier-box-shadow)]',
    'w-fit',
    'cursor-pointer'
  );

  const downloadDiv = createDiv(errorViewContainer);
  downloadDiv.classList.add(
    'pt-4',
    'flex-row',
    'gap-2',
    'flex',
    'justify-center',
    'items-center'
  );

  const successMsg = createEl(downloadDiv, 'p');
  successMsg.innerText =
    'Follow the installer instructions, then run PiecesOS to continue';
  successMsg.style.display = 'none';

  const cancelBtn = createEl(downloadDiv, 'button');

  cancelBtn.classList.add(
    'p-2',
    'rounded',
    'shadow-sm',
    'w-fit',
    'cursor-pointer'
  );
  cancelBtn.innerText = 'Cancel';
  cancelBtn.style.display = 'none';
  cancelBtn.style.cursor = 'pointer';

  const progressEl = createEl(downloadDiv, 'progress');
  progressEl.value = 0;
  progressEl.max = 100;
  progressEl.style.display = 'none';

  const cleanup = () => {
    progressEl.style.display = 'none';
    progressEl.value = 0;
    successMsg.style.display = 'none';
    cancelBtn.style.display = 'none';
    installBtn.disabled = false;
    installBtn.innerText = 'Install';
  };

  installBtn.innerText = 'Install';
  const downloader = new POSDownloader(
    (state) => {
      if (state === DownloadState.COMPLETED) {
        cleanup();
        successMsg.style.display = 'block'; // temporarily show
        installBtn.innerText = 'Download again?';
        if (process.platform === 'win32') {
          Applet.launchPos();
        }
      } else if (state === DownloadState.FAILED) {
        cleanup();
        installBtn.innerText = 'Download Failed (Retry)';
      }
    },
    (progress) => {
      progressEl.value = progress;
      installBtn.innerText = `Downloading ${progress.toFixed(0)}%`;
    }
  );

  installBtn.onclick = async () => {
    installBtn.innerText = 'Downloading...';
    installBtn.disabled = true;
    installBtn.disabled = true;
    cancelBtn.style.display = 'block';
    successMsg.style.display = 'none';

    cancelBtn.onclick = () => {
      downloader.cancel();
      cleanup();
    };

    downloader.connect();
  };
};
