import { motion } from "framer-motion";

const CONFIDENCE_META: Record<string, { color: string; pct: number }> = {
  High: { color: "#1e7a34", pct: 100 },
  Medium: { color: "#9a6300", pct: 65 },
  Low: { color: "#b3261e", pct: 30 },
};

interface Props {
  label: "High" | "Medium" | "Low";
  reducedMotion: boolean;
}

export function ConfidenceIndicator({ label, reducedMotion }: Props) {
  const meta = CONFIDENCE_META[label] ?? CONFIDENCE_META.Low;

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <span style={{ fontSize: 12, fontWeight: 700, color: meta.color, minWidth: 92 }}>
        {label} confidence
      </span>
      <div
        style={{
          flex: 1,
          maxWidth: 120,
          height: 6,
          borderRadius: 999,
          background: "#e9ecef",
          overflow: "hidden",
        }}
        role="progressbar"
        aria-valuenow={meta.pct}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`${label} confidence`}
      >
        <motion.div
          initial={reducedMotion ? false : { width: 0 }}
          animate={{ width: `${meta.pct}%` }}
          transition={{ duration: reducedMotion ? 0 : 0.6, ease: "easeOut" }}
          style={{ height: "100%", background: meta.color, borderRadius: 999 }}
        />
      </div>
    </div>
  );
}
