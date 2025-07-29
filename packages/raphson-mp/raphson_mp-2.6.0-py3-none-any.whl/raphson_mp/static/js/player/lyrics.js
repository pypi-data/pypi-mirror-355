import { eventBus, MusicEvent } from "./event.js";
import { queue } from "./queue.js";
import { TimeSyncedLyrics, PlainLyrics } from "../api.js";
import { coverSize } from "./coversize.js";
import { player } from "./player.js";
import { createToast, vars } from "../util.js";

class PlayerLyrics {
    #lyricsSetting = /** @type {HTMLInputElement} */ (document.getElementById("settings-lyrics"));
    #lyricsBox = /** @type {HTMLDivElement} */ (document.getElementById('lyrics-box'));
    #albumCoverBox = /** @type {HTMLDivElement} */ (document.getElementById('album-cover-box'));
    /** @type {number | null} */
    #lastLine = null;
    #updateSyncedLyricsListener;

    constructor() {
        this.#updateSyncedLyricsListener = () => this.#updateSyncedLyrics();

        // Quick toggle for lyrics setting
        this.#albumCoverBox.addEventListener('click', () => this.toggleLyrics());

        // Listener is only registered if page is visible, so if page visibility
        // changes we must register (or unregister) the listener.
        document.addEventListener('visibilitychange', () => this.#registerListener());

        // Handle lyrics setting being changed
        this.#lyricsSetting.addEventListener('change', () => {
            this.#replaceLyrics();
            coverSize.resizeCover();
        });

        eventBus.subscribe(MusicEvent.TRACK_CHANGE, () => {
            // When track changes, current state is no longer accurate
            this.#lastLine = null;
            this.#replaceLyrics();
        });
    }

    toggleLyrics() {
        this.#lyricsSetting.checked = !this.#lyricsSetting.checked;
        this.#lyricsSetting.dispatchEvent(new Event('change'));
        if (this.#lyricsSetting.checked) {
            createToast(vars.tLyricsEnabled);
        } else {
            createToast(vars.tLyricsDisabled);
        }
    }

    #updateSyncedLyrics() {
        const position = player.getPosition();

        if (!queue.currentTrack || !queue.currentTrack.lyrics || !(queue.currentTrack.lyrics instanceof TimeSyncedLyrics) || position === null) {
            throw new Error();
        }

        const lyrics = queue.currentTrack.lyrics;
        const currentLine = lyrics.currentLine(position);

        if (currentLine == this.#lastLine) {
            // Still the same line, no need to cause expensive DOM update.
            return;
        }

        this.#lastLine = currentLine;

        // Show current line, with context
        const context = 3;
        const lyricsHtml = [];
        for (let i = currentLine - context; i <= currentLine + context; i++) {
            if (i >= 0 && i < lyrics.text.length) {
                const lineHtml = document.createElement('span');
                lineHtml.textContent = lyrics.text[i].text;
                if (i != currentLine) {
                    lineHtml.classList.add('secondary-large');
                }
                lyricsHtml.push(lineHtml);
            }
            lyricsHtml.push(document.createElement('br'));
        }

        this.#lyricsBox.replaceChildren(...lyricsHtml);
    }

    #registerListener() {
        if (document.visibilityState == 'visible'
            && queue.currentTrack
            && queue.currentTrack.lyrics
            && queue.currentTrack.lyrics instanceof TimeSyncedLyrics
            && this.#lyricsSetting.checked
        ) {
            console.debug('lyrics: registered timeupdate listener');
            eventBus.unsubscribe(MusicEvent.PLAYER_POSITION, this.#updateSyncedLyricsListener); // remove it in case it is already registered
            eventBus.subscribe(MusicEvent.PLAYER_POSITION, this.#updateSyncedLyricsListener);
            // also trigger immediate update, especially necessary when audio is paused and no timeupdate events will be triggered
            this.#updateSyncedLyrics();
        } else {
            console.debug('lyrics: unregistered timeupdate listener');
            eventBus.unsubscribe(MusicEvent.PLAYER_POSITION, this.#updateSyncedLyricsListener); // remove it in case it is already registered
        }
    }

    #replaceLyrics() {
        const queuedTrack = queue.currentTrack;

        const showLyrics = queuedTrack && queuedTrack.lyrics && this.#lyricsSetting.checked;

        this.#lyricsBox.hidden = !showLyrics;

        if (showLyrics && queuedTrack.lyrics instanceof PlainLyrics) {
            this.#lyricsBox.textContent = queuedTrack.lyrics.text;
        }

        // time-synced lyrics is handled by updateSyncedLyrics
        this.#registerListener();
    }
}

export const lyrics = new PlayerLyrics();
