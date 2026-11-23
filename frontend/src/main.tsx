import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Aperture,
  MessageSquare,
  Library,
  History,
  BarChart3,
  Plus,
  Search,
  Send,
  FileText,
  X,
  Check,
  LoaderCircle,
  Copy,
  ThumbsUp,
  ThumbsDown,
  BookOpen,
  ShieldCheck,
  Sparkles,
  Upload,
  Trash2,
  ChevronRight,
  Download,
  CircleHelp,
  Layers,
  Clock3,
  CircleAlert,
  FlaskConical,
  ExternalLink,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { api, json } from "./api";
import type { Answer, Doc, Health, Stats, Report } from "./api";
import "./styles.css";

type Tab = "copilot" | "knowledge" | "history" | "evaluation";
const tabs: { id: Tab; label: string; icon: LucideIcon }[] = [
  { id: "copilot", label: "Support copilot", icon: MessageSquare },
  { id: "knowledge", label: "Knowledge base", icon: Library },
  { id: "history", label: "Conversations", icon: History },
  { id: "evaluation", label: "Evaluation lab", icon: BarChart3 },
];
const examples = [
  "Can I return an unused item after 20 days?",
  "How do I reset my password?",
  "How much does express shipping cost?",
];
const percent = (n: number) => `${Math.round(n * 100)}%`;
const date = (value: string) =>
  new Date(
    value.endsWith("Z") || /[+-]\d\d:\d\d$/.test(value) ? value : `${value}Z`,
  ).toLocaleDateString(undefined, { month: "short", day: "numeric" });

