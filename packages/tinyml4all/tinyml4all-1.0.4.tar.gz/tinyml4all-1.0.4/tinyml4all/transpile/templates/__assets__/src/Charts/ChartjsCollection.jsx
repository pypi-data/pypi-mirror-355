import {useState, useEffect, useRef} from "react";
import Single from "./ChartjsSingle.jsx";


/**
 *
 */
export default function App() {
    const [charts, setCharts] = useState(window.charts || []);

    useEffect(() => {
        const controller = new AbortController();
        const signal = controller.signal;

        window.addEventListener("updateCharts", (ev) => {
            console.log('updateCharts', ev.detail.charts)
            setCharts(ev.detail.charts);
        }, {signal})

        return () => controller.abort();
    })

    return (
        <div className={"flex flex-col space-y-8 [&>div]:py-8 [&>div+div]:border-t [&>div+div]:border-slate-300"}>
            {charts.map(chart => <Single definition={chart} />)}
        </div>
    )
}