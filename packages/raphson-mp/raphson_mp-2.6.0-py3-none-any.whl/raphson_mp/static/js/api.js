// Common JavaScript interface to API, to be used by the music player and other pages.

import { vars, uuidv4, checkResponseCode, jsonPost, jsonGet } from "./util.js";

export const ControlCommand = {
    CLIENT_PLAYING: "c_playing",
    CLIENT_SUBSCRIBE: "c_subscribe",
    CLIENT_TOKEN: "c_token",
    CLIENT_PLAY: "c_play",
    CLIENT_PAUSE: "c_pause",
    CLIENT_PREVIOUS: "c_previous",
    CLIENT_NEXT: "c_next",
    SERVER_PLAYING: "s_playing",
    SERVER_PLAYED: "s_played",
    SERVER_PLAYING_STOPPED: "s_playing_stopped",
    SERVER_FILE_CHANGE: "s_file_change",
    SERVER_PLAY: "s_play",
    SERVER_PAUSE: "s_pause",
    SERVER_PREVIOUS: "s_previous",
    SERVER_NEXT: "s_next",
};

export const ControlTopic = {
    ACTIVITY: "activity",
};

class ControlChannel {
    /** @type {string} */
    #id;
    /** @type {Array<string>} */
    #subscriptions;
    /** @type {Object<string, Array<function>>} */
    #handlers;
    /** @type {Array<Function>} */
    #onConnect;
    /** @type {WebSocket | null} */
    #socket;
    constructor() {
        this.#id = uuidv4();
        this.#subscriptions = [];
        this.#handlers = {};
        this.#onConnect = [];
        this.#socket = null;

        for (const command of Object.values(ControlCommand)) {
            this.#handlers[command] = [];
        }

        if (!vars.offlineMode) {
            setInterval(() => {
                if (this.#socket == null ||
                    !(this.#socket.readyState in [WebSocket.CONNECTING, WebSocket.OPEN])
                ) {
                    this.#open();
                }
            }, 10000);

            this.#open();
        }
    }

    #open() {
        // Modern browsers (since early 2024) have support for connecting to a partial URL (just "/control?id=...").
        // However, we need to support earlier versions, especially because of mobile Safari and Firefox ESR in Linux distributions.
        // So, construct a URL manually:
        var url = new URL('/control?id=' + encodeURIComponent(this.#id), window.location.href);
        url.protocol = url.protocol.replace('http', 'ws'); // http -> ws, https -> wss
        console.info('ws: connect:', url.href);
        this.#socket = new WebSocket(url.href);

        this.#socket.addEventListener("message", event => this.#handleMessage(event.data));

        // Reissue previous subscriptions when socket is opened
        this.#socket.addEventListener("open", () => {
            this.sendMessage(ControlCommand.CLIENT_TOKEN, { "csrf": vars.csrfToken });
            for (const func of this.#onConnect) {
                func();
            }
            for (const topic of this.#subscriptions) {
                this.sendMessage(ControlCommand.CLIENT_SUBSCRIBE, { "topic": topic });
            }
        });
    }

    /**
     * @param {object} message
     */
    #handleMessage(message) {
        message = JSON.parse(message);
        console.debug('api: ws: received:', message);
        if (message.name in this.#handlers) {
            for (const handler of this.#handlers[message.name]) {
                handler(message);
            }
        } else {
            console.warn("ws: received command is unknown");
        }
    }

    /**
     * @param {string} name
     * @param {Object} data
     */
    sendMessage(name, data) {
        if (vars.offlineMode) {
            return;
        }
        if (this.#socket == null || this.#socket.readyState != WebSocket.OPEN) {
            console.warn('api: ws: disconnected, cannot send:', name);
            return;
        }
        console.debug('api: ws: send:', name, data);
        this.#socket.send(JSON.stringify({ "name": name, ...data }));
    }

    /**
     * @param {string} command
     * @param {function} handler
     */
    registerMessageHandler(command, handler) {
        this.#handlers[command].push(handler);
    }

    registerConnectHandler(handler) {
        this.#onConnect.push(handler);
    }

    /**
     * @param {string} topic
     */
    subscribe(topic) {
        this.#subscriptions.push(topic);
        this.sendMessage(ControlCommand.CLIENT_SUBSCRIBE, { "topic": topic });
    }

    async play(player_id) {
        this.sendMessage(ControlCommand.CLIENT_PLAY, { player_id: player_id });
    }

    async pause(player_id) {
        this.sendMessage(ControlCommand.CLIENT_PAUSE, { player_id: player_id });
    }

    async previous(player_id) {
        this.sendMessage(ControlCommand.CLIENT_PREVIOUS, { player_id: player_id });
    }

    async next(player_id) {
        this.sendMessage(ControlCommand.CLIENT_NEXT, { player_id: player_id });
    }

    sendStopSignal() {
        const data = new FormData();
        data.set("csrf", vars.csrfToken);
        data.set("id", this.#id);
        navigator.sendBeacon("/activity/stop", data);
    }
}

