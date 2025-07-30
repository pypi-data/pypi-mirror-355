import ChartJS from "chart.js/auto"
import ZoomPlugin from "chartjs-plugin-zoom";
import AnnotationPlugin from 'chartjs-plugin-annotation';
import {Chart} from "react-chartjs-2";
import {useState, useEffect, useRef} from "react";

ChartJS.register({ZoomPlugin, AnnotationPlugin});


/**
 *
 */
export default function ChartjsSingle({definition, ...props}) {
    const ref = useRef(null);
    const [def, setDef] = useState(definition);

    useEffect(() => {
        const controller = new AbortController();
        const signal = controller.signal;
        const chart = ref.current

        console.log('chart def', def)
        console.log('chart instance', chart)

        // reset chart on double click
        chart?.canvas.addEventListener("dblclick", () => chart.resetZoom(), {signal});

        // cleanup
        return () => controller.abort()
    }, [])

    return (
        <div className={"chart"}>
            {def.options.extra?.content?.before && (<div dangerouslySetInnerHTML={{ __html: def.options.extra.content.before }} />)}
            <Chart ref={ref} {...def} {...props} />
            {def.options.extra?.content?.after && (<div dangerouslySetInnerHTML={{ __html: def.options.extra.content.after }} />)}
        </div>
    )
}