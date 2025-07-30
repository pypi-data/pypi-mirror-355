// assumes def variable is available
// assumes T variable is available
let lastLabel = ''
let debounceTimeout

// on click, prompt for label and dispatch event
def.options.onClick = (event, elements) => {
    // debounce
    if (debounceTimeout)
        clearTimeout(debounceTimeout)

    debounceTimeout = setTimeout(() => {
        // on double click, event.native.detail is 2
        if (event.native.detail === 2) return;

        // detect click on point
        if (elements.length > 0 && elements[0].datasetIndex === event.chart.data.datasets.length - 1) {
            const point = event.chart.data.datasets[elements[0].datasetIndex].data[elements[0].index]
            window.dispatchEvent(new CustomEvent('pointClick', {detail: point}))
            return
        }

        const {x, y} = Chart.helpers.getRelativePosition(event, event.chart);
        const area = event.chart.chartArea

        if (x < area.left || x > area.right || y < area.top || y > area.bottom) return;

        const index = event.chart.scales.x.getValueForPixel(x);
        const t = T[Math.round(index)];
        const height = event.chart.scales.y.getValueForPixel(y);
        const label = prompt('Event label', lastLabel);

        if (label) {
            lastLabel = label;
            window.dispatchEvent(new CustomEvent('label', {detail: {label, t, height}}))
        }
    }, 200)
}

return def