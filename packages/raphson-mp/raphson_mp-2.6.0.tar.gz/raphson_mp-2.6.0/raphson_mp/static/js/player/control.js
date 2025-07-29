import { controlChannel, ControlCommand, Track } from "../api.js";
import { player, playerControls } from "./player.js";
import { queue } from "./queue.js";
import { eventBus, MusicEvent } from "./event.js";
import { createToast } from "../util.js";
import { vars } from "../util.js";

controlChannel.registerMessageHandler(ControlCommand.SERVER_PLAY, () => {
    createToast(vars.tControlPlay);
    player.play();
});

controlChannel.registerMessageHandler(ControlCommand.SERVER_PAUSE, () => {
    createToast(vars.tControlPause);
    player.pause();
});

controlChannel.registerMessageHandler(ControlCommand.SERVER_PREVIOUS, () => {
    createToast(vars.tControlPrevious);
    queue.previous();
});

controlChannel.registerMessageHandler(ControlCommand.SERVER_NEXT, () => {
    createToast(vars.tControlNext);
    queue.next();
});

async function updateNowPlaying() {
    const track = queue.currentTrack && queue.currentTrack.track instanceof Track ? queue.currentTrack.track : null;
    const duration = player.getDuration() ? player.getDuration() : (track ? track.duration : null);
    if (duration) {
        const data = {
            track: track ? track.path : null,
            paused: player.isPaused(),
            position: player.getPosition(),
            duration: duration,
            control: true,
            volume: playerControls.getVolume(),
        };

        controlChannel.sendMessage(ControlCommand.CLIENT_PLAYING, data);
    }
}

setInterval(updateNowPlaying, 30_000);

controlChannel.registerConnectHandler(() => {
    updateNowPlaying();
});

eventBus.subscribe(MusicEvent.PLAYER_PLAY, updateNowPlaying);
eventBus.subscribe(MusicEvent.PLAYER_PAUSE, updateNowPlaying);
eventBus.subscribe(MusicEvent.PLAYER_SEEK, updateNowPlaying);

export const remoteControl = window.location.hash ? window.location.hash.substring(1) : null;
