// assumes def variable is available
// assumes T variable is available

const threshold = def.options.plugins.zoom.zoom.drag.threshold || 0
let isEditingMode = false

function dispatchEditingModeEvent() {
    window.dispatchEvent(new CustomEvent("editingMode", {detail: {active: isEditingMode}}))
}

document.addEventListener("keyup", event => {
    isEditingMode = (event.key === "l")
    dispatchEditingModeEvent()
})

/**
 * Track start of labeling if 'L' key is pressed
 */
def.options.plugins.zoom.zoom.onZoomStart = function({chart}) {
    // increase threshold so no zooming happens
    chart.options.plugins.zoom.zoom.drag.threshold = isEditingMode ? 10000 : threshold

    return true
}

def.options.plugins.zoom.zoom.onThresholdRejected = function({chart, rect}) {
    if (isEditingMode && rect.width > 1) {
        const ax = chart.scales.x
        const startIndex = ax.getValueForPixel(rect.left)
        const endIndex = ax.getValueForPixel(rect.right)
        const startAt = T[startIndex]
        const endAt = T[endIndex]

        const label = prompt("Label for interval")

        label && window.dispatchEvent(new CustomEvent("label", {detail: {label, startAt, endAt}}))
    }

    isEditingMode = false
    dispatchEditingModeEvent()
}

return def