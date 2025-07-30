{
    labelAnnotations: window.labelAnnotations,
    created: window.labelAnnotations.length,
    isEditingMode: false,

    get output() {
        return [
            `# paste this code after TimeSeries.read_csv or TimeSeries.read_csv_folder`,
            ...this.labelAnnotations.map(({t1, t2, label}) => {
                const labelName = label.content.split(': ')[1]

                return `ts.add_label('${labelName}', start_at='${t1}', end_at='${t2}')`
            }),
            '',
            '# save to a file for later use',
            `ts.save_to(folder='path-to-folder', name='dataset-name')`
        ].join('\n')
    },

    init() {
        window.addEventListener('label', (ev) => this.addLabelAnnotation(ev.detail))
        window.addEventListener('editingMode', (ev) => this.isEditingMode = ev.detail.active)
    },

    addLabelAnnotation({label, startAt, endAt}) {
        const startIndex = window.T.indexOf(startAt)
        const endIndex = window.T.indexOf(endAt)
        const annotation = {
            uid: Math.random().toString(36).substr(2, 9),
            type: 'box',
            label: {content: `label: ${label}`},
            t1: startAt.replace(' ', 'T'),
            t2: endAt.replace(' ', 'T'),
            xMin: window.chart.data.labels[startIndex],
            xMax: window.chart.data.labels[endIndex],
            yMin: (ctx) => percent(ctx.chart.scales.y, 0),
            yMax: (ctx) => percent(ctx.chart.scales.y, 0.93),
            backgroundColor: window.annotationPalette[this.created % window.annotationPalette.length]
        }

        this.labelAnnotations.push(annotation)
        this.created += 1

        // sync chart
        window.chart.options.plugins.annotation.annotations[annotation.uid] = annotation
        window.chart.update()
    },

    removeAnnotation(uid) {
        if (!confirm('Are you sure you want to remove this range?')) return;

        this.labelAnnotations = this.labelAnnotations.filter((ann) => ann.uid !== uid)
        this.created = Math.max(0, this.created - 1)

        // sync chart
        delete window.chart.options.plugins.annotation.annotations[uid]
        window.chart.update()
    }
}