export const controlChannel = new ControlChannel();

export class Album {
    /** @type {string} */
    name;
    /** @type {string|null} */
    artist;
    /** @type {string} */
    track; // arbitrary track from album to get cover image
    constructor(albumObj) {
        this.name = albumObj.name;
        this.artist = albumObj.artist;
        this.track = albumObj.track;
    }

    /**
     * @param {string} imageQuality 'low' or 'high'
     * @param {boolean} stream
     * @param {boolean} memeCover
     * @returns {Promise<string>}
     */
    async getCover(imageQuality, stream, memeCover) {
        const imageUrl = `/track/${encodeURIComponent(this.track)}/cover?quality=${imageQuality}&meme=${memeCover ? 1 : 0}`;
        if (stream) {
            return imageUrl;
        } else {
            const coverResponse = await fetch(imageUrl);
            checkResponseCode(coverResponse);
            const imageBlob = await coverResponse.blob();
            console.debug('api: downloaded image', imageUrl);
            return URL.createObjectURL(imageBlob);
        }
    }
}

class SearchResult {
    /** @type {Array<Track>} */
    tracks;
    /** @type {Array<Album>} */
    albums;
    constructor(tracks, albums) {
        this.tracks = tracks;
        this.albums = albums;
    }
}

class Music {
    /** @type {Array<Playlist>} */
    #playlists;

    constructor() { }

    /**
     * @returns {Promise<Array<Playlist>>}
     */
    async playlists() {
        // has to be an anonymous function assigned to a variable instead of a normal function or 'this' is not available
        const retrievePlaylists = async () => {
            if (this.#playlists == undefined) {
                const response = await fetch('/playlist/list');
                checkResponseCode(response);
                const json = await response.json();
                this.#playlists = [];
                for (const playlistObj of json) {
                    this.#playlists.push(new Playlist(playlistObj));
                }
            }
        };

        if (navigator.locks) {
            await navigator.locks.request("api_playlists", retrievePlaylists);
        } else {
            console.warn('navigator.locks not available, redundant requests may happen');
            await retrievePlaylists();
        }

        return this.#playlists;
    }

    /**
     * @param {string} name
     * @returns {Promise<Playlist>}
     */
    async playlist(name) {
        const playlists = await this.playlists();
        for (const playlist of playlists) {
            if (playlist.name == name) {
                return playlist;
            }
        }
        throw new Error("playlist not found: " + name);
    }

