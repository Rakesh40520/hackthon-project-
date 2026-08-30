import { ProgressBar } from "./ProgressBar";
import type { AnalysisJob } from "@/types";
import { CheckCircle2, Loader2 } from "lucide-react";

const STAGES = [
  { key: "UPLOAD", label: "Uploading" },
  { key: "EXTRACT", label: "Extracting document" },
  { key: "ANALYZE", label: "Analyzing content" },
  { key: "EVALUATE_REQUIREMENTS", label: "Checking requirements" },
  { key: "ANALYZE_RISKS", label: "Detecting risks" },
  { key: "SCORE", label: "Calculating score" },
  { key: "RECOMMEND", label: "Finalizing" },
];

export function AnalysisProgress({ job }: { job?: AnalysisJob }) {
  if (!job) return null;
  const idx = STAGES.findIndex((s) => s.key === job.current_stage);
  return (
    <div>
      <ProgressBar value={job.progress} label={job.stage_message || "Working..."} />
      <div className="mt-4 grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-2 text-xs">
        {STAGES.map((s, i) => {
          const done = i < idx || job.status === "COMPLETED";
          const active = i === idx && job.status === "RUNNING";
          return (
            <div
              key={s.key}
              className={`flex items-center gap-2 p-2 rounded-lg ${
                done ? "bg-emerald-50 text-emerald-700" : active ? "bg-blue-50 text-blue-700" : "bg-slate-50 text-slate-500"
              }`}
            >
              {done ? <CheckCircle2 className="w-3 h-3" /> : active ? <Loader2 className="w-3 h-3 animate-spin" /> : <span className="w-3 h-3 inline-block rounded-full bg-slate-200" />}
              <span>{s.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
