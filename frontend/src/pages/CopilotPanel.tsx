import { useState, useEffect, useRef } from "react";
import { Send, Sparkles, Loader2 } from "lucide-react";
import api from "@/lib/api";
import { Card } from "@/components/Card";

type Message = { role: "user" | "assistant"; content: string; citations?: any[]; confidence?: number };

const SUGGESTIONS = [
  "Which vendor is cheapest over 3 years?",
  "Which vendor meets all mandatory requirements?",
  "What are the biggest risks?",
  "Compare vendors A and B.",
  "Why did the top vendor receive that score?",
];

export function CopilotPanel({ projectId, vendorId }: { projectId: string; vendorId?: string }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const send = async (text: string) => {
    if (!text.trim()) return;
    const userMsg: Message = { role: "user", content: text };
    const next = [...messages, userMsg];
    setMessages(next);
    setInput("");
    setLoading(true);
    try {
      const r = await api.post("/copilot/chat", {
        project_id: projectId,
        vendor_id: vendorId,
        messages: next.map(({ role, content }) => ({ role, content })),
      });
      setMessages([...next, {
        role: "assistant",
        content: r.data.answer,
        citations: r.data.citations,
        confidence: r.data.confidence,
      }]);
    } catch (e: any) {
      setMessages([...next, { role: "assistant", content: "Sorry, I couldn't answer that. " + (e?.response?.data?.detail || "") }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="p-0 overflow-hidden flex flex-col h-[600px]">
      <div className="px-4 py-3 border-b border-slate-200 flex items-center gap-2">
        <Sparkles className="w-4 h-4 text-accent-600" />
        <div className="font-semibold text-sm">AI Copilot</div>
        <div className="text-xs text-slate-500">Answers are grounded in your project data</div>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-slate-50">
        {messages.length === 0 && (
          <div>
            <div className="text-sm text-slate-500 mb-3">Try asking:</div>
            <div className="flex flex-wrap gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className="text-xs px-3 py-1.5 rounded-full bg-white border border-slate-200 hover:border-accent-500 hover:text-accent-600 transition"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[80%] rounded-2xl px-4 py-2 text-sm whitespace-pre-wrap ${
              m.role === "user" ? "bg-brand-800 text-white" : "bg-white border border-slate-200 text-slate-800"
            }`}>
              {m.content}
              {m.citations && m.citations.length > 0 && (
                <div className="mt-2 pt-2 border-t border-slate-200 text-xs text-slate-500">
                  <div className="font-semibold text-slate-600">Sources:</div>
                  {m.citations.map((c: any, idx: number) => (
                    <div key={idx} className="mt-0.5">
                      📄 {c.document || "Document"}{c.page ? `, p. ${c.page}` : ""}{c.section ? `, ${c.section}` : ""}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-slate-200 rounded-2xl px-4 py-2 text-sm text-slate-500 flex items-center gap-2">
              <Loader2 className="w-3 h-3 animate-spin" /> Thinking…
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <div className="p-3 border-t border-slate-200 flex items-center gap-2">
        <input
          className="input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask the AI copilot…"
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send(input)}
          disabled={loading}
        />
        <button className="btn-primary" onClick={() => send(input)} disabled={loading || !input.trim()}>
          <Send className="w-4 h-4" />
        </button>
      </div>
    </Card>
  );
}