    /**
     * @param {Array<import("./types.js").TrackJson>} json
     * @returns {Array<Track>}
     */
    #tracksFromJson(json) {
        const tracks = [];
        for (const trackObj of json) {
            tracks.push(new Track(trackObj));
        }
        return tracks;
    }

    /**
     * @param {Array<object>} json
     * @returns {Array<Album>}
     */
    #albumsFromJson(json) {
        const albums = [];
        for (const album of json) {
            albums.push(new Album(album));
        }
        return albums;
    }

    /**
     * @param {object} filters with key = playlist, artist, album_artist, album, etc.
     * @returns {Promise<Array<Track>>}
     */
    async filter(filters) {
        const encodedFilters = [];
        for (const filter in filters) {
            encodedFilters.push(filter + '=' + encodeURIComponent(filters[filter]));
        }
        const response = await fetch('/tracks/filter?' + encodedFilters.join('&'));
        checkResponseCode(response);
        const json = await response.json();
        return this.#tracksFromJson(json.tracks);
    }

    /**
     * Paginated alternative to filter()
     * @param {object} filters
     * @param {((tracks: Array<Track>) => Promise<void>)} callback function that accepts a list of tracks
     */
    async filterPages(filters, callback) {
        filters = structuredClone(filters); // avoid modifying 'limit' on existing filters object
        const totalLimit = filters.limit ? filters.limit : 5000;
        filters.limit = Math.min(1000, totalLimit);
        filters.offset = 0;
        while (true) {
            console.debug('api: filter', filters);
            const tracks = await this.filter(filters);
            await callback(tracks);
            filters.offset += tracks.length;
            if (tracks.length < filters.limit || filters.offset >= totalLimit) {
                break;
            }
        }
    }

    /**
     * @param {string} query FTS5 search query
     * @returns {Promise<SearchResult>}
     */
    async search(query) {
        const response = await fetch('/tracks/search?query=' + encodeURIComponent(query));
        checkResponseCode(response);
        const json = await response.json();
        const tracks = this.#tracksFromJson(json.tracks);
        const albums = this.#albumsFromJson(json.albums);
        return new SearchResult(tracks, albums);
    }

    /**
     * @param {string} path
     * @returns {Promise<Track>}
     */
    async track(path) {
        const response = await fetch(`/track/info${encodeURIComponent(path)}/info`);
        checkResponseCode(response);
        return new Track(await response.json());
    }

    /**
     * @returns {Promise<Array<string>>}
     */
    async tags() {
        const response = await fetch('/tracks/tags');
        checkResponseCode(response);
        return await response.json();
    }

    /**
     * @param {Track} track
     * @param {number} startTimestamp
     */
    async played(track, startTimestamp) {
        const data = {
            track: track.path,
            timestamp: startTimestamp,
        };
        await jsonPost('/activity/played', data);
    }

    /**
     * @param {string} url
     * @returns {Promise<DownloadedTrack>}
     */
    async downloadTrackFromWeb(url) {
        const audioResponse = await fetch('/download/ephemeral?url=' + encodeURIComponent(url));
        checkResponseCode(audioResponse);
        const track = new VirtualTrack(url);
        const audio = URL.createObjectURL(await audioResponse.blob());
        const image = '/static/img/raphson_small.webp';
        return new DownloadedTrack(track, audio, image, null);
    }

    /**
     * @returns {Promise<DownloadedTrack|null>}
     */
    async downloadNews() {
        const audioResponse = await fetch('/news/audio');
        if (audioResponse.status == 503) {
            return null;
        }
        checkResponseCode(audioResponse);
        const track = new VirtualTrack(audioResponse.headers.get("X-Name"));
        const audioBlob = URL.createObjectURL(await audioResponse.blob());
        const imageUrl = '/static/img/raphson.png';
        return new DownloadedTrack(track, audioBlob, imageUrl, null);
    }
}

export const music = new Music();

export class Playlist {
    /** @type {string} */
    name;
    /** @type {number} */
    trackCount;
    /** @type {boolean} */
    favorite;
    /** @type {boolean} */
    write;

    /**
     * @param {Object.<string, string|boolean|number>} objectFromApi
     */
    constructor(objectFromApi) {
        this.name = /** @type {string} */ (objectFromApi.name);
        this.trackCount = /** @type {number} */ (objectFromApi.track_count);
        this.favorite = /** @type {boolean} */ (objectFromApi.favorite);
        this.write = /** @type {boolean} */ (objectFromApi.write);
    }

    /**
     * @param {boolean} requireMetadata
     * @param {object} tagFilter Empty object for no tag filter
     * @returns
     */
    async chooseRandomTrack(requireMetadata, tagFilter) {
        const chooseResponse = await jsonPost('/playlist/' + encodeURIComponent(this.name) + '/choose_track', { 'require_metadata': requireMetadata, ...tagFilter });
        const trackData = await chooseResponse.json();
        console.info('api: chosen track', trackData.path);
        return new Track(trackData);
    }
}

/**
 * Metadata suggested by AcoustID
 */
export class AcoustIDSuggestedRelease {
    /** @type {string} */
    id;
    /** @type {string} */
    title;
    /** @type {Array<string>} */
    artists;
    /** @type {string} */
    album;
    /** @type {string} */
    albumArtist;
    /** @type {number | null} */
    year;
    /** @type {string} */
    releaseType;
    /** @type {string} */
    packaging;

    constructor(metaObj) {
        this.id = metaObj.id;
        this.title = metaObj.title;
        this.artists = metaObj.artists;
        this.album = metaObj.album;
        this.albumArtist = metaObj.album_artist;
        this.year = metaObj.year;
        this.releaseType = metaObj.release_type;
        this.packaging = metaObj.packaging;
    }
}

export class AcoustIDResult {
    /** @type {string} */
    acoustid; // acoustid track id
    /** @type {Array<AcoustIDSuggestedRelease>} */
    releases;

