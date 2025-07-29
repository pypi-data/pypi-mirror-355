import { jsonPost } from "./util.js";

const downloadUrl = /** @type {HTMLInputElement} */ (document.getElementById('download-url'));
const downloadPlaylist = /** @type {HTMLSelectElement} */ (document.getElementById('download-playlist'));
const downloadButton = /** @type {HTMLButtonElement} */ (document.getElementById('download-button'));
const downloadLoading = /** @type {HTMLDivElement} */ (document.getElementById('download-loading'));
const downloadLog = /** @type {HTMLTextAreaElement} */ (document.getElementById('download-log'));

downloadButton.addEventListener('click', async () => {
    downloadButton.hidden = true;
    downloadLoading.hidden = false;

    downloadLog.style.backgroundColor = '';
    downloadLog.textContent = '';

    const decoder = new TextDecoder();

    function handleResponse(result) {
        downloadLog.textContent += decoder.decode(result.value);
        downloadLog.scrollTop = downloadLog.scrollHeight;
        return result
    }

    try {
        const response = await jsonPost('/download/ytdl', {directory: downloadPlaylist.value, url: downloadUrl.value});
        if (response.body == null) throw new Error();
        const reader = response.body.getReader();
        let result;
        while (!(result = await reader.read()).done) {
            await handleResponse(result);
        }
    } finally {
        downloadButton.hidden = false;
        downloadLoading.hidden = true;
    }
});