function App() {
  const [tab, setTab] = useState<Tab>("copilot");
  const [health, setHealth] = useState<Health | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [docs, setDocs] = useState<Doc[]>([]);
  const [history, setHistory] = useState<Answer[]>([]);
  const [question, setQuestion] = useState("");
  const [method, setMethod] = useState("hybrid");
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [selectedSource, setSelectedSource] = useState(0);
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");
  const [modal, setModal] = useState<"add" | "guide" | null>(null);
  const [viewDoc, setViewDoc] = useState<Doc | null>(null);
  const [report, setReport] = useState<Report | null>(null);
  const [evaluating, setEvaluating] = useState(false);
  const [search, setSearch] = useState("");
  const [caseMethod, setCaseMethod] = useState(1);
  const questionRef = useRef<HTMLTextAreaElement>(null);

  async function refresh() {
    try {
      const [h, s, d, c] = await Promise.all([
        api<Health>("/health"),
        api<Stats>("/stats"),
        api<Doc[]>("/documents"),
        api<Answer[]>("/conversations"),
      ]);
      setHealth(h);
      setStats(s);
      setDocs(d);
      setHistory(c);
    } catch (e) {
      setError((e as Error).message);
    }
  }
  useEffect(() => {
    void refresh();
  }, []);
  useEffect(() => {
    if (toast) {
      const id = setTimeout(() => setToast(""), 3500);
      return () => clearTimeout(id);
    }
  }, [toast]);

  async function ask(event?: React.FormEvent, text = question) {
    event?.preventDefault();
    if (asking || text.trim().length < 3) return;
    setQuestion(text);
    setAsking(true);
    setError("");
    setTab("copilot");
    try {
      const result = await api<Answer>(
        "/questions",
        json({ question: text, method }),
      );
      setAnswer(result);
      setSelectedSource(0);
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setAsking(false);
    }
  }
  async function feedback(value: string) {
    if (!answer) return;
    try {
      await api(
        `/conversations/${answer.id}/feedback`,
        json({ feedback: value }, "PUT"),
      );
      setAnswer({ ...answer, feedback: value });
      setToast("Feedback saved. Thank you.");
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    }
  }
  async function openDocument(id: string) {
    try {
      setViewDoc(await api<Doc>(`/documents/${id}`));
    } catch (e) {
      setError((e as Error).message);
    }
  }
  async function deleteDocument(doc: Doc) {
    if (
      !window.confirm(
        `Delete “${doc.title}” from the knowledge base? Saved conversations keep their source snapshots.`,
      )
    )
      return;
    try {
      await api(`/documents/${doc.id}`, { method: "DELETE" });
      setToast("Document deleted.");
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    }
  }
  async function evaluate() {
    setEvaluating(true);
    setError("");
    try {
      setReport(await api<Report>("/evaluations", { method: "POST" }));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setEvaluating(false);
    }
  }
  async function copyAnswer() {
    if (!answer) return;
    try {
      await navigator.clipboard.writeText(answer.answer);
      setToast("Answer copied.");
    } catch {
      setError(
        "Clipboard access is unavailable. You can select and copy the answer text.",
      );
    }
  }
  function downloadReport() {
    if (!report) return;
    const url = URL.createObjectURL(
      new Blob([JSON.stringify(report, null, 2)], { type: "application/json" }),
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = "supportlens-evaluation.json";
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  function showAnswer(item: Answer) {
    setAnswer(item);
    setQuestion(item.question);
    setSelectedSource(0);
    setTab("copilot");
  }
  const active = tabs.find((t) => t.id === tab)!;
  const local = !health || health.answer_provider === "extractive";

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a
          className="brand"
          href="#"
          onClick={(e) => {
            e.preventDefault();
            setTab("copilot");
          }}
        >
          <span className="brand-mark">
            <Aperture size={25} strokeWidth={1.8} />
          </span>
          <span>
            supportlens<span className="brand-period">.</span>
          </span>
        </a>
        <div className="workspace">
          <span className="workspace-avatar">SL</span>
          <div>
            <strong>My workspace</strong>
            <span>Personal project</span>
          </div>
          <span className="small-tag">LOCAL</span>
        </div>
        <div className="nav-label">WORKSPACE</div>
        <nav aria-label="Main navigation">
          {tabs.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              className={`nav-item ${tab === id ? "active" : ""}`}
              onClick={() => {
                setTab(id);
                setError("");
              }}
              aria-current={tab === id ? "page" : undefined}
            >
              <Icon size={19} />
              <span>{label}</span>
              {id === "knowledge" && stats && (
                <span className="nav-count">{stats.documents}</span>
              )}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="mode-card">
            <div className="mode-icon">
              <ShieldCheck size={19} />
            </div>
            <strong>{local ? "Local evidence mode" : "AI draft mode"}</strong>
            <p>
              {local
                ? "Your documents stay on your computer. No API key needed."
                : `Drafting with ${health?.model}. Review every answer.`}
            </p>
            <span className="mode-caption">
              {health ? health.retrieval_mode : "Connecting to local server"}
            </span>
          </div>
          <button className="help-button" onClick={() => setModal("guide")}>
            <CircleHelp size={18} /> How it works
          </button>
          <div className="sidebar-footer">
            <span className="user-avatar">YOU</span>
            <span>
              Built to be understood<small>SupportLens · v0.2</small>
            </span>
          </div>
        </div>
      </aside>

      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumb">
            Workspace <ChevronRight size={14} />
            <strong>{active.label}</strong>
          </div>
          <span className="private-label">
            <ShieldCheck size={15} /> Local workspace
          </span>
        </header>
        <main>
          {error && (
            <div role="alert" className="alert error">
              <CircleAlert size={19} />
              <span>{error}</span>
              <button aria-label="Dismiss error" onClick={() => setError("")}>
                <X size={16} />
              </button>
            </div>
          )}
          <div className="page-heading">
            <div>
              <div className="eyebrow">
                {tab === "copilot"
                  ? "A LITTLE CONTEXT. A BETTER ANSWER."
                  : tab === "knowledge"
                    ? "THE SOURCE OF GOOD SUPPORT"
                    : tab === "evaluation"
                      ? "MEASURE. COMPARE. IMPROVE."
                      : "A RECORD YOU CAN REVISIT"}
              </div>
              <h1>
                {tab === "copilot"
                  ? "Support, with substance."
                  : tab === "knowledge"
                    ? "Your knowledge base."
                    : tab === "evaluation"
                      ? "Evidence over assumptions."
                      : "Every conversation, saved."}
              </h1>
              <p>
                {tab === "copilot"
                  ? "Turn your documentation into answers you can stand behind."
                  : tab === "knowledge"
                    ? "Give your copilot the information it needs to be helpful."
                    : tab === "evaluation"
                      ? "See what works, where it fails, and what to improve next."
                      : "Revisit answers, inspect sources, and keep learning."}
              </p>
            </div>
            <button
              className="button secondary"
              onClick={() => setModal("add")}
            >
              <Plus size={17} /> Add documents
            </button>
          </div>

          {tab === "copilot" && (
            <>
              <section className="stats-grid" aria-label="Workspace overview">
                <Stat
                  icon={Library}
                  label="Knowledge sources"
                  value={stats?.documents}
                  detail="Documents in your library"
                />
                <Stat
                  icon={Layers}
                  label="Searchable passages"
                  value={stats?.chunks}
                  detail="Ready to retrieve and cite"
                />
                <Stat
                  icon={MessageSquare}
                  label="Questions explored"
                  value={stats?.questions}
                  detail="Saved in your conversations"
                />
              </section>
              <div className="copilot-grid">
                <section className="panel conversation-panel">
                  <div className="panel-heading">
                    <div>
                      <span className="icon-tile">
                        <Sparkles size={19} />
                      </span>
                      <h2>Support copilot</h2>
                    </div>
                    <span className="pill">
                      {local ? "Source excerpts" : "AI drafts"}
                    </span>
                  </div>
                  <div
                    className={`conversation-body ${answer ? "has-answer" : ""}`}
                    aria-live="polite"
                    aria-busy={asking}
                  >
                    {!answer && !asking ? (
                      <div className="welcome">
                        <div className="welcome-mark">
                          <Aperture size={37} strokeWidth={1.3} />
                        </div>
                        <h2>Let's find a well-supported answer.</h2>
                        <p>
                          Ask a customer question. I'll find the relevant
                          passages
                          <br className="desktop-break" /> and keep the evidence
                          close at hand.
                        </p>
                        <div className="suggestion-list">
                          {examples.map((q, i) => (
                            <button
                              key={q}
                              onClick={() => void ask(undefined, q)}
                            >
                              <span className="suggestion-icon">
                                {i === 0 ? (
                                  <History size={17} />
                                ) : i === 1 ? (
                                  <ShieldCheck size={17} />
                                ) : (
                                  <Upload size={17} />
                                )}
                              </span>
                              {q}
                              <ChevronRight size={16} />
                            </button>
                          ))}
                        </div>
                        <span className="sample-note">
                          Try the included sample store policies, or add your
                          own.
                        </span>
                      </div>
                    ) : asking ? (
                      <div className="thinking">
                        <LoaderCircle className="spin" size={28} />
                        <h3>Finding the evidence…</h3>
                        <p>
                          {local
                            ? "Searching your documents and checking relevance."
                            : "Retrieving sources and drafting a response. This may take a minute."}
                        </p>
                      </div>
                    ) : (
                      answer && (
                        <>
                          <div className="question-bubble">
                            <span className="tiny-label">
                              CUSTOMER QUESTION
                            </span>
                            <p>{answer.question}</p>
                          </div>
                          <div className="answer-heading">
                            <span className="answer-avatar">
                              <Aperture size={20} />
                            </span>
                            <strong>
                              {answer.mode === "ollama"
                                ? "Suggested reply"
                                : answer.mode === "insufficient_evidence"
                                  ? "More information needed"
                                  : "Relevant source excerpts"}
                            </strong>
                          </div>
                          <div className="answer-text">
                            {answer.answer.split(/(\[\d+\])/g).map((part, i) =>
                              /^\[\d+\]$/.test(part) ? (
                                <button
                                  key={i}
                                  className="citation"
                                  onClick={() =>
                                    setSelectedSource(
                                      Number(part.slice(1, -1)) - 1,
                                    )
                                  }
                                  aria-label={`Show source ${part}`}
                                >
                                  {part}
                                </button>
                              ) : (
                                <React.Fragment key={i}>{part}</React.Fragment>
                              ),
                            )}
                          </div>
                          {answer.notice && (
                            <div className="review-note">
                              <ShieldCheck size={16} />
                              <span>{answer.notice}</span>
                            </div>
                          )}
                          <div className="answer-meta">
                            <span className="pill neutral">
                              {answer.classification.label}
                            </span>
                            <span>
                              <Clock3 size={13} />
                              {answer.latency_ms < 1000
                                ? `${Math.round(answer.latency_ms)} ms`
                                : `${(answer.latency_ms / 1000).toFixed(1)} s`}
                            </span>
                            <span>
                              {answer.citation_ids.length} cited sources
                            </span>
                          </div>
                          <div className="answer-actions">
                            <button
                              className="text-button"
                              onClick={() => void copyAnswer()}
                            >
                              <Copy size={15} />
                              Copy text
                            </button>
                            <div>
                              <span>Was this useful?</span>
                              <button
                                className={`icon-button ${answer.feedback === "helpful" ? "selected" : ""}`}
                                aria-label="Mark helpful"
                                onClick={() => void feedback("helpful")}
                              >
                                <ThumbsUp size={16} />
                              </button>
                              <button
                                className={`icon-button ${answer.feedback === "unhelpful" ? "selected" : ""}`}
                                aria-label="Mark unhelpful"
                                onClick={() => void feedback("unhelpful")}
                              >
                                <ThumbsDown size={16} />
                              </button>
                            </div>
                          </div>
                        </>
                      )
                    )}
                  </div>
                  <form className="composer" onSubmit={ask}>
                    <label className="sr-only" htmlFor="question">
                      Customer question
                    </label>
                    <textarea
                      id="question"
                      ref={questionRef}
                      value={question}
                      onChange={(e) => setQuestion(e.target.value)}
                      maxLength={2000}
                      placeholder="Ask a question about your documents…"
                      rows={2}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" && !e.shiftKey) {
                          e.preventDefault();
                          void ask();
                        }
                      }}
                    />
                    <div className="composer-bottom">
                      <label className="search-method">
                        <Search size={14} />
                        <select
                          aria-label="Retrieval method"
                          value={method}
                          onChange={(e) => setMethod(e.target.value)}
                        >
                          <option value="hybrid">Hybrid search</option>
                          <option value="bm25">Keyword search</option>
                        </select>
                      </label>
                      <button
                        className="button primary ask-button"
                        disabled={asking || question.trim().length < 3}
                        type="submit"
                      >
                        {asking ? (
                          <LoaderCircle className="spin" size={17} />
                        ) : (
                          <Send size={16} />
                        )}
                        <span>Find answer</span>
                      </button>
                    </div>
                  </form>
                  <p className="composer-caption">
                    {local
                      ? "Evidence mode quotes source text. Connect Ollama for AI-written replies."
                      : "AI can make mistakes. Review the cited evidence before sending a reply."}
                  </p>
                </section>
                <aside className="evidence-column">
                  <section className="panel evidence-panel">
                    <div className="panel-heading">
                      <div>
                        <BookOpen size={19} />
                        <h2>The evidence</h2>
                      </div>
                      {answer && (
                        <span className="number-badge">
                          {answer.sources.length}
                        </span>
                      )}
                    </div>
                    {answer?.sources.length ? (
                      <div className="sources-list">
                        {answer.sources.map((source, i) => (
                          <article
                            key={source.id}
                            className={`source-card ${selectedSource === i ? "expanded" : ""}`}
                          >
                            <button
                              className="source-summary"
                              onClick={() => setSelectedSource(i)}
                              aria-expanded={selectedSource === i}
                            >
                              <span className="source-number">{i + 1}</span>
                              <span>
                                <strong>{source.title}</strong>
                                <small>
                                  Passage {source.position + 1} ·{" "}
                                  {source.filename}
                                </small>
                              </span>
                              <ChevronRight size={15} />
                            </button>
                            {selectedSource === i && (
                              <div className="source-content">
                                <p>{source.text}</p>
                                <span className="source-status">
                                  {answer.citation_ids.includes(i + 1)
                                    ? "Cited in this answer"
                                    : "Retrieved for context"}
                                </span>
                              </div>
                            )}
                          </article>
                        ))}
                      </div>
                    ) : (
                      <div className="evidence-empty">
                        <div className="document-illustration">
                          <FileText size={34} strokeWidth={1.2} />
                          <span>
                            <Search size={16} />
                          </span>
                        </div>
                        <h3>
                          {answer
                            ? "No matching evidence"
                            : "Sources, not guesswork."}
                        </h3>
                        <p>
                          {answer
                            ? "Add a relevant document or try a more specific question."
                            : "Relevant passages will appear here when you ask a question."}
                        </p>
                        <div className="evidence-check">
                          <Check size={14} /> Inspect every cited passage
                        </div>
                      </div>
                    )}
                  </section>
                  <section className="principle-card">
                    <div className="eyebrow">BUILT FOR TRUST</div>
                    <h3>
                      A useful answer
                      <br />
                      shows its work.
                    </h3>
                    <p>
                      Source links, clear limitations, and a human in the loop.
                      That's the idea.
                    </p>
                    <button
                      className="text-button"
                      onClick={() => setModal("guide")}
                    >
                      Explore how it works <ChevronRight size={15} />
                    </button>
                  </section>
                </aside>
              </div>
            </>
          )}

          {tab === "knowledge" && (
            <section className="panel library-panel">
              <div className="library-toolbar">
                <h2>
                  All documents{" "}
                  <span className="number-badge">{docs.length}</span>
                </h2>
                <label className="search-input">
                  <Search size={17} />
                  <input
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Find a document…"
                    aria-label="Find a document"
                  />
                </label>
              </div>
              <div className="document-list">
                {docs
                  .filter((d) =>
                    `${d.title} ${d.filename}`
                      .toLowerCase()
                      .includes(search.toLowerCase()),
                  )
                  .map((d) => (
                    <div className="document-row" key={d.id}>
                      <span className="file-icon">
                        <FileText size={21} />
                      </span>
                      <button
                        className="document-title"
                        onClick={() => void openDocument(d.id)}
                      >
                        <strong>{d.title}</strong>
                        <span>
                          {d.filename} · {d.word_count} words
                        </span>
                      </button>
                      <span className="document-chunks">
                        {d.chunk_count}{" "}
                        {d.chunk_count === 1 ? "passage" : "passages"}
                      </span>
                      <span className="document-date">
                        {date(d.created_at)}
                      </span>
                      <button
                        className="icon-button danger"
                        aria-label={`Delete ${d.title}`}
                        onClick={() => void deleteDocument(d)}
                      >
                        <Trash2 size={17} />
                      </button>
                    </div>
                  ))}
              </div>
              {!docs.length && (
                <Empty
                  icon={Library}
                  title="Your library starts here"
                  text="Upload a policy, product guide, or FAQ to give your copilot something to work with."
                />
              )}
              {docs.length > 0 &&
                !docs.some((d) =>
                  `${d.title} ${d.filename}`
                    .toLowerCase()
                    .includes(search.toLowerCase()),
                ) && (
                  <Empty
                    icon={Search}
                    title="No documents found"
                    text="Try a different title or file name."
                  />
                )}
              <div className="library-footer">
                <ShieldCheck size={16} /> Documents are stored locally. PDF,
                Markdown, and plain text supported.
              </div>
            </section>
          )}

          {tab === "history" && (
            <section className="panel history-panel">
              <div className="panel-heading">
                <div>
                  <History size={19} />
                  <h2>Recent conversations</h2>
                </div>
                <span className="pill">{history.length} saved</span>
              </div>
              {history.length ? (
                history.map((item) => (
                  <div className="history-row" key={item.id}>
                    <button onClick={() => showAnswer(item)}>
                      <span className="history-icon">
                        <MessageSquare size={18} />
                      </span>
                      <span>
                        <strong>{item.question}</strong>
                        <small>
                          {item.classification.label} ·{" "}
                          {item.citation_ids.length} cited sources ·{" "}
                          {item.created_at && date(item.created_at)}
                        </small>
                      </span>
                      <ChevronRight size={17} />
                    </button>
                    <button
                      className="icon-button danger"
                      aria-label={`Delete conversation: ${item.question}`}
                      onClick={async () => {
                        if (
                          !window.confirm(
                            "Delete this saved conversation and its feedback?",
                          )
                        )
                          return;
                        try {
                          await api(`/conversations/${item.id}`, {
                            method: "DELETE",
                          });
                          if (answer?.id === item.id) setAnswer(null);
                          await refresh();
                        } catch (e) {
                          setError((e as Error).message);
                        }
                      }}
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))
              ) : (
                <Empty
                  icon={MessageSquare}
                  title="A fresh conversation starts with a question"
                  text="Questions and answers will appear here after you use the copilot."
                />
              )}
            </section>
          )}

          {tab === "evaluation" && (
            <>
              <div className="evaluation-intro panel">
                <div className="eval-intro-icon">
                  <FlaskConical size={29} />
                </div>
                <div>
                  <h2>A small benchmark. An honest starting point.</h2>
                  <p>
                    Compare keyword and hybrid retrieval on 32 bundled
                    questions, then test the ticket classifier on 20 held-out
                    examples. Your uploaded documents aren't used in this
                    benchmark.
                  </p>
                </div>
                <button
                  className="button primary"
                  disabled={evaluating}
                  onClick={() => void evaluate()}
                >
                  {evaluating ? (
                    <LoaderCircle className="spin" size={17} />
                  ) : (
                    <FlaskConical size={17} />
                  )}{" "}
                  {evaluating
                    ? "Running…"
                    : report
                      ? "Run again"
                      : "Run benchmark"}
                </button>
              </div>
              {report ? (
                <>
                  <div className="report-toolbar">
                    <span>
                      Measured {new Date(report.created_at).toLocaleString()} ·{" "}
                      {report.retrieval_mode}
                    </span>
                    <button className="text-button" onClick={downloadReport}>
                      <Download size={16} /> Export results
                    </button>
                  </div>
                  <div className="eval-cards">
                    {report.retrieval.map((run) => (
                      <section className="panel eval-card" key={run.method}>
                        <div className="eyebrow">
                          {run.method === "bm25"
                            ? "KEYWORD BASELINE"
                            : "HYBRID RETRIEVAL"}
                        </div>
                        <div className="big-metric">
                          {percent(run.recall_at_3)}
                          <span>Recall @ 3</span>
                        </div>
                        <Metric
                          label="Mean reciprocal rank"
                          value={run.mrr_at_3.toFixed(3)}
                        />
                        <Metric
                          label="Unknown-question abstention"
                          value={percent(run.unknown_abstention_rate)}
                        />
                        <Metric
                          label="Mean warm search time"
                          value={`${run.mean_latency_ms} ms`}
                        />
                      </section>
                    ))}
                    <section className="panel eval-card">
                      <div className="eyebrow">TICKET CLASSIFICATION</div>
                      <div className="big-metric">
                        {report.classifier.macro_f1.toFixed(2)}
                        <span>Macro F1</span>
                      </div>
                      <Metric
                        label="Test accuracy"
                        value={percent(report.classifier.accuracy)}
                      />
                      <Metric
                        label="Majority-class baseline"
                        value={percent(
                          report.classifier.majority_baseline_accuracy,
                        )}
                      />
                      <Metric
                        label="Held-out examples"
                        value={String(report.classifier.test_examples)}
                      />
                    </section>
                  </div>
                  <div className="alert benchmark-note">
                    <CircleAlert size={18} />
                    <span>{report.limitations}</span>
                  </div>
                  <section className="panel cases-panel">
                    <div className="library-toolbar">
                      <h2>Inspect every test case</h2>
                      <select
                        aria-label="Benchmark method"
                        value={caseMethod}
                        onChange={(e) => setCaseMethod(Number(e.target.value))}
                      >
                        <option value={1}>Hybrid search</option>
                        <option value={0}>Keyword baseline</option>
                      </select>
                    </div>
                    <div className="table-scroll">
                      <table>
                        <thead>
                          <tr>
                            <th>Question</th>
                            <th>Expected source</th>
                            <th>Result</th>
                          </tr>
                        </thead>
                        <tbody>
                          {report.retrieval[caseMethod].cases.map((c) => (
                            <tr key={c.question}>
                              <td>{c.question}</td>
                              <td>{c.expected_source || "Should abstain"}</td>
                              <td>
                                <span
                                  className={`result-chip ${c.passed ? "pass" : "fail"}`}
                                >
                                  {c.passed ? (
                                    <Check size={13} />
                                  ) : (
                                    <X size={13} />
                                  )}{" "}
                                  {c.rank
                                    ? `Rank ${c.rank}`
                                    : c.abstained
                                      ? "Abstained"
                                      : "Needs work"}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </section>
                </>
              ) : (
                <div className="eval-empty">
                  <BarChart3 size={40} strokeWidth={1.2} />
                  <h3>Your results belong here.</h3>
                  <p>
                    Run the benchmark to get actual measurements.
                    <br />
                    No placeholder scores. No hidden failures.
                  </p>
                </div>
              )}
            </>
          )}
          <footer className="main-footer">
            <Aperture size={14} />
            <span>SupportLens</span>
            <span className="footer-divider">/</span> Evidence first. Always.
          </footer>
        </main>
      </div>
      {toast && (
        <div className="toast" role="status">
          <Check size={17} />
          {toast}
        </div>
      )}
      {modal === "add" && (
        <AddDocument
          onClose={() => setModal(null)}
          onSaved={async () => {
            setModal(null);
            setToast("Document added and ready to search.");
            await refresh();
          }}
        />
      )}
      {modal === "guide" && (
        <Modal
          title="A useful answer shows its work"
          onClose={() => setModal(null)}
        >
          <div className="guide-content">
            <p>
              SupportLens is a local support workspace that combines document
              search, optional language-model drafting, and a trained ticket
              classifier.
            </p>
            <ol>
              <li>
                <strong>Add knowledge.</strong> Upload your policies, guides, or
                FAQs. Documents are divided into searchable passages.
              </li>
              <li>
                <strong>Ask a question.</strong> Keyword search uses BM25.
                Hybrid search combines BM25 with TF-IDF, or with sentence
                embeddings when enabled.
              </li>
              <li>
                <strong>Inspect the evidence.</strong> The default mode quotes
                exact passages. Enable Ollama in the project’s .env file for
                generated replies. Every answer needs review.
              </li>
              <li>
                <strong>Measure the results.</strong> The evaluation lab runs a
                fixed synthetic benchmark. Use its failures to guide
                improvements.
              </li>
            </ol>
            <div className="review-note">
              <CircleAlert size={17} />
              <span>
                This is a single-user portfolio app. Search scores are not
                probabilities that an answer is correct. Keep it local until
                authentication and access controls are added.
              </span>
            </div>
            <a
              className="button secondary"
              href="/docs"
              target="_blank"
              rel="noreferrer"
            >
              Explore the API <ExternalLink size={15} />
            </a>
          </div>
        </Modal>
      )}
      {viewDoc && (
        <Modal title={viewDoc.title} onClose={() => setViewDoc(null)}>
          <div className="document-preview">{viewDoc.content}</div>
        </Modal>
      )}
    </div>
  );
}

function Stat({
  icon: Icon,
  label,
  value,
  detail,
}: {
  icon: LucideIcon;
  label: string;
  value?: number;
  detail: string;
}) {
  return (
    <div className="stat-card">
      <div>
        <span>{label}</span>
        <Icon size={18} />
      </div>
      <strong>{value ?? "—"}</strong>
      <small>{detail}</small>
    </div>
  );
}
function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric-row">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
function Empty({
  icon: Icon,
  title,
  text,
}: {
  icon: LucideIcon;
  title: string;
  text: string;
}) {
  return (
    <div className="empty">
      <Icon size={35} strokeWidth={1.3} />
      <h3>{title}</h3>
      <p>{text}</p>
    </div>
  );
}
function Modal({
  title,
  onClose,
  children,
}: {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const dialog = ref.current;
    dialog?.showModal();
    return () => dialog?.close();
  }, []);
  return (
    <dialog
      className="modal"
      ref={ref}
      onCancel={onClose}
      onClick={(e) => {
        if (e.target === ref.current) onClose();
      }}
    >
      <div className="modal-heading">
        <h2>{title}</h2>
        <button
          autoFocus
          className="icon-button"
          aria-label="Close dialog"
          onClick={onClose}
        >
          <X size={21} />
        </button>
      </div>
      {children}
    </dialog>
  );
}
function AddDocument({
  onClose,
  onSaved,
}: {
  onClose: () => void;
  onSaved: () => Promise<void>;
}) {
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [mode, setMode] = useState("file");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (mode === "file") {
        if (!file) throw new Error("Choose a file first.");
        const data = new FormData();
        data.append("file", file);
        await api("/documents/upload", { method: "POST", body: data });
      } else {
        await api("/documents", json({ title, content }));
      }
      await onSaved();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <Modal
      title="Add to your knowledge base"
      onClose={() => {
        if (!busy) onClose();
      }}
    >
      <form className="upload-form" onSubmit={submit}>
        <div className="segmented">
          <button
            type="button"
            className={mode === "file" ? "selected" : ""}
            onClick={() => setMode("file")}
          >
            Upload file
          </button>
          <button
            type="button"
            className={mode === "text" ? "selected" : ""}
            onClick={() => setMode("text")}
          >
            Paste text
          </button>
        </div>
        {mode === "file" ? (
          <label className="upload-area">
            <Upload size={30} />
            <strong>{file ? file.name : "Choose a document"}</strong>
            <span>PDF, Markdown, or plain text · Up to 5 MB</span>
            <input
              type="file"
              accept=".pdf,.md,.txt"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              aria-label="Choose document file"
              required
            />
          </label>
        ) : (
          <>
            <label>
              Document title
              <input
                required
                maxLength={160}
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Product warranty policy"
              />
            </label>
            <label>
              Document text
              <textarea
                required
                rows={8}
                minLength={10}
                maxLength={250000}
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Paste the policy, guide, or FAQ you want the copilot to use…"
              />
            </label>
          </>
        )}
        {error && (
          <div className="alert error" role="alert">
            {error}
          </div>
        )}
        <p className="form-hint">
          Use text-based PDFs. Scanned documents need OCR before uploading.
        </p>
        <div className="modal-actions">
          <button
            type="button"
            className="button secondary"
            onClick={onClose}
            disabled={busy}
          >
            Cancel
          </button>
          <button type="submit" className="button primary" disabled={busy}>
            {busy ? (
              <LoaderCircle className="spin" size={16} />
            ) : (
              <Plus size={16} />
            )}{" "}
            {busy ? "Adding…" : "Add document"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
