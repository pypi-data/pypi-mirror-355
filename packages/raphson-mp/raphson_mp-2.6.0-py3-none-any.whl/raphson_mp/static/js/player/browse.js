import { eventBus, MusicEvent } from "./event.js";
import { vars, createIconButton, replaceIconButton, durationToString } from "../util.js";
import { windows } from "./window.js";
import { music, Track } from "../api.js";
import { trackDisplayHtml } from "./track.js";
import { editor } from "./editor.js";
import { settings } from "./settings.js";
import { queue } from "./queue.js";

class BrowseHistoryEntry {
    /** @type {string} */
    title;
    /** @type {object} */
    filters;
    /**
     * @param {string} title
     * @param {object} filters
     */
    constructor(title, filters) {
        this.title = title;
        this.filters = filters;
    }
}

class Browse {
    /** @type {Array<BrowseHistoryEntry>} */
    #history = [];
    #playlistElem = /** @type {HTMLSelectElement} */ (document.getElementById('browse-playlist'));
    #allButton = /** @type {HTMLButtonElement} */ (document.getElementById('browse-all'));
    #backButton = /** @type {HTMLButtonElement} */ (document.getElementById('browse-back'));
    #bottomButton = /** @type {HTMLButtonElement} */ (document.getElementById('browse-bottom'));
    #recentlyAddedButton = /** @type {HTMLButtonElement} */ (document.getElementById("browse-recently-added"));
    #recentlyReleasedButton = /** @type {HTMLButtonElement} */ (document.getElementById("browse-recently-released"));
    #randomButton = /** @type {HTMLButtonElement} */ (document.getElementById("browse-random"));
    #missingMetadataButton = /** @type {HTMLButtonElement} */ (document.getElementById("browse-missing-metadata"));
    #tableElem = /** @type {HTMLTableElement} */ (document.getElementById('browse-table'));
    #noContentElem = /** @type {HTMLParagraphElement} */ (document.getElementById('browse-no-content'));
    #loadingElem = /** @type {HTMLDivElement} */ (document.getElementById('browse-loading'));

