import { windows } from "./window.js";
import { queue } from "./queue.js";
import { player, playerControls } from "./player.js";
import { search } from "./search.js";
import { lyrics } from "./lyrics.js";
import { theater } from "./theater.js";
import { visualiser } from "./visualise.js";

const VOLUME_HOTKEY_CHANGE = 0.05;

document.addEventListener('keydown', event => {
    // Ignore hotkey when in combination with modifier keys
    if (event.ctrlKey || event.altKey || event.metaKey) {
        return;
    }

    const key = event.key;

    // Ignore F<N> keys
    if (event.key.length >= 2 && event.key[0] == 'F') {
        return;
    }

    // Don't perform hotkey actions when user is typing in a text field
    // But do still allow escape key
    if (document.activeElement &&
        ['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName) &&
        key !== 'Escape') {
        console.debug('hotkey: ignoring keypress:', key);
        return;
    }

    event.preventDefault();

    if (key === 'p' || key === ' ') {
        player.isPaused() ? player.play() : player.pause();
    } else if (key === 'ArrowLeft') {
        queue.previous();
    } else if (key === 'ArrowRight') {
        queue.next();
    } else if (key == 'ArrowUp') {
        playerControls.setVolume(playerControls.getVolume() + VOLUME_HOTKEY_CHANGE);
    } else if (key == 'ArrowDown') {
        playerControls.setVolume(playerControls.getVolume() - VOLUME_HOTKEY_CHANGE);
    } else if (key === '.' || key == '>') {
        player.seekRelative(3);
    } else if (key === ',' || key == '<') {
        player.seekRelative(-3);
    } else if (key === 'Escape') {
        windows.closeTop();
    } else if (key == '/') {
        search.openSearchWindow();
    } else if (key == "c") {
        queue.clear();
    } else if (key == "l") {
        lyrics.toggleLyrics();
    } else if (key == "t") {
        theater.toggle();
    } else if (key == "v") {
        visualiser.toggleSetting();
    } else {
        console.debug('hotkey: unhandled keypress:', key);
    }
});
