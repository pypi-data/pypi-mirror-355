import { music, Playlist } from "./api.js";
import { uuidv4 } from "./util.js";

export class PlaylistCheckboxes {
    #parentElement;
    #changeCallback;

    /**
     *
     * @param {HTMLDivElement} parentElement
     * @param {() => void} changeCallback Function called when playlists change
     */
    constructor(parentElement, changeCallback) {
        this.#parentElement = parentElement;
        this.#changeCallback = changeCallback;

        document.addEventListener("keydown", event => {
            const keyInt = parseInt(event.key);
            if (isNaN(keyInt) || keyInt == 0) {
                return;
            }

            console.debug('playlistcheckboxes: toggle playlist', keyInt);

            const checkboxes = parentElement.getElementsByTagName('div')[0].getElementsByTagName('input');
            if (keyInt <= checkboxes.length) {
                // Toggle checkbox
                checkboxes[keyInt - 1].checked = !checkboxes[keyInt - 1].checked;
            }
            this.#changeCallback();
            this.#savePlaylistState();
        });
    }

    /**
     * Update checked state of playlist checkboxes from local storage
     * @returns {void}
     */
    #loadPlaylistState() {
        const playlistsString = localStorage.getItem('playlists');
        if (!playlistsString) {
            console.info('playlist: no state saved');
            this.#changeCallback();
            return;
        }
        /** @type {Array<string>} */
        const savedPlaylists = JSON.parse(playlistsString);
        console.debug('playlist: restoring state', savedPlaylists);
        const checkboxes = this.#parentElement.getElementsByTagName('input');
        for (const checkbox of checkboxes) {
            const playlist = checkbox.dataset.playlist;
            if (!playlist) throw new Error();
            checkbox.checked = savedPlaylists.indexOf(playlist) != -1;
        }
        this.#changeCallback();
    }

    /**
     * Save state of playlist checkboxes to local storage
     * @returns {void}
     */
    #savePlaylistState() {
        const checkboxes = this.#parentElement.getElementsByTagName('input');
        const checkedPlaylists = [];
        for (const checkbox of checkboxes) {
            if (checkbox.checked) {
                checkedPlaylists.push(checkbox.dataset.playlist);
            }
        }
        console.debug('playlist: saving checkbox state', checkedPlaylists);
        localStorage.setItem('playlists', JSON.stringify(checkedPlaylists));
    }

    /**
     * @param {Playlist} playlist Playlist
     * @param {number} index Hotkey number, set to >=10 to not assign a hotkey
     * @param {boolean} defaultChecked Whether checkbox should be checked
     * @returns {HTMLSpanElement}
     */
    #createPlaylistCheckbox(playlist, index, defaultChecked) {
        const input = document.createElement("input");
        input.type = 'checkbox';
        input.dataset.playlist = playlist.name;
        input.id = uuidv4();
        input.checked = defaultChecked;

        const sup = document.createElement('sup');
        if (index < 10) { // Assume number keys higher than 9 don't exist
            sup.textContent = index + '';
        }

        const trackCount = document.createElement('span');
        trackCount.classList.add('secondary');
        trackCount.textContent = ' ' + playlist.trackCount;

        const label = document.createElement("label");
        label.htmlFor = input.id;
        label.textContent = playlist.name;
        label.replaceChildren(playlist.name, sup, trackCount);

        // Checkbox and label must always be together
        const span = document.createElement("div");
        span.replaceChildren(input, label);

        return span;
    }

    async createPlaylistCheckboxes() {
        const mainDiv = document.createElement('div');
        const otherDiv = document.createElement('div');
        mainDiv.classList.add('playlist-checkbox-row');
        otherDiv.classList.add('playlist-checkbox-row');

        let index = 1;
        for (const playlist of await music.playlists()) {
            if (playlist.trackCount == 0) {
                continue;
            }

            if (playlist.favorite) {
                mainDiv.appendChild(this.#createPlaylistCheckbox(playlist, index++, true));
            } else {
                otherDiv.appendChild(this.#createPlaylistCheckbox(playlist, 10, false));
            }
        }

        this.#parentElement.replaceChildren(mainDiv, otherDiv);

        for (const input of this.#parentElement.getElementsByTagName('input')) {
            input.addEventListener('input', () => {
                this.#changeCallback();
                this.#savePlaylistState();
            });
        }

        // load checked/unchecked state from local storage
        this.#loadPlaylistState();
    }
}