    constructor() {
        // Playlist dropdown
        this.#playlistElem.addEventListener('input', () => {
            console.debug('browse: filter-playlist input trigger');
            const playlist = this.#playlistElem.value;
            const current = browse.current();
            // browse again, but with a changed playlist filter
            const newFilter = { ...current.filters };
            if (playlist == 'all') {
                delete newFilter.playlist;
            } else {
                newFilter.playlist = playlist;
            }
            browse.browse(current.title, newFilter);
        });

        // Button to open browse window
        this.#allButton.addEventListener('click', () => browse.browseNothing());

        // Back button in top left corner of browse window
        this.#backButton.addEventListener('click', () => browse.back());

        // Button to jump to bottom
        const scroll = /** @type {HTMLElement} */ (document.getElementById("browse-scroll"));
        this.#bottomButton.addEventListener("click", () => {
            scroll.scrollTo(0, scroll.scrollHeight);
        });

        // Browse discover buttons
        this.#recentlyAddedButton.addEventListener("click", () => browse.browseRecentlyAdded());
        this.#recentlyReleasedButton.addEventListener("click", () => browse.browseRecentlyReleased());
        this.#randomButton.addEventListener("click", () => browse.browseRandom());
        this.#missingMetadataButton.addEventListener("click", () => browse.browseMissingMetadata());

        eventBus.subscribe(MusicEvent.METADATA_CHANGE, () => {
            if (!windows.isOpen('window-browse')) {
                console.debug('browse: ignore METADATA_CHANGE, browse window is not open. Is editor open: ', windows.isOpen('window-editor'));
                return;
            }

            console.debug('browse: received METADATA_CHANGE, updating content');
            this.updateContent();
        });
    };

    /**
     * @returns {BrowseHistoryEntry}
     */
    current() {
        if (this.#history.length === 0) {
            throw new Error();
        }

        return this.#history[this.#history.length - 1];
    }

    /**
     * @param {string} textContent
     */
    setHeader(textContent) {
        const browseWindow = /** @type {HTMLDivElement} */ (document.getElementById('window-browse'));
        browseWindow.getElementsByTagName('h2')[0].textContent = textContent;
    };

    /**
     * @param {string} title
     * @param {object} filters
     */
    browse(title, filters) {
        windows.open('window-browse');
        if (!filters.playlist) {
            this.#playlistElem.value = 'all';
        }
        this.#history.push(new BrowseHistoryEntry(title, filters));
        this.updateContent();
    };

    back() {
        if (this.#history.length < 2) {
            return;
        }
        this.#history.pop();
        this.updateContent();
    };

    async updateContent() {
        // Remove previous content, while new content is loading
        this.#tableElem.replaceChildren();
        this.#loadingElem.hidden = false;
        this.#noContentElem.hidden = true;

        const current = this.current();
        this.setHeader(current.title);

        // update playlist dropdown from current filter
        if (current.filters.playlist) {
            this.#playlistElem.value = current.filters.playlist;
        } else {
            this.#playlistElem.value = 'all';
        }

        console.info('browse:', current);

        if (Object.keys(current.filters).length == 0) {
            this.#noContentElem.hidden = false;
            this.#loadingElem.hidden = true;
            return;
        }

        await music.filterPages(current.filters, async tracks => {
            this.#loadingElem.hidden = true;
            await this.appendTrackRows(this.#tableElem, tracks);
        });
    }

    /**
     * @param {string} artistName
     */
    browseArtist(artistName) {
        this.browse(vars.tBrowseArtist + artistName, { 'artist': artistName, 'order': 'title' });
    };

    /**
     * @param {string} albumName
     * @param {string|null} albumArtistName
     */
    browseAlbum(albumName, albumArtistName) {
        const title = vars.tBrowseAlbum + (albumArtistName === null ? '' : albumArtistName + ' - ') + albumName;
        const filters = { 'album': albumName };
        if (albumArtistName) {
            filters.album_artist = albumArtistName;
        }
        this.browse(title, filters);
    };

    /**
     * @param {string} tagName
     */
    browseTag(tagName) {
        this.browse(vars.tBrowseTag + tagName, { 'tag': tagName });
    };

    /**
     * @param {string} playlistName
     */
    browsePlaylist(playlistName) {
        this.browse(vars.tBrowsePlaylist + playlistName, { playlist: playlistName });
    };

    /**
     * @param {number} year
     */
    browseYear(year) {
        this.browse(vars.tBrowseYear + year, { year: year });
    }

    browseRecentlyAdded() {
        this.browse(vars.tBrowseRecentlyAdded, { order: "ctime", limit: 100 });
    }

    browseRecentlyReleased() {
        this.browse(vars.tBrowseRecentlyReleased, { order: "year", limit: 100 });
    }

    browseRandom() {
        this.browse(vars.tBrowseRandom, { order: "random", limit: 100 });
    }

    browseMissingMetadata() {
        this.browse(vars.tBrowseMissingMetadata, { has_metadata: "0", order: "random", limit: 100 });
    }

    browseNothing() {
        this.browse(vars.tBrowseNothing, {});
    };

    /**
     * also used by search.js
     * @param {HTMLTableElement} table
     * @param {Array<Track>} tracks
     */
    async appendTrackRows(table, tracks) {
        const addButton = createIconButton('playlist-plus');
        const editButton = createIconButton('pencil');
        const rows = [];
        for (const track of tracks) {
            const colPlaylist = document.createElement('td');
            colPlaylist.textContent = track.playlistName;

            const colDuration = document.createElement('td');
            colDuration.textContent = durationToString(track.duration);

            const colTitle = document.createElement('td');
            colTitle.appendChild(trackDisplayHtml(track));

            const addButton2 = /** @type {HTMLButtonElement} */ (addButton.cloneNode(true));
            addButton2.addEventListener('click', async () => {
                replaceIconButton(addButton2, 'loading');
                addButton2.disabled = true;

                try {
                    const downloadedTrack = await track.download(...settings.getTrackDownloadParams());
                    queue.add(downloadedTrack, true);
                } catch (ex) {
                    console.error('browse: error adding track to queue', ex);
                }

                replaceIconButton(addButton2, 'playlist-plus');
                addButton2.disabled = false;
            });
            const colAdd = document.createElement('td');
            colAdd.appendChild(addButton2);
            colAdd.style.width = '2rem';

            const colEdit = document.createElement('td');
            colEdit.style.width = '2rem';

            if ((await music.playlist(track.playlistName)).write) {
                const editButton2 = editButton.cloneNode(true);
                editButton2.addEventListener('click', () => editor.open(track));
                colEdit.appendChild(editButton2);
            }

            const row = document.createElement('tr');
            row.append(colPlaylist, colDuration, colTitle, colAdd, colEdit);
            rows.push(row);
        }
        table.append(...rows);
    }
};

export const browse = new Browse();
