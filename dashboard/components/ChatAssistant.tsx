"use client";

import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import {
  Bot,
  ChevronDown,
  ChevronUp,
  MessageCircle,
  Send,
  User,
  X,
} from "lucide-react";
import { useTranslations } from "next-intl";
import { clsx } from "clsx";
import { sendChatMessage, type ChatContextUsed } from "@/lib/api";

interface Props {
  district: string;
  season: string;
  year: number;
  /** True once the dashboard has an actual prediction for this
   * district/season/year — the assistant is grounded in server-computed
   * data either way, but there's nothing meaningful to ask about yet. */
  hasPrediction: boolean;
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  contextUsed?: ChatContextUsed;
}

/**
 * Context-Aware XAI chat panel. Every answer comes from POST /api/chat,
 * which grounds the model in the current prediction/SHAP/historical data
 * for the selected district/season/year — never a general-knowledge reply.
 * The "based on this data" section makes that traceable rather than a
 * black box.
 *
 * Rendered as a floating action button, fixed to the bottom-right corner
 * above the rest of the page — the panel below only mounts while `isOpen`,
 * as a `fixed`-positioned popup, so it never occupies space in (or pushes
 * around) the prediction page's grid layout.
 */
export default function ChatAssistant({
  district,
  season,
  year,
  hasPrediction,
}: Props) {
  const t = useTranslations("chat");
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Old answers describe a different location's data once the selection
  // changes — drop them rather than let them linger next to a new context.
  useEffect(() => {
    setMessages([]);
    setError(null);
    setExpandedIndex(null);
  }, [district, season, year]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [messages, loading]);

  const canAsk = Boolean(district && season && hasPrediction);

  const handleSend = async () => {
    const query = input.trim();
    if (!query || !canAsk || loading) return;

    setMessages((prev) => [...prev, { role: "user", content: query }]);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const res = await sendChatMessage({ query, district, season, year });
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: res.answer,
          contextUsed: res.context_used,
        },
      ]);
    } catch (err) {
      console.error("Chat request failed:", err);
      setError(t("error"));
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void handleSend();
    }
  };

  return (
    <>
      {/* Floating action button — fixed above all dashboard content, always
          visible regardless of scroll position. This is the only element in
          this file actually present during hydration (the popup below only
          mounts once `isOpen` flips true via a client click, well after
          hydration completes, so nothing inside it can hit a hydration
          mismatch). suppressHydrationWarning: autofill/password-manager
          browser extensions stamp fdprocessedid="..." onto every <button>
          they scan post-mount, which React otherwise reports as a mismatch
          even though nothing here renders differently server vs. client —
          see LanguageSwitcher.tsx/Navbar.tsx for the same, already-confirmed
          case. */}
      <button
        type="button"
        onClick={() => setIsOpen((v) => !v)}
        title={t("title")}
        aria-label={t("title")}
        aria-expanded={isOpen}
        className="fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-emerald-600 text-white shadow-lg transition-transform hover:scale-105 hover:bg-emerald-700 active:scale-95"
        suppressHydrationWarning
      >
        {isOpen ? <X size={24} /> : <MessageCircle size={24} />}
      </button>

      {/* Popup panel — only mounted while open, positioned above the button
          via `fixed`, so it never affects the page's normal-flow layout. */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 z-50 flex h-112 max-h-[70vh] w-[calc(100vw-3rem)] max-w-sm flex-col rounded-3xl border border-slate-200 bg-white shadow-2xl">
          <div className="flex items-start justify-between gap-2 border-b border-slate-100 p-5">
            <div>
              <h3 className="text-lg font-bold text-slate-900">{t("title")}</h3>
              <p className="mt-1 text-xs leading-relaxed text-slate-500">
                {t("subtitle")}
              </p>
            </div>
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              aria-label={t("close")}
              className="shrink-0 rounded-lg p-1 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600"
            >
              <X size={18} />
            </button>
          </div>

          <div className="flex-1 space-y-4 overflow-y-auto p-5">
            {messages.length === 0 && (
              <p className="text-sm text-slate-400">
                {canAsk ? t("emptyState") : t("needsPrediction")}
              </p>
            )}

            {messages.map((msg, i) => (
              <div
                key={i}
                className={clsx(
                  "flex",
                  msg.role === "user" ? "justify-end" : "justify-start",
                )}
              >
                <div
                  className={clsx(
                    "max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
                    msg.role === "user"
                      ? "bg-emerald-600 text-white"
                      : "border border-slate-200 bg-slate-50 text-slate-800",
                  )}
                >
                  <div className="mb-1 flex items-center gap-1.5 opacity-60">
                    {msg.role === "user" ? (
                      <User size={11} />
                    ) : (
                      <Bot size={11} />
                    )}
                  </div>
                  <p className="whitespace-pre-wrap">{msg.content}</p>

                  {msg.role === "assistant" && msg.contextUsed && (
                    <div className="mt-2 border-t border-slate-200 pt-2">
                      <button
                        type="button"
                        onClick={() =>
                          setExpandedIndex(expandedIndex === i ? null : i)
                        }
                        className="flex items-center gap-1 text-[11px] font-semibold text-emerald-700 transition-colors hover:text-emerald-800"
                      >
                        {expandedIndex === i ? (
                          <ChevronUp size={12} />
                        ) : (
                          <ChevronDown size={12} />
                        )}
                        <span>{t("basedOnData")}</span>
                      </button>

                      {expandedIndex === i && (
                        <div className="mt-2 space-y-1.5 rounded-xl bg-white p-3 text-[11px] leading-relaxed text-slate-600">
                          {msg.contextUsed.error ? (
                            <p className="text-red-600">
                              {msg.contextUsed.error}
                            </p>
                          ) : (
                            <>
                              {msg.contextUsed.predicted_yield_MT_per_Ha !==
                                undefined && (
                                <p>
                                  <span className="font-semibold text-slate-700">
                                    {t("dataPrediction")}:
                                  </span>{" "}
                                  {msg.contextUsed.predicted_yield_MT_per_Ha}{" "}
                                  MT/Ha
                                </p>
                              )}
                              {msg.contextUsed.confidence_lower !==
                                undefined && (
                                <p>
                                  <span className="font-semibold text-slate-700">
                                    {t("dataConfidence")}:
                                  </span>{" "}
                                  {msg.contextUsed.confidence_lower}–
                                  {msg.contextUsed.confidence_upper} MT/Ha
                                </p>
                              )}
                              {msg.contextUsed.top_shap_features &&
                                msg.contextUsed.top_shap_features.length >
                                  0 && (
                                  <p>
                                    <span className="font-semibold text-slate-700">
                                      {t("dataTopFactors")}:
                                    </span>{" "}
                                    {msg.contextUsed.top_shap_features
                                      .map(
                                        (f) =>
                                          `${f.feature} (${
                                            f.shap_value > 0 ? "+" : ""
                                          }${f.shap_value})`,
                                      )
                                      .join(", ")}
                                  </p>
                                )}
                              {msg.contextUsed.historical_baseline?.mean !==
                                undefined && (
                                <p>
                                  <span className="font-semibold text-slate-700">
                                    {t("dataBaseline")}:
                                  </span>{" "}
                                  {msg.contextUsed.historical_baseline.mean}{" "}
                                  MT/Ha (
                                  {msg.contextUsed.historical_baseline.n_years}{" "}
                                  seasons)
                                </p>
                              )}
                              {msg.contextUsed.recent_yield_history &&
                                msg.contextUsed.recent_yield_history.length >
                                  0 && (
                                  <p>
                                    <span className="font-semibold text-slate-700">
                                      {t("dataHistory")}:
                                    </span>{" "}
                                    {msg.contextUsed.recent_yield_history
                                      .map(
                                        (h) =>
                                          `${h.year}: ${h.yield_MT_per_Ha}`,
                                      )
                                      .join(", ")}
                                  </p>
                                )}
                            </>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start">
                <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm text-slate-500">
                  {t("thinking")}
                </div>
              </div>
            )}

            {error && (
              <p className="text-xs font-medium text-red-600">{error}</p>
            )}

            <div ref={bottomRef} />
          </div>

          <div className="flex items-center gap-2 border-t border-slate-100 p-4">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={!canAsk || loading}
              placeholder={t("placeholder")}
              className="flex-1 rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-emerald-500 disabled:bg-slate-50 disabled:text-slate-400"
            />
            <button
              type="button"
              onClick={() => void handleSend()}
              disabled={!canAsk || loading || !input.trim()}
              aria-label={t("send")}
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-emerald-600 text-white transition-colors hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Send size={16} />
            </button>
          </div>
        </div>
      )}
    </>
  );
}
