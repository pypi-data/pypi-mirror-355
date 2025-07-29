export type Vars = {
    csrfToken: string,
    offlineMode: string,
    loadTimestamp: number,
    tBrowseArtist: string,
    tBrowseAlbum: string,
    tBrowseTag: string,
    tBrowsePlaylist: string,
    tBrowseYear: string,
    tBrowseRecentlyAdded: string,
    tBrowseRecentlyReleased: string,
    tBrowseRandom: string,
    tBrowseMissingMetadata: string,
    tBrowseNothing: string,
    tActivityFileAdded: string,
    tActivityFileModified: string,
    tActivityFileDeleted: string,
    tActivityFileMoved: string,
    tTrackInfoUnavailable: string,
    tNoData: string,
    tTheaterModeEnabled: string,
    tTheaterModeDisabled: string,
    tLyricsEnabled: string,
    tLyricsDisabled: string,
    tVisualiserEnabled: string,
    tVisualiserDisabled: string,
    tQueueCleared: string,
    tErrorOccurredReported: string,
    tErrorOccurredUnreported: string,
    tTokenSetUpSuccessfully: string,
    tInvalidSpotifyPlaylistUrl: string,
    tFingerprintFailed: string,
    tControlPause: string,
    tControlPlay: string,
    tControlPrevious: string,
    tControlNext: string,
    tTrackProblemReported: string,
};

export type TrackJson = {
    path: string
    mtime: number
    ctime: number
    duration: number
    title: string | null | undefined
    album: string | null | undefined
    album_artist: string | null | undefined
    year: number | null | undefined
    video: string | null | undefined
    lyrics: string | null | undefined
    artists: Array<string> | undefined
    tags: Array<string> | undefined
};

export type ControlServerPlaying = {
    player_id: string
    username: string
    update_time: number,
    paused: boolean,
    position: number,
    duration: number,
    control: boolean,
    volume: number,
    track: TrackJson,
};

export type ControlServerPlayed = {
    played_time: number,
    username: string,
    track: TrackJson,
};

export type ControlServerFileChange = {
    change_time: number,
    action: string,
    track: string,
    username: string | null,
};

export type WebauthnSetupVars = {
    challenge: string,
    identifier: string,
    username: string,
    displayname: string,
};
