import { vars, createToast } from "../util.js";
import { eventBus, MusicEvent } from "./event.js"

class Theater {
    #htmlSetting = /** @type {HTMLInputElement} */ (document.getElementById("settings-theater"));
    #htmlBody = document.getElementsByTagName('body')[0];
    #stillCount = 0;
    /** @type {number | null} */
    #timerId = null;
    /** @type {(() => void) | null} */
    #listenerFunction = null;

    constructor() {
        this.#htmlSetting.addEventListener('change', () => this.#onSettingChange());
        eventBus.subscribe(MusicEvent.SETTINGS_LOADED, () => this.#onSettingChange());
    }

    toggle() {
        console.debug('theater: toggled setting');
        this.#htmlSetting.checked = !this.#htmlSetting.checked;
        this.#onSettingChange();
        if (this.#htmlSetting.checked) {
            createToast(vars.tTheaterModeEnabled);
        } else {
            createToast(vars.tTheaterModeDisabled);
        }
    }

    #checkStill() {
        console.debug('theater: timer', this.#stillCount);
        this.#stillCount++;

        if (this.#stillCount > 10) {
            this.#activate();
        }
    }

    #onMove() {
        // if stillCount is not higher than 10, theater mode was never activated
        if (this.#stillCount > 10) {
            this.#deactivate()
        }
        this.#stillCount = 0;
    }

    #onSettingChange() {
        if (this.#timerId) {
            console.debug('theater: unregistered timer');
            clearInterval(this.#timerId);
            this.#timerId = null;
        }

        if (this.#listenerFunction) {
            console.debug('theater: unregistered listener');
            document.removeEventListener('pointermove', this.#listenerFunction);
            this.#listenerFunction = null;
        }

        const theaterModeEnabled = this.#htmlSetting.checked;
        if (theaterModeEnabled) {
            console.debug('theater: registered timer and listener');
            this.#timerId = setInterval(() => this.#checkStill(), 1000);
            this.#listenerFunction = () => this.#onMove();
            document.addEventListener('pointermove', this.#listenerFunction);
            return;
        } else {
            this.#deactivate();
        }
    }

    #activate() {
        this.#htmlBody.classList.add('theater');
    }

    #deactivate() {
        this.#htmlBody.classList.remove('theater');
    }
}

export const theater = new Theater();
