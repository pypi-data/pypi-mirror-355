import { DownloadedTrack, music } from "./api.js";
import { PlaylistCheckboxes } from "./playlistcheckboxes.js";
import { choice } from "./util.js";

/** @type {Array<DownloadedTrack>} */
const downloadedTracks = [];
const playlists = /** @type {HTMLDivElement} */ (document.getElementById('playlists'));
const cover =  /** @type {HTMLDivElement} */ (document.getElementById('cover'));
const audio = /** @type {HTMLAudioElement} */ (document.getElementById('audio'));
const loadingText = /** @type {HTMLDivElement} */ (document.getElementById('loading-text'));
const startText = /** @type {HTMLDivElement} */ (document.getElementById('start-text'));
const revealText = /** @type {HTMLDivElement} */ (document.getElementById('reveal-text'));
const nextText = /** @type {HTMLDivElement} */ (document.getElementById('next-text'));
const details = /** @type {HTMLDivElement} */ (document.getElementById('details'));

/** @type {DownloadedTrack | null} */
let currentTrack = null;
let state = 'start'; // one of: start, playing, reveal

function start() {
    // Choose a random track, and display it blurred. Show start text
    state = 'start';
    console.info('start');

    audio.pause();
    details.textContent = '';

    if (downloadedTracks.length == 0) {
        console.debug('games_guess: cachedTracks still empty')
        setTimeout(start, 500);
        return;
    }

    currentTrack = /** @type {DownloadedTrack} */ (downloadedTracks.shift());

    cover.style.backgroundImage = `url("${currentTrack.imageUrl}")`;
    audio.src = currentTrack.audioUrl;
    cover.classList.add('blurred');
    startText.hidden = false;
    nextText.hidden = true;
    loadingText.hidden = true;
}

function play() {
    // Hide start text, start playing audio, show reveal text
    state = 'playing';
    console.info('playing');
    startText.hidden = true;
    revealText.hidden = false;
    audio.play();
}

function reveal() {
    // Hide reveal text, show next text
    state = 'reveal'
    console.info('reveal');
    cover.classList.remove('blurred');
    revealText.hidden = true;
    nextText.hidden = false;
    if (!currentTrack || !currentTrack.track) throw new Error();
    details.textContent = currentTrack.track.displayText();
}

function onClick() {
    if (state == "start") {
        play();
    } else if (state == "playing") {
        reveal();
    } else if (state == "reveal") {
        start();
    }
}

cover.addEventListener('click', onClick);
document.addEventListener('keydown', event => {
    if (event.key == ' ') {
        onClick();
    }
});

async function fillCachedTracks() {
    if (downloadedTracks.length > 2) {
        return;
    }

    const enabledPlaylists = [];

    for (const input of playlists.getElementsByTagName('input')) {
        if (!input.dataset.playlist) throw new Error();
        if (input.checked) {
            enabledPlaylists.push(input.dataset.playlist);
        }
    }

    if (enabledPlaylists.length == 0) {
        return;
    }

    const playlistName = choice(enabledPlaylists);
    const playlist = await music.playlist(playlistName);
    const track = await playlist.chooseRandomTrack(true, {});
    const downloadedTrack = await track.download();
    downloadedTracks.push(downloadedTrack);
}

setInterval(fillCachedTracks, 2000);
fillCachedTracks(); // intentionally not awaited
start();

const onPlaylistChange = () => {
    downloadedTracks.length = 0;
    fillCachedTracks();
}

new PlaylistCheckboxes(playlists, onPlaylistChange).createPlaylistCheckboxes();
