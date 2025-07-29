import { eventBus, MusicEvent } from "./event.js";
import { choice, durationToString, vars, createToast } from "../util.js";
import { music, DownloadedTrack, Track } from "../api.js";
import { getTagFilter } from "./tag.js";
import { settings } from "./settings.js";
import { trackDisplayHtml } from "./track.js";
import { player } from "./player.js";

const MAX_HISTORY_SIZE = 3; // 3 tracks of 5 minutes at 128kbps = ~15MB

/**
 * @returns {Array<string>} list of playlist names
 */
function getActivePlaylists() {
    const playlistCheckboxes = /** @type {HTMLDivElement} */ (document.getElementById('playlist-checkboxes'));
    const active = [];
    for (const checkbox of playlistCheckboxes.getElementsByTagName('input')) {
        if (checkbox.checked) {
            active.push(/** @type {string} */(checkbox.dataset.playlist));
        }
    }

    return active;
}

/**
 * @param {string | null} currentPlaylist current playlist name
 * @returns {string | null} next playlist name
 */
function getNextPlaylist(currentPlaylist) {
    const active = getActivePlaylists();

    let playlist;

    if (active.length === 0) {
        // No one is selected
        console.warn('playlist: no playlists active');
        return null;
    } else if (currentPlaylist === null) {
        // No playlist chosen yet, choose random playlist
        playlist = choice(active);
    } else {
        const currentIndex = active.indexOf(currentPlaylist);
        if (currentIndex === -1) {
            // Current playlist is no longer active, we don't know the logical next playlist
            // Choose random playlist
            playlist = choice(active);
        } else {
            // Choose next playlist in list, wrapping around if at the end
            playlist = active[(currentIndex + 1) % active.length];
        }
    }

    return playlist;
}

class Queue {
    #htmlCurrentQueueSize = /** @type {HTMLSpanElement} */ (document.getElementById("current-queue-size"));
    #htmlMinimumQueueSize = /** @type {HTMLInputElement} */ (document.getElementById("settings-queue-size"));
    #htmlNoPlaylistsSelected = /** @type {HTMLSpanElement} */ (document.getElementById("no-playlists-selected"));
    #htmlQueueRemovalBehaviour = /** @type {HTMLSelectElement} */ (document.getElementById("settings-queue-removal-behaviour"));
    #htmlQueueTable = /** @type {HTMLTableElement} */ (document.getElementById("queue-table"));
    #previousPlaylist = /** @type {string|null} */ (null);
    #playlistOverrides = /** @type {Array<string>} */ ([]);
    #previousTracks = /** @type {Array<DownloadedTrack>} */ ([]);
    #manualQueuedTracks = /** @type {Array<DownloadedTrack>} */ ([]);
    #autoQueuedTracks = /** @type {Array<DownloadedTrack>} */ ([]);
    #queueChanged = true;
    currentTrack = /** @type {DownloadedTrack | null} */ (null);
    #filling = false;
    #fillDelay = 1000;

    constructor() {
        eventBus.subscribe(MusicEvent.METADATA_CHANGE, updatedTrack => {
            for (const downloadedTrack of [this.currentTrack, ...this.#previousTracks, ...this.#manualQueuedTracks, ...this.#autoQueuedTracks]) {
                if (downloadedTrack == null
                    || !(downloadedTrack.track instanceof Track)
                    || downloadedTrack.track.path != updatedTrack.path) {
                    continue;
                }

                console.debug('queue: updating track in queue following a METADATA_CHANGE event', updatedTrack.path);
                downloadedTrack.track = updatedTrack;
                this.#queueChanged = true;
            }

            this.updateHtml();
        });
    };

    /**
     * @returns {Array<DownloadedTrack>}
     */
    #combinedQueue() {
        return [...this.#manualQueuedTracks, ...this.#autoQueuedTracks];
    }

    /**
     * @returns {Number}
     */
    #combinedQueueLength() {
        return this.#manualQueuedTracks.length + this.#autoQueuedTracks.length;
    }

