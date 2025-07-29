import { eventBus, MusicEvent } from "./event.js";

const SETTING_ELEMENTS = [
    'settings-queue-size',
    'settings-audio-type',
    'settings-volume',
    'settings-queue-removal-behaviour',
    'settings-download-mode',
    'settings-audio-gain',
    'settings-meme-mode',
    'settings-news',
    'settings-theater',
    'settings-visualiser',
    'settings-lyrics',
];

class Settings {
    constructor() {
        SETTING_ELEMENTS.forEach(elem => this.#syncInputWithStorage(elem));
        setTimeout(() => {
            eventBus.publish(MusicEvent.SETTINGS_LOADED);
        }, 0); // publish slightly later, so other code can subscribe to the event first
    }

    /**
     * @param {string} elemId
     * @returns {void}
     */
    #syncInputWithStorage(elemId) {
        const elem = /** @type {HTMLInputElement | HTMLSelectElement} */ (document.getElementById(elemId));
        const isCheckbox = elem instanceof HTMLInputElement && elem.matches('input[type="checkbox"]');

        if (elem.dataset.restore === 'false') {
            return;
        }

        // Initialize input form local storage
        const value = window.localStorage.getItem(elemId);
        if (value !== null) {
            if (isCheckbox) {
                const checked = value === 'true';
                if (elem.checked != checked) {
                    elem.checked = checked;
                }
            } else if (elem.value != value) {
                elem.value = value;
            }
        }

        // If input value is updated, change storage accordingly
        elem.addEventListener('change', () => {
            const value = isCheckbox ? elem.checked + '' : elem.value;
            window.localStorage.setItem(elemId, value);
        });
    }

    getTrackDownloadParams() {
        const audioTypeElem = /** @type {HTMLInputElement} */ (document.getElementById('settings-audio-type'));
        const downloadModeInput = /** @type {HTMLInputElement} */ (document.getElementById('settings-download-mode'));
        const stream = downloadModeInput.value == 'stream';
        const memeModeInput = /** @type {HTMLInputElement} */ (document.getElementById('settings-meme-mode'));
        const memeCover = memeModeInput.checked;
        return /** @type {[string, boolean, boolean]} */ ([audioTypeElem.value, stream, memeCover]);
    }
}

export const settings = new Settings();
