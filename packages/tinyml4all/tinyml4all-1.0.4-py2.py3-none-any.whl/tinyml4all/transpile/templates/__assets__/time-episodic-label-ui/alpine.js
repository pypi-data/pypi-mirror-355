{
    events: [],

    get uniqueLabels() {
        return [...new Set(this.events.map(({label}) => label))]
    },

    get newLabels() {
        return this.uniqueLabels.filter(label => !(label in window.existingPalette))
    },

    get originalDataset() {
        return window.chart.data.datasets[window.chart.data.datasets.length - 1]
    },

    get dataset() {
        const newLabels = this.newLabels

        const data = this.events.map((e) => {
            // if event came from backend, pass it through
            if ('__source__' in e) return e

            const index = window.T.indexOf(e.t)
            const x = window.chart.data.labels[index]
            const backgroundColor = window.existingPalette[e.label] || window.newPalette[newLabels.indexOf(e.label)]

            return {
                x,
                y: e.height,
                label: e.label,
                t: e.t,
                tooltip: e.tooltip,
                backgroundColor
            }
        })

        return Object.assign({}, this.originalDataset, {
            data,
            backgroundColor: data.map((e) => e.backgroundColor)
        })
    },

    get fileOutput() {
        // kind of JSONL, but still valid JSON
        return '[\n' + this.events.map(({label, t, y, height}) => '  ' + JSON.stringify({label, t, height: Math.round(100 * (y || height)) / 100})).join(',\n') + '\n]'
    },

    init() {
        window.addEventListener('label', (ev) => this.addEvent(ev.detail))
        window.addEventListener('pointClick', (ev) => this.removeEvent(ev.detail.t))
        this.$nextTick(() => {
            this.events = this.originalDataset.data
            this.sync()
        })
    },

    addEvent({label, t, height}) {
        this.events.push({
            label,
            t,
            height,
            tooltip: `Label: ${label}`
        })

        this.sync()
    },

    removeEvent(t) {
        if (!confirm('Are you sure you want to remove this event?')) return;

        const index = this.events.map(e => e.t).indexOf(t)

        this.events.splice(index, 1)
        this.originalDataset.backgroundColor.splice(index, 1)
        this.sync()
    },

    sync() {
        window.chart.data.datasets[window.chart.data.datasets.length - 1] = this.dataset
        window.chart.update()
    }
}