    constructor(dataObj) {
        this.acoustid = dataObj.acoustid;
        this.releases = [];
        for (const meta of dataObj.releases) {
            this.releases.push(new AcoustIDSuggestedRelease(meta));
        }
    }
}

export class Track {
    /** @type {string} */
    path;
    /** @type {number} */
    duration;
    /** @type {Array<string>} */
    tags;
    /** @type {string | null} */
    title;
    /** @type {Array<string>} */
    artists;
    /** @type {string | null} */
    album;
    /** @type {string | null} */
    albumArtist;
    /** @type {number | null} */
    year;
    /** @type {string | null} */
    video;
    /** @type {string | null} */
    lyrics;

    /**
     * @param {import("./types.js").TrackJson} trackData
     */
    constructor(trackData) {
        this.#updateLocalVariablesFromTrackDataResponse(trackData);
    };

    get playlistName() {
        return this.path.substring(0, this.path.indexOf('/'));
    }

    /**
     * @param {import("./types.js").TrackJson} trackData
     */
    #updateLocalVariablesFromTrackDataResponse(trackData) {
        this.path = trackData.path;
        this.duration = trackData.duration;
        this.title = trackData.title || null;
        this.album = trackData.album || null;
        this.albumArtist = trackData.album_artist || null;
        this.year = trackData.year || null;
        this.video = trackData.video || null;
        this.lyrics = trackData.lyrics || null;
        this.artists = trackData.artists || [];
        this.tags = trackData.tags || [];
    }

    /**
     * Generates display text for this track
     * @param {boolean} showPlaylist
     * @returns {string}
     */
    displayText(showPlaylist = true, showAlbum = true) {
        // Should be similar to on Metadata.display_title on server for consistency

        let text = '';

        if (showPlaylist) {
            text += `${this.playlistName}: `;
        }

        if (this.artists !== null && this.title !== null) {
            text += this.artists.join(', ');
            text += ' - ';
            text += this.title;

            if (this.album && showAlbum) {
                text += ` (${this.album}`;
                if (this.year) {
                    text += `, ${this.year})`;
                } else {
                    text += ')';
                }
            } else if (this.year) {
                text += ` (${this.year})`;
            }
        } else {
            // Not enough metadata available, generate display title based on file name
            let filename = this.path.substring(this.path.lastIndexOf('/') + 1);

            // remove extension
            filename = filename.substring(0, filename.lastIndexOf('.'))

            // Remove YouTube id suffix
            filename = filename.replaceAll(/\[[a-zA-Z0-9\-_]+\]/g, "")

            // Remove whitespace
            filename = filename.trim()

            text += filename;
        }

        return text;
    };

    /**
     * @param {string} audioType
     * @param {boolean} stream
     * @returns {Promise<string>} URL
     */
    async getAudio(audioType, stream) {
        const audioUrl = `/track/${encodeURIComponent(this.path)}/audio?type=${audioType}`;
        if (stream) {
            return audioUrl;
        } else {
            const trackResponse = await fetch(audioUrl);
            checkResponseCode(trackResponse);
            const audioBlob = await trackResponse.blob();
            console.debug('api: downloaded audio', audioUrl);
            return URL.createObjectURL(audioBlob);
        }
    }

    getAlbum() {
        return new Album({ 'name': this.album, 'artist': this.albumArtist, 'track': this.path });
    }

    /**
     * @returns {Promise<Lyrics|null>}
     */
    async getLyrics() {
        const lyricsUrl = `/track/${encodeURIComponent(this.path)}/lyrics`;
        const lyricsResponse = await fetch(lyricsUrl);
        checkResponseCode(lyricsResponse);
        const lyricsJson = await lyricsResponse.json();
        console.debug('api: downloaded lyrics', lyricsUrl);
        switch (lyricsJson.type) {
            case "none":
                return null;
            case "synced":
                const lines = [];
                for (const line of lyricsJson.text) {
                    lines.push(new LyricsLine(line.start_time, line.text));
                }
                return new TimeSyncedLyrics(lyricsJson.source, lines);
            case "plain":
                return new PlainLyrics(lyricsJson.source, lyricsJson.text);
        }
        throw new Error("unexpected lyrics type");
    }

    /**
     * @param {string} audioType
     * @param {boolean} stream
     * @param {boolean} memeCover
     * @returns {Promise<DownloadedTrack>}
     */
    async download(audioType = 'webm_opus_high', stream = false, memeCover = false) {
        // Download audio, cover, lyrics in parallel
        const promises = /** @type {[Promise<string>, Promise<string>, Promise<Lyrics | null>]} */ ([
            this.getAudio(audioType, stream),
            this.getAlbum().getCover(audioType == 'webm_opus_low' ? 'low' : 'high', stream, memeCover),
            this.getLyrics(),
        ]);
        return new DownloadedTrack(this, ...(await Promise.all(promises)));
    }

    async delete() {
        const oldName = this.path.split('/').pop();
        const newName = '.trash.' + oldName;
        await jsonPost('/files/rename', { path: this.path, new_name: newName });
    }

    async dislike() {
        await jsonPost('/dislikes/add', { track: this.path });
    }

    /**
     * Updates track metadata by sending current metadata of this object to the server.
     */
    async saveMetadata() {
        const payload = {
            title: this.title,
            album: this.album,
            artists: this.artists,
            album_artist: this.albumArtist,
            tags: this.tags,
            year: this.year,
            lyrics: this.lyrics,
        };

        await jsonPost(`/track/${encodeURIComponent(this.path)}/update_metadata`, payload);
    }

    /**
     * Copy track to other playlist
     * @param {string} playlistName
     * @returns {Promise<void>}
     */
    async copyTo(playlistName) {
        await jsonPost('/player/copy_track', { track: this.path, playlist: playlistName });
    }

    async refresh() {
        const json = await jsonGet(`/track/${encodeURIComponent(this.path)}/info`);
        this.#updateLocalVariablesFromTrackDataResponse(json);
    }

    /**
     * Look up metadata for this track using the AcoustID service
     * @returns {Promise<AcoustIDResult | null>}
     */
    async acoustid() {
        const json = await jsonGet(`/track/${encodeURIComponent(this.path)}/acoustid`);
        return json ? new AcoustIDResult(json) : null;
    }

    getVideoURL() {
        return `/track/${encodeURIComponent(this.path)}/video`;
    }

    async reportProblem() {
        await jsonPost(`/track/${encodeURIComponent(this.path)}/report_problem`, {})
    }
}

