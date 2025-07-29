/*
Build eCharts on this page: https://echarts.apache.org/en/builder.html
Charts: Bar, Heatmap
Coordinate systems: Grid
Component: Title, Legend, Tooltip, VisualMap
Others: Code Compression
*/
import "../lib/echarts-5.6.1.js";
import { vars } from "./util.js";

const commonOptions = {
    backgroundColor: 'transparent',
    textStyle: {
        fontFamily: 'Quicksand',
    },
    color: [
        '#dd6b66',
        '#759aa0',
        '#e69d87',
        '#8dc1a9',
        '#ea7e53',
        '#eedd78',
        '#73a373',
        '#73b9bc',
        '#7289ab',
        '#91ca8c',
        '#f49f42',
        '#a77fdd',
        '#dd7f98',
        '#ddab7f',
        '#7f91dd',
    ],
};

const buttons = {
    day: /** @type {HTMLButtonElement} */ (document.getElementById('btn-day')),
    week: /** @type {HTMLButtonElement} */ (document.getElementById('btn-week')),
    month: /** @type {HTMLButtonElement} */ (document.getElementById('btn-month')),
    year: /** @type {HTMLButtonElement} */ (document.getElementById('btn-year')),
    all: /** @type {HTMLButtonElement} */ (document.getElementById('btn-all')),
};

async function loadCharts(button, period) {
    console.info('load charts:', period);

    // Update buttons
    for (const otherButton of Object.values(buttons)) {
        otherButton.disabled = false;
    }
    button.disabled = true;

    // Render charts
    const promises = [];
    for (const chartElem of document.getElementsByClassName("chart")) {
        const id = chartElem.dataset.id;
        promises.push((async () => {
            const response = await fetch('/stats/data/' + encodeURIComponent(id) + '?period=' + encodeURIComponent(period));
            if (response.status == 200) {
                const data = await response.json();
                chartElem.style.border = null;
                let eChart = echarts.getInstanceByDom(chartElem);
                if (!eChart) {
                    eChart = echarts.init(chartElem, 'dark');
                }
                // https://echarts.apache.org/en/api.html#echartsInstance.setOption
                // replaceMerge is required to be able to remove data (e.g. when going from last year to last week's data)
                eChart.setOption({...data, ...commonOptions}, {replaceMerge: ['series'], lazyUpdate: true});
            } else if (response.status == 204) {
                echarts.dispose(chartElem);
                chartElem.textContent = vars.tNoData;
                chartElem.style.border = '1px dashed rgba(255, 255, 255, 0.5)'
            } else {
                checkResponseCode(response);
            }
        })());
    }

    // Wait for all charts to load
    await Promise.all(promises);
    // TODO do something with a spinner
}

// Delayed resize, to avoid redrawing charts many times during a resize
let resizeTimerId = 0;

function doResize() {
    resizeTimerId = 0;
    for (const chartElem of document.getElementsByClassName("chart")) {
        let eChart = echarts.getInstanceByDom(chartElem);
        if (eChart) {
            // https://echarts.apache.org/en/api.html#echartsInstance.resize
            eChart.resize({animation: {duration: 50}});
        }
    }
}

function delayedResize() {
    if (resizeTimerId != 0) {
        clearTimeout(resizeTimerId);
        resizeTimerId = 0;
    }
    resizeTimerId = setTimeout(doResize, 50);
}

for (const buttonName in buttons) {
    const button = buttons[buttonName];
    button.addEventListener('click', () => {
        window.location.hash = buttonName;
        loadCharts(button, buttonName);
    });
}

window.addEventListener('resize', delayedResize);

(() => {
    for (const buttonName in buttons) {
        if (window.location.hash == '#' + buttonName) {
            loadCharts(buttons[buttonName], buttonName);
            return;
        }
    }

    loadCharts(buttons['week'], "week");
})();
