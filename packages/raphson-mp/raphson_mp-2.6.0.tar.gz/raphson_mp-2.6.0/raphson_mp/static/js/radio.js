import { DownloadedTrack, Track } from "./api.js";
import { jsonGet } from "./util.js";

const updateInterval = 1000;

class RadioTrack {
    /** @type {number} */
    startTime;
    /** @type {DownloadedTrack} */
    downloadedTrack;
    constructor(startTime, downloadedTrack) {
        this.startTime = startTime;
        this.downloadedTrack = downloadedTrack;
    }
}

const state = {
    /** @type {RadioTrack | null} */
    currentTrack: null,
    /** @type {RadioTrack | null} */
    nextTrack: null,
};

async function updateState() {
    if (state.currentTrack && state.nextTrack) {
        console.debug('radio: updateState: ok');
        return;
    }

    const json = await jsonGet('/radio/info');

    if (state.currentTrack == null) {
        console.debug('radio: updateState: init currentTrack');
        const download = await new Track(json.current).download();
        state.currentTrack = new RadioTrack(json.current_time, download);
    }

    if (state.nextTrack == null) {
        console.debug('radio: updateState: init nextTrack');
        const download = await new Track(json.next).download();
        state.nextTrack = new RadioTrack(json.next_time, download);
    }
}

setInterval(updateState, 10_000);
updateState();


const audio = /** @type {HTMLAudioElement} */ (document.getElementById('audio'));
const image = /** @type {HTMLImageElement} */ (document.getElementById('image'));
const current = /** @type {HTMLSpanElement} */ (document.getElementById('current'));
const next = /** @type {HTMLSpanElement} */ (document.getElementById('next'));
const status = /** @type {HTMLSpanElement} */ (document.getElementById('status'));
const play = /** @type {HTMLButtonElement} */ (document.getElementById('play'));

/**
 * @param {RadioTrack} track
 */
async function setSrc(track) {
    console.debug('radio: setSrc');
    audio.src = track.downloadedTrack.audioUrl;
    image.src = track.downloadedTrack.imageUrl;

    try {
        await audio.play();
    } catch (err) {
        console.warn('cannot play, autoplay blocked?', err);
    }
}

async function update() {
    if (state.currentTrack != null) {
        current.textContent = state.currentTrack.downloadedTrack.track.displayText();
    } else {
        current.textContent = 'loading';
    }

    if (state.nextTrack != null) {
        next.textContent = state.nextTrack.downloadedTrack.track.displayText();
    } else {
        next.textContent = 'loading';
    }

    if (state.currentTrack == null) {
        return;
    }

    // load initial track, once available
    if (audio.src == '') {
        console.debug('radio: set initial audio');
        await setSrc(state.currentTrack);
    }

    const currentPos = Date.now() - state.currentTrack.startTime;
    const offset = audio.currentTime * 1000 - currentPos;
    let rate = 1;

    if (Math.abs(offset) > 1000) {
        console.debug('radio: large offset', offset, 'skip from', audio.currentTime, 'to', currentPos / 1000);
        audio.currentTime = currentPos / 1000;
        audio.playbackRate = 1;
        status.textContent = 'very out of sync';
    } else {
        // Aim to be in sync in 60 seconds
        rate = 1 - offset / (60 * updateInterval);
        audio.playbackRate = rate;
        if (Math.abs(offset) < 100) {
            status.textContent = 'in sync';
        } else {
            status.textContent = 'out of sync';
        }
    }

    status.textContent += " | " + Math.round(offset / 10) / 100 + 's';
    status.textContent += " | " + Math.round(rate * 1000) / 1000 + 'x';
};

setInterval(update, updateInterval);

audio.addEventListener('ended', async () => {
    state.currentTrack = state.nextTrack;
    state.nextTrack = null;
    await setSrc(state.currentTrack);
});

play.addEventListener('click', () => {
    audio.play();
});
