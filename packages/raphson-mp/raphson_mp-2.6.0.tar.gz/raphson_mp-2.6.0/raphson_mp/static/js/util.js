/** @type {import("./types").Vars} */
export const vars = JSON.parse(/** @type {string} */(/** @type {HTMLScriptElement} */ (document.getElementById('vars')).textContent));

/**
 * @param {number} seconds
 * @returns {string} formatted duration
 */
export function durationToString(seconds) {
    // If you modify this function, also copy it to util.js!
    const isoString = new Date(1000 * seconds).toISOString();
    const days = Math.floor(seconds / (24 * 60 * 60));
    const hours = parseInt(isoString.substring(11, 13)) + (days * 24);
    const mmss = isoString.substring(14, 19);
    if (hours == 0) {
        return mmss;
    } else {
        return hours + ':' + mmss;
    }
}

/**
 * @param {number} seconds
 * @returns {string}
 */
export function timestampToString(seconds) {
    if (seconds == 0) {
        return '-';
    } else {
        return new Date(1000 * seconds).toLocaleString();
    }
}

/**
 * @param {number} min
 * @param {number} max
 * @returns {number}
 */
export function randInt(min, max) {
    return Math.floor(Math.random() * (max - min)) + min;
}

/**
 * @template T
 * @param {Array<T>} arr
 * @returns {T}
 */
export function choice(arr) {
    return arr[randInt(0, arr.length)];
}

export function formatLargeNumber(number) {
    if (number > 1_000_000) {
        return (number / 1_000_000).toFixed(1) + 'M';
    } else if (number > 1_000) {
        return (number / 1_000).toFixed(1) + 'k';
    } else {
        return number + '';
    }
}

/**
 * Create button element containing an icon
 * @param {string} iconName
 * @returns {HTMLButtonElement}
 */
export function createIconButton(iconName) {
    const button = document.createElement('button');
    button.classList.add('icon-button');
    const icon = document.createElement('div');
    icon.classList.add('icon', 'icon-' + iconName);
    button.appendChild(icon);
    return button;
}

/**
 * Replace icon in icon button
 * @param {HTMLButtonElement} iconButton
 * @param {string} iconName
 */
export function replaceIconButton(iconButton, iconName) {
    const icon = /** @type {HTMLElement} */ (iconButton.firstChild);
    icon.classList.remove(...icon.classList.values());
    icon.classList.add('icon', 'icon-' + iconName);
    if (iconName == 'loading') {
        icon.classList.add('spinning');
    } else {
        icon.classList.remove('spinning');
    }
}

// https://stackoverflow.com/a/2117523
export function uuidv4() {
    return "10000000-1000-4000-8000-100000000000".replace(/[018]/g, c =>
        (+c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> +c / 4).toString(16)
    );
}

export function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
}

/**
 * Throw error if response status code is an error code
 * @param {Response} response
 */
export function checkResponseCode(response) {
    if (!response.ok) {
        throw Error('response code ' + response.status + ' for url ' + response.url);
    }
}

/**
 * @param {string} url
 * @param {object} postDataObject
 * @returns {Promise<Response>}
 */
export async function jsonPost(url, postDataObject, checkError = true) {
    postDataObject.csrf = vars.csrfToken;
    const options = {
        method: 'POST',
        body: JSON.stringify(postDataObject),
        headers: new Headers({
            'Content-Type': 'application/json'
        }),
    };
    const response = await fetch(new Request(url, options));
    if (checkError) {
        checkResponseCode(response);
    }
    return response;
}

export async function jsonGet(url, checkError = true) {
    const options = {
        headers: new Headers({
            'Accept': 'application/json'
        }),
    };
    const response = await fetch(new Request(url, options));
    if (checkError) {
        checkResponseCode(response);
    }
    if (response.status == 204) {  // HTTP No Content
        return null;
    }
    return await response.json();
}

function errorObjectToJson(error) {
    if (error instanceof ErrorEvent) {
        return {
            type: 'ErrorEvent',
            message: error.message,
            file: error.filename,
            line: error.lineno,
            error: errorObjectToJson(error.error),
        }
    }

    if (error instanceof PromiseRejectionEvent) {
        return {
            type: 'PromiseRejectionEvent',
            reason: errorObjectToJson(error.reason),
        }
    }

    if (['string', 'number', 'boolean'].includes(typeof(error))) {
        return {
            type: 'literal',
            value: error,
        }
    }

    if (error instanceof Error) {
        return {
            type: 'Error',
            name: error.name,
            message: error.message,
            stack: error.stack,
        }
    }

    if (error == null) {
        return null;
    }

    return {
        name: 'unknown error object',
        type: typeof(error),
        string: String(error),
    }
}

export async function sendErrorReport(error) {
    console.error(error);
    try {
        const errorJson = JSON.stringify(errorObjectToJson(error));
        await fetch('/report_error', {method: 'POST', body: errorJson, headers: {'Content-Type': 'application/json'}});
        createToast(vars.tErrorOccurredReported);
    } catch (error2) {
        // need to catch errors, this function must never throw an error or a loop is created
        console.error('unable to report error:', error2)
        createToast(vars.tErrorOccurredUnreported);
    }
}

// https://stackoverflow.com/a/30546115/4833737
function cssToMS(s) {
    return parseFloat(s) * (/\ds$/.test(s) ? 1000 : 1);
}

export const TRANSITION_DURATION = cssToMS(window.getComputedStyle(document.body).getPropertyValue('--transition-duration'));

const TOAST_HIDE_TIME = 5000;

/**
 * @param {string} text
 */
export function createToast(text) {
    const toast = document.createElement("div");
    toast.classList.add("toast", "hidden", "box", "padding");
    toast.textContent = text;
    document.getElementById("toasts")?.prepend(toast);
    setTimeout(() => toast.classList.remove("hidden"), 0);
    setTimeout(() => toast.classList.add("hidden"), TOAST_HIDE_TIME);
    setTimeout(() => toast.remove(), TOAST_HIDE_TIME + TRANSITION_DURATION);
}
