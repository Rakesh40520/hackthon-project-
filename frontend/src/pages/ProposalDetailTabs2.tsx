import { Card, CardHeader } from "@/components/Card";
import { ScoreRing } from "@/components/ScoreRing";
import { StatusBadge } from "@/components/StatusBadge";
import { EmptyState } from "@/components/EmptyState";
import { AlertTriangle } from "lucide-react";

function Row({ label, value, currency }: { label: string; value: any; currency?: string }) {
  return (
    <div className="flex justify-between">
      <dt className="text-slate-500">{label}</dt>
      <dd className="font-medium">
        {value !== null && value !== undefined
          ? (typeof value === "number" ? `${currency || ""} ${value.toLocaleString()}` : value)
          : "—"}
      </dd>
    </div>
  );
}

export function Overview({ data, onExport }: any) {
  return (
    <div className="space-y-5">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <Card>
          <CardHeader title="Summary" />
          <div className="space-y-2 text-sm">
            {data.recommendation ? (
              <>
                <div className="font-medium">{data.recommendation.summary}</div>
                <div className="text-slate-600">{data.recommendation.reasoning}</div>
                <div className="mt-3 flex items-center gap-2">
                  <StatusBadge status={data.recommendation.decision} />
                  {data.recommendation.recommended ? <StatusBadge status="RECOMMENDED" /> : null}
                </div>
              </>
            ) : <div className="text-slate-500">Awaiting analysis…</div>}
          </div>
        </Card>
        <Card>
          <CardHeader title="Score Breakdown" />
          {data.score ? (
            <div className="grid grid-cols-3 gap-3">
              {data.score.components.map((c: any) => (
                <div key={c.name} className="text-center">
                  <ScoreRing value={c.raw_score} size={64} label={c.name} />
                  <div className="text-[10px] text-slate-500 mt-1">weight {Math.round(c.weight * 100)}%</div>
                </div>
              ))}
            </div>
          ) : <EmptyState title="No score yet" />}
        </Card>
      </div>

      {data.score?.ineligibility_reasons?.length ? (
        <Card>
          <CardHeader title="Eligibility Issues" icon={<AlertTriangle className="w-4 h-4 text-red-500" />} />
          <ul className="text-sm text-red-700 list-disc pl-5 space-y-1">
            {data.score.ineligibility_reasons.map((r: string, i: number) => <li key={i}>{r}</li>)}
          </ul>
        </Card>
      ) : null}

      <div className="flex gap-2">
        <button className="btn-secondary" onClick={() => onExport("pdf")}>Export PDF</button>
        <button className="btn-secondary" onClick={() => onExport("xlsx")}>Export Excel</button>
      </div>
    </div>
  );
}

export function Requirements({ data }: any) {
  return (
    <Card padded={false}>
      <table className="w-full text-sm">
        <thead className="text-xs text-slate-500 border-b border-slate-200">
          <tr>
            <th className="text-left p-3">Requirement</th>
            <th className="text-left p-3">Status</th>
            <th className="text-left p-3">Score</th>
            <th className="text-left p-3">Reason</th>
          </tr>
        </thead>
        <tbody>
          {data.evaluations.map((e: any) => (
            <tr key={e.id} className="border-b border-slate-100 align-top">
              <td className="p-3 font-medium">{e.requirement_name}</td>
              <td className="p-3"><StatusBadge status={e.status} /></td>
              <td className="p-3">{Math.round(e.score)}</td>
              <td className="p-3 text-slate-600 text-xs">
                {e.reason}
                {e.evidence_quote ? (
                  <div className="mt-1 italic text-slate-500 border-l-2 border-slate-200 pl-2">"{e.evidence_quote}"</div>
                ) : null}
              </td>
            </tr>
          ))}
          {!data.evaluations.length && <tr><td colSpan={4} className="p-6 text-center text-slate-500">No evaluations yet.</td></tr>}
        </tbody>
      </table>
    </Card>
  );
}

export function Pricing({ data }: any) {
  const p = data.pricing;
  if (!p) return <EmptyState title="No pricing extracted" />;
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
      <Card>
        <CardHeader title="Totals" />
        <dl className="text-sm space-y-2">
          <Row label="Year 1" value={p.year1_total} currency={p.currency} />
          <Row label="Year 3" value={p.year3_total} currency={p.currency} />
          <Row label="Year 5" value={p.year5_total} currency={p.currency} />
          <Row label="Recurring Annual" value={p.recurring_annual_cost} currency={p.currency} />
          <Row label="Implementation" value={p.implementation_cost} currency={p.currency} />
          <Row label="License" value={p.license_cost} currency={p.currency} />
          <Row label="Support" value={p.support_cost} currency={p.currency} />
          <Row label="Training" value={p.training_cost} currency={p.currency} />
          <Row label="Migration" value={p.migration_cost} currency={p.currency} />
          <Row label="Additional" value={p.additional_fees} currency={p.currency} />
          <Row label="Discounts" value={p.discounts} currency={p.currency} />
          <Row label="Price Escalation" value={p.price_escalation_pct ? `${p.price_escalation_pct}%` : "—"} />
        </dl>
      </Card>
      <Card>
        <CardHeader title="Assumptions" />
        <ul className="text-sm list-disc pl-5 space-y-1 text-slate-600">
          {(p.assumptions?.assumptions || []).map((a: string, i: number) => <li key={i}>{a}</li>)}
          {!p.assumptions?.assumptions?.length && <li>No explicit assumptions recorded.</li>}
        </ul>
        {p.notes ? <div className="mt-3 text-xs text-slate-500">{p.notes}</div> : null}
      </Card>
    </div>
  );
}

export function Risks({ data }: any) {
  return (
    <div className="space-y-3">
      {data.risks.length === 0 && <EmptyState title="No risks detected" />}
      {data.risks.map((r: any) => (
        <Card key={r.id}>
          <div className="flex items-start justify-between">
            <div>
              <div className="font-semibold text-sm">{r.title}</div>
              <div className="text-xs text-slate-500">{r.category}</div>
            </div>
            <StatusBadge status={r.severity} />
          </div>
          <p className="mt-2 text-sm text-slate-600">{r.description}</p>
          {r.evidence_quote ? <div className="mt-2 text-xs italic text-slate-500 border-l-2 border-slate-200 pl-2">"{r.evidence_quote}"</div> : null}
          {r.recommendation ? <div className="mt-2 text-xs text-blue-700">Recommendation: {r.recommendation}</div> : null}
        </Card>
      ))}
    </div>
  );
}

export function Missing({ data }: any) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
      <Card>
        <CardHeader title="Missing Information" />
        <div className="space-y-2">
          {data.missing_info.length === 0 && <div className="text-sm text-slate-500">No missing items.</div>}
          {data.missing_info.map((m: any) => (
            <div key={m.id} className="border border-slate-100 rounded-lg p-3">
              <div className="flex items-center justify-between">
                <div className="text-sm font-medium">{m.field_name}</div>
                <StatusBadge status={m.importance} />
              </div>
              {m.why_it_matters ? <div className="text-xs text-slate-500 mt-1">{m.why_it_matters}</div> : null}
            </div>
          ))}
        </div>
      </Card>
      <Card>
        <CardHeader title="Clarification Questions" />
        <ul className="space-y-2 text-sm list-decimal pl-5">
          {data.clarification_questions.length === 0 && <li className="text-slate-500 list-none">No questions yet.</li>}
          {data.clarification_questions.map((c: any) => <li key={c.id}>{c.question}</li>)}
        </ul>
      </Card>
    </div>
  );
}
