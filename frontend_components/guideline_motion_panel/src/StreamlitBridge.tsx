import { useEffect, useRef, useState } from "react";
import {
  Streamlit,
  RenderData,
} from "streamlit-component-lib";
import GuidancePanel from "./GuidancePanel";
import type { MotionPanelPayload } from "./types";

export default function StreamlitBridge() {
  const [payload, setPayload] = useState<MotionPanelPayload | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onRender(event: Event) {
      const data = (event as CustomEvent<RenderData>).detail;
      const args = data?.args ?? {};
      setPayload((args.payload as MotionPanelPayload) ?? null);
    }

    Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender);
    Streamlit.setComponentReady();

    return () => {
      Streamlit.events.removeEventListener(Streamlit.RENDER_EVENT, onRender);
    };
  }, []);

  useEffect(() => {
    // Keep the iframe sized to fit content (Framer Motion height changes on expand/collapse).
    if (!containerRef.current) return;
    const resizeObserver = new ResizeObserver(() => {
      Streamlit.setFrameHeight(containerRef.current?.scrollHeight ?? 400);
    });
    resizeObserver.observe(containerRef.current);
    Streamlit.setFrameHeight(containerRef.current.scrollHeight);
    return () => resizeObserver.disconnect();
  }, [payload]);

  return (
    <div ref={containerRef}>
      {payload ? (
        <GuidancePanel payload={payload} />
      ) : (
        <div style={{ fontSize: 13, color: "#5b6570", padding: 8 }}>Waiting for guidance data…</div>
      )}
    </div>
  );
}