    /**
     * @param {Number} start
     * @param {Number} deleteCount
     * @param  {...DownloadedTrack} insertTracks
     * @returns {Array<DownloadedTrack>}
     */
    #combinedQueueSplice(start, deleteCount, ...insertTracks) {
        this.#queueChanged = true;
        if (start < this.#manualQueuedTracks.length) {
            return this.#manualQueuedTracks.splice(start, deleteCount, ...insertTracks);
        } else {
            return this.#autoQueuedTracks.splice(start - this.#manualQueuedTracks.length, deleteCount, ...insertTracks);
        }
    }

    /**
     * @returns {DownloadedTrack}
     */
    #combinedQueuePop() {
        this.#queueChanged = true;
        if (this.#manualQueuedTracks.length) {
            return /** @type {DownloadedTrack} */ (this.#manualQueuedTracks.shift());
        } else {
            return /** @type {DownloadedTrack} */ (this.#autoQueuedTracks.shift());
        }
    }

    /**
     * Add track to queue
     * @param {DownloadedTrack} downloadedTrack
     * @param {boolean} manual True to add track to the manual queue instead of auto queue (manual queue is played first)
     * @param {boolean} top True to add track to top of queue
     */
    add(downloadedTrack, manual, top = false) {
        const queue = (manual ? this.#manualQueuedTracks : this.#autoQueuedTracks);
        if (top) {
            queue.unshift(downloadedTrack);
        } else {
            queue.push(downloadedTrack);
        }
        this.#queueChanged = true;
        this.updateHtml();
    };

    /**
     * Remove all items from queue
     */
    clear(auto = true, manual = false) {
        if (auto) {
            this.#autoQueuedTracks.forEach(track => track.revokeObjects());
            this.#autoQueuedTracks = [];
        }

        if (manual) {
            this.#manualQueuedTracks.forEach(track => track.revokeObjects());
            this.#manualQueuedTracks = [];
        }

        if (auto || manual) {
            this.#queueChanged = true;
            this.fill();
        }
        createToast(vars.tQueueCleared);
    }

    /**
     * @returns {DownloadedTrack | null}
     */
    getPreviousTrack() {
        if (this.#previousTracks.length > 0) {
            return this.#previousTracks[this.#previousTracks.length - 1];
        } else {
            return null;
        }
    };

    #getMinimumSize() {
        let minQueueSize = parseInt(this.#htmlMinimumQueueSize.value);
        return isFinite(minQueueSize) ? minQueueSize : 1;
    }

    async fill() {
        console.debug('queue: fill');
        this.updateHtml();

        if (this.#autoQueuedTracks.length >= this.#getMinimumSize()) {
            console.debug('queue: full');
            return;
        }

        if (this.#filling) {
            console.debug('queue: already filling');
            return;
        }

        try {
            this.#filling = true;

            let playlist;

            if (this.#playlistOverrides.length > 0) {
                playlist = this.#playlistOverrides.pop();
                console.debug('queue: override', playlist);
            } else {
                playlist = getNextPlaylist(this.#previousPlaylist);
                console.debug(`queue: round robin: ${this.#previousPlaylist} -> ${playlist}`);
                this.#previousPlaylist = playlist;
            }

            if (!playlist) {
                this.#htmlNoPlaylistsSelected.hidden = false;
                // fill() will be called again when a playlist is enabled
                return;
            }

            this.#htmlNoPlaylistsSelected.hidden = true;

            await queue.addRandomTrackFromPlaylist(playlist);
            // start next track if there is no current track playing (most likely when the page has just loaded)
            if (this.currentTrack == null) {
                console.info('queue: no current track, call next()');
                this.next();
            }

            this.#fillDelay = 0;
        } catch (error) {
            console.warn('queue: error');
            console.warn(error);
            if (this.#fillDelay < 10000) {
                this.#fillDelay += 1000;
            }
            setTimeout(() => this.fill(), this.#fillDelay);

        } finally {
            this.#filling = false;
        }

        // maybe we have more tracks to fill
        setTimeout(() => this.fill(), this.#fillDelay);
    };

    /**
     * @param {string} playlistName Playlist directory name
     */
    async addRandomTrackFromPlaylist(playlistName) {
        const playlist = await music.playlist(playlistName);
        const track = await playlist.chooseRandomTrack(false, getTagFilter());
        const downloadedTrack = await track.download(...settings.getTrackDownloadParams());
        this.add(downloadedTrack, false);
    };

    /**
     * Update queue HTML, if #queueChanged is true
     */
    updateHtml() {
        if (!this.#queueChanged) {
            return;
        }

        this.#queueChanged = false;

        const rows = /** @type {Array<HTMLTableRowElement>} */ ([]);
        let i = 0;
        let totalQueueDuration = 0;
        for (const queuedTrack of this.#combinedQueue()) {
            const track = queuedTrack.track;

            if (track instanceof Track) {
                totalQueueDuration += track.duration;
            }

            // Trash can that appears when hovering - click to remove track
            const trashTemplate = /** @type {HTMLTemplateElement} */ (document.getElementById('template-td-cover'));
            const tdCover = /** @type {HTMLTableSectionElement} */ (/** @type {HTMLElement} */ (trashTemplate.content.cloneNode(true)).firstElementChild);
            tdCover.style.backgroundImage = `url("${queuedTrack.imageUrl}")`;
            const rememberI = i;
            tdCover.onclick = () => queue.removeFromQueue(rememberI);

            // Track title HTML
            const tdTrack = document.createElement('td');
            tdTrack.appendChild(trackDisplayHtml(track, true));

            // Add columns to <tr> row and add the row to the table
            const row = document.createElement('tr');
            row.dataset.queuePos = i + '';
            row.appendChild(tdCover);
            row.appendChild(tdTrack);

            rows.push(row);
            i++;
        }

        this.#htmlCurrentQueueSize.textContent =
            this.#combinedQueueLength() + ' / ' + durationToString(totalQueueDuration);

        // If the queue is still loading (size smaller than target size), add a loading spinner
        if (i < this.#getMinimumSize()) {
            const spinnerTemplate = /** @type {HTMLTemplateElement} */ (document.getElementById('template-queue-spinner'));
            rows.push(/** @type {HTMLTableRowElement} */ (spinnerTemplate.content.cloneNode(true)));
        }

        // Add events to <tr> elements
        queue.#dragDropTable(rows);

        this.#htmlQueueTable.replaceChildren(...rows);
    };

    /**
     * @param {number} index
     */
    removeFromQueue(index) {
        const track = this.#combinedQueueSplice(index, 1)[0];
        track.revokeObjects();
        const removalBehaviour = this.#htmlQueueRemovalBehaviour.value;
        if (removalBehaviour === 'same') {
            // Add playlist to override array. Next time a track is picked, when #playlistOverrides contains elements,
            // one element is popped and used instead of choosing a random playlist.
            if (track.track instanceof Track) {
                this.#playlistOverrides.push(track.track.playlistName);
            }
        } else if (removalBehaviour !== 'roundrobin') {
            console.warn('queue: unexpected removal behaviour: ' + removalBehaviour);
        }
        this.fill();
    };

    // Based on https://code-boxx.com/drag-drop-sortable-list-javascript/
    /**
     * @param {Array<HTMLTableRowElement>} rows
     */
    #dragDropTable(rows) {
        let current = null; // Element that is being dragged

        for (let row of rows) {
            row.draggable = true; // Make draggable

            // The .hint class is purely cosmetic, it may be styled using css
            // Currently disabled because no CSS is applied

            row.ondragstart = () => {
                current = row;
                // for (let row2 of rows) {
                //     if (row2 != current) {
                //         row2.classList.add('hint');
                //     }
                // }
            };

            // row.ondragend = () => {
            //     for (let row2 of rows) {
            //         row2.classList.remove("hint");
            //     }
            // };

            row.ondragover = event => event.preventDefault();

            row.ondrop = (event) => {
                event.preventDefault();

                if (current == null) {
                    return;
                }

                if (row == current) {
                    // No need to do anything if row was put back in same location
                    return;
                }

                const currentPos = parseInt(current.dataset.queuePos);
                const targetPos = parseInt(/** @type {string} */ (row.dataset.queuePos));
                // Remove current (being dragged) track from queue
                const track = this.#combinedQueueSplice(currentPos, 1)[0];
                // Add it to the place it was dropped
                this.#combinedQueueSplice(targetPos, 0, track);
                // Now re-render the table
                this.updateHtml();
                current = null;
            };
        };
    };

    previous() {
        if (!this.currentTrack) {
            return;
        }

        // Try to skip to beginning of current track first
        const position = player.getPosition()
        if (position && position > 15 || !this.#previousTracks) {
            player.seek(0);
            return;
        }

        // Move current track to beginning of queue
        this.#manualQueuedTracks.unshift(this.currentTrack);
        // Replace current track with last track in history
        this.currentTrack = /** @type {DownloadedTrack} */ (this.#previousTracks.pop());
        this.#queueChanged = true;

        eventBus.publish(MusicEvent.TRACK_CHANGE, this.currentTrack);
        this.updateHtml();
    };

    next() {
        if (this.#combinedQueueLength() === 0) {
            console.warn('queue: no next track available');
            return;
        }

        // Add current track to history
        if (this.currentTrack !== null) {
            this.#previousTracks.push(this.currentTrack);
            // If history exceeded maximum length, remove first (oldest) element
            if (this.#previousTracks.length > MAX_HISTORY_SIZE) {
                const removedTrack = /** @type {DownloadedTrack } */ (this.#previousTracks.shift());
                removedTrack.revokeObjects();
            }
        }

        // Replace current track with first item from queue
        this.currentTrack = this.#combinedQueuePop();

        eventBus.publish(MusicEvent.TRACK_CHANGE, this.currentTrack);
        this.fill();
    };
};

export const queue = new Queue();

// When playlist checkboxes are loaded, fill queue
eventBus.subscribe(MusicEvent.PLAYLIST_CHANGE, () => queue.fill());

// Clear queue button
const clearButton = /** @type {HTMLButtonElement} */ (document.getElementById('queue-clear'));
clearButton.addEventListener('click', () => queue.clear());

// Fill queue when size is changed
const queueSizeSetting = /** @type {HTMLInputElement} */ (document.getElementById('settings-queue-size'));
queueSizeSetting.addEventListener('change', () => queue.fill());