export class VirtualTrack {
    /** @type {string} */
    title;

    constructor(title) {
        this.title = title;
    }
}

export class DownloadedTrack {
    /**
     * @type {Track|VirtualTrack}
     */
    track;
    /**
     * @type {string}
     */
    audioUrl;
    /**
     * @type {string}
     */
    imageUrl;
    /**
     * @type {Lyrics|null}
     */
    lyrics;

    /**
     *
     * @param {Track|VirtualTrack} track
     * @param {string} audioUrl
     * @param {string} imageUrl
     * @param {Lyrics|null} lyrics
     */
    constructor(track, audioUrl, imageUrl, lyrics) {
        this.track = track;
        this.audioUrl = audioUrl;
        this.imageUrl = imageUrl;
        this.lyrics = lyrics;
    }

    revokeObjects() {
        // audioUrl and imageUrl are not always object URLs. If they are not, revokeObjectURL does not raise an error.
        URL.revokeObjectURL(this.audioUrl);
        URL.revokeObjectURL(this.imageUrl);
    }
}

export class Lyrics {
    /** @type {string | null} */
    source;
    constructor(source) {
        this.source = source;
    };
};

export class PlainLyrics extends Lyrics {
    /** @type {string} */
    text;
    constructor(source, text) {
        super(source);
        this.text = text;
    };
};

export class LyricsLine {
    /** @type {number} */
    startTime;
    /** @type {string} */
    text;
    constructor(startTime, text) {
        this.startTime = startTime;
        this.text = text;
    }
}

export class TimeSyncedLyrics extends Lyrics {
    /** @type {Array<LyricsLine>} */
    text;
    constructor(source, text) {
        super(source);
        this.text = text;
    };

    /**
     * @returns {string}
     */
    asPlainText() {
        const lines = [];
        for (const line of this.text) {
            lines.push(line.text);
        }
        return lines.join('\n');
    }

    /**
     * @param {number} currentTime
     * @returns {number}
     */
    currentLine(currentTime) {
        currentTime += 0.5; // go to next line slightly earlier, to give the user time to read
        // current line is the last line where currentTime is after the line start time
        for (let i = 0; i < this.text.length; i++) {
            if (currentTime < this.text[i].startTime) {
                return i - 1;
            }
        }
        return this.text.length - 1;
    }
};
