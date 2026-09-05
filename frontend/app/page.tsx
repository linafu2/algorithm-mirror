"use client";

import { useCallback, useEffect, useState } from "react";

const API = "http://localhost:8000";

type Post = {
  id: number;
  title: string;
  tags: string[];
  tone: string;
  intensity: number;
};

type Interaction = {
  post_id: number;
  action: string;
  title: string;
};

type AlgorithmReason = {
  summary: string;
  score: number;
  matched_tags: string[];
  tag_scores: Record<string, number>;
};

type FeedMetrics = {
  diversity_score: number;
  concentration_score: number;
  dominant_topic: string | null;
  top_topics: {
    topic: string;
    share: number;
  }[];
  interaction_count: number;
};

type FeedAudit = {
  summary: string;
  dominant_patterns: string[];
  narrowing_level: "low" | "moderate" | "high";
  user_reflection: string;
  suggested_action: string;
};

type AuditResponse = {
  metrics: FeedMetrics;
  ai_analysis: FeedAudit;
};

type TraceContribution = {
  tag: string;
  contribution: number;
};

type TraceCandidate = {
  post_id: number;
  title: string;
  tags: string[];
  score: number;
  contributions: TraceContribution[];
};

type RecommendationTrace = {
  profile: Record<string, number>;
  selected: TraceCandidate | null;
  candidates: TraceCandidate[];
};


export default function Home() {
  const [currentPost, setCurrentPost] = useState<Post | null>(null);
  const [interactions, setInteractions] = useState<Interaction[]>([]);
  const [profile, setProfile] = useState<Record<string, number>>({});
  const [algorithmReason, setAlgorithmReason] = useState<AlgorithmReason | null>(null);
  const [loadingFeed, setLoadingFeed] = useState(true);
  const [loadingAction, setLoadingAction] = useState(false);
  const [error, setError] = useState("");
  const [feedAudit, setFeedAudit] = useState<AuditResponse | null>(null);
  const [auditLoading, setAuditLoading] = useState(false);
  const [auditError, setAuditError] = useState<string | null>(null);
  const [recommendationTrace, setRecommendationTrace] =
    useState<RecommendationTrace | null>(null);
  const [traceLoading, setTraceLoading] = useState(false);
  const [traceError, setTraceError] = useState<string | null>(null);
  const [analysisTab, setAnalysisTab] = useState<"trace" | "audit">("trace");

  const actionButtonClass =
    "w-full px-4 py-3 rounded-xl bg-white text-black font-medium disabled:opacity-50";

  const showAnalysisPanel =
    recommendationTrace !== null || feedAudit !== null;

  function getDeepDiveButtonClass(tab: "trace" | "audit") {
    const hasData =
      tab === "trace" ? recommendationTrace !== null : feedAudit !== null;

    if (analysisTab === tab && hasData) {
      return actionButtonClass;
    }

    if (hasData) {
      return "w-full px-4 py-3 rounded-xl bg-neutral-800 text-neutral-200 font-medium hover:bg-neutral-700 disabled:opacity-50";
    }

    return actionButtonClass;
  }

  function showTraceResults() {
    if (!recommendationTrace) return;
    setAnalysisTab("trace");
    setTraceError(null);
  }

  function showAuditResults() {
    if (!feedAudit) return;
    setAnalysisTab("audit");
    setAuditError(null);
  }

  const loadRecommendation = useCallback(async (nextInteractions: Interaction[]) => {
    const res = await fetch(`${API}/recommend`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(
        nextInteractions.map((i) => ({
          post_id: i.post_id,
          action: i.action,
        }))
      ),
    });

    if (!res.ok) {
      throw new Error("Could not load the next recommendation.");
    }

    const data = await res.json();
    setCurrentPost(data.next_post);
    setProfile(data.profile);
    setAlgorithmReason(data.reason);
  }, []);

  useEffect(() => {
    loadRecommendation([])
      .catch(() => setError("Could not connect to the backend at localhost:8000."))
      .finally(() => setLoadingFeed(false));
  }, [loadRecommendation]);

  async function handleAction(action: string) {
    if (!currentPost || loadingAction) return;

    setLoadingAction(true);
    setError("");
    setRecommendationTrace(null);
    setFeedAudit(null);
    setTraceError(null);
    setAuditError(null);

    const updatedInteractions = [
      ...interactions,
      {
        post_id: currentPost.id,
        action,
        title: currentPost.title,
      },
    ];

    setInteractions(updatedInteractions);

    try {
      await loadRecommendation(updatedInteractions);
    } catch {
      setError("Something went wrong updating your feed.");
    } finally {
      setLoadingAction(false);
    }
  }

  async function runFeedAudit() {
    if (interactions.length === 0) {
      setAuditError(
        "Interact with a few posts before running an audit."
      );
      return;
    }

    if (feedAudit) {
      showAuditResults();
      return;
    }

    setAuditLoading(true);
    setAuditError(null);
  
    try {
      const response = await fetch(`${API}/audit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ interactions }),
      });
  
      if (!response.ok) {
        throw new Error(
          `Audit failed: ${response.status}`
        );
      }
  
      const data: AuditResponse =
        await response.json();
  
      setFeedAudit(data);
      setAnalysisTab("audit");
    } catch (error) {
      console.error(error);
  
      setAuditError(
        "Something went wrong while auditing the feed."
      );
    } finally {
      setAuditLoading(false);
    }
  }

  async function runRecommendationTrace() {
    if (interactions.length === 0) {
      setTraceError(
        "Interact with at least one post first."
      );
      return;
    }

    if (recommendationTrace) {
      showTraceResults();
      return;
    }

    setTraceLoading(true);
    setTraceError(null);

    try {
      const response = await fetch(`${API}/trace`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ interactions }),
      });

      if (!response.ok) {
        throw new Error(
          `Trace failed: ${response.status}`
        );
      }

      const data: RecommendationTrace =
        await response.json();

      setRecommendationTrace(data);
      setAnalysisTab("trace");
    } catch (error) {
      console.error(error);

      setTraceError(
        "Something went wrong while tracing the recommendation."
      );

    } finally {
      setTraceLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-neutral-950 text-white p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <section className="md:col-span-2 bg-neutral-900 rounded-2xl p-6">
          <h1 className="text-3xl font-bold mb-2">Algorithm Mirror</h1>
          <p className="text-neutral-400 mb-6">
            A transparent social feed that shows how your actions shape
            recommendations.
          </p>

          {error && (
            <div className="mb-4 rounded-xl border border-red-800 bg-red-950/40 px-4 py-3 text-sm text-red-200">
              {error}
            </div>
          )}

          {loadingFeed ? (
            <div className="border border-neutral-700 rounded-2xl p-8 text-neutral-400">
              Loading your mock feed...
            </div>
          ) : currentPost ? (
            <div className="border border-neutral-700 rounded-2xl p-8 min-h-[420px] flex flex-col justify-between">
              <div>
                <div className="text-sm text-neutral-400 mb-3">
                  Mock short-form post · {interactions.length + 1} of 8
                </div>
                <h2 className="text-4xl font-semibold mb-4">
                  {currentPost.title}
                </h2>

                <div className="flex flex-wrap gap-2 mb-4">
                  {currentPost.tags.map((tag) => (
                    <span
                      key={tag}
                      className="px-3 py-1 rounded-full bg-neutral-800 text-sm"
                    >
                      #{tag}
                    </span>
                  ))}
                </div>

                <p className="text-neutral-400">
                  Tone: {currentPost.tone} · Intensity: {currentPost.intensity}
                  /5
                </p>
              </div>

              <div className="flex gap-3 mt-8">
                <button
                  onClick={() => handleAction("like")}
                  disabled={loadingAction}
                  className="px-5 py-3 rounded-xl bg-white text-black font-medium disabled:opacity-50"
                >
                  Like
                </button>
                <button
                  onClick={() => handleAction("skip")}
                  disabled={loadingAction}
                  className="px-5 py-3 rounded-xl bg-neutral-800 disabled:opacity-50"
                >
                  Skip
                </button>
                <button
                  onClick={() => handleAction("not_interested")}
                  disabled={loadingAction}
                  className="px-5 py-3 rounded-xl bg-neutral-800 disabled:opacity-50"
                >
                  Not interested
                </button>
              </div>
            </div>
          ) : (
            <div className="border border-neutral-700 rounded-2xl p-8">
              <h2 className="text-2xl font-semibold mb-2">Feed complete</h2>
              <p className="text-neutral-400">
                You have seen all mock posts. Run an audit below to summarize
                your session and review your visible profile.
              </p>
            </div>
          )}
          </section>

          <aside className="bg-neutral-900 rounded-2xl p-6 space-y-6 md:self-start">
            <div>
              <h2 className="text-xl font-semibold mb-3">Visible User Model</h2>

              {Object.keys(profile).length === 0 ? (
                <p className="text-neutral-400">
                  Interact with posts to let the algorithm form a profile.
                </p>
              ) : (
                <div className="space-y-3">
                  {Object.entries(profile)
                    .sort((a, b) => b[1] - a[1])
                    .map(([tag, value]) => (
                      <div key={tag}>
                        <div className="flex justify-between text-sm">
                          <span>{tag}</span>
                          <span>
                            {value > 0 ? "+" : ""}
                            {value.toFixed(1)}
                          </span>
                        </div>
                        <div className="h-2 bg-neutral-800 rounded">
                          <div
                            className={`h-2 rounded ${
                              value >= 0 ? "bg-white" : "bg-red-400"
                            }`}
                            style={{
                              width: `${Math.min(Math.abs(value) * 20, 100)}%`,
                            }}
                          />
                        </div>
                      </div>
                    ))}
                </div>
              )}
            </div>

            <div>
              <h2 className="text-xl font-semibold mb-3">
                Why this recommendation?
              </h2>
              {algorithmReason ? (
                <div className="space-y-3 text-sm">
                  <p className="text-neutral-200 leading-relaxed">
                    {algorithmReason.summary}
                  </p>
                  <div className="rounded-xl bg-neutral-950 p-3 text-neutral-400">
                    <div className="mb-2">
                      Match score:{" "}
                      <span className="text-white">{algorithmReason.score}</span>
                    </div>
                    {algorithmReason.matched_tags.map((tag) => (
                      <div
                        key={tag}
                        className="flex justify-between py-0.5 text-xs"
                      >
                        <span>#{tag}</span>
                        <span>
                          {algorithmReason.tag_scores[tag] > 0 ? "+" : ""}
                          {algorithmReason.tag_scores[tag]}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <p className="text-neutral-400 text-sm">
                  No recommendation reason yet.
                </p>
              )}
            </div>
          </aside>
        </div>

        <section className="bg-neutral-900 rounded-2xl p-6">
          <h2 className="text-xl font-semibold mb-3">Deep dive</h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-2xl">
            <button
              onClick={runRecommendationTrace}
              disabled={traceLoading}
              className={getDeepDiveButtonClass("trace")}
            >
              {traceLoading
                ? "Tracing recommendation..."
                : "Why did I get this?"}
            </button>

            <button
              onClick={runFeedAudit}
              disabled={auditLoading}
              className={getDeepDiveButtonClass("audit")}
            >
              {auditLoading
                ? "Auditing feed..."
                : "Audit my algorithm"}
            </button>
          </div>

          {(traceError || auditError) && (
            <div className="mt-3 space-y-1">
              {traceError &&
                (!showAnalysisPanel || analysisTab === "trace") && (
                  <p className="text-sm text-red-400">{traceError}</p>
                )}
              {auditError &&
                (!showAnalysisPanel || analysisTab === "audit") && (
                  <p className="text-sm text-red-400">{auditError}</p>
                )}
            </div>
          )}

          {showAnalysisPanel && (
            <>
            {analysisTab === "trace" && recommendationTrace?.selected && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
                <div className="border border-neutral-800 rounded-2xl p-5">
                  <p className="text-xs uppercase tracking-wider text-neutral-500">
                    Recommendation trace
                  </p>

                  <h3 className="text-xl font-semibold mt-2">
                    Why you saw this
                  </h3>

                  <p className="text-neutral-300 mt-1">
                    {recommendationTrace.selected.title}
                  </p>

                  <div className="mt-6 space-y-3">
                    {recommendationTrace.selected.contributions.map(
                      (contribution) => (
                        <div
                          key={contribution.tag}
                          className="flex items-center justify-between"
                        >
                          <span className="text-sm">{contribution.tag}</span>

                          <span
                            className={
                              contribution.contribution > 0
                                ? "text-green-400"
                                : contribution.contribution < 0
                                ? "text-red-400"
                                : "text-neutral-500"
                            }
                          >
                            {contribution.contribution > 0 ? "+" : ""}
                            {contribution.contribution}
                          </span>
                        </div>
                      )
                    )}
                  </div>

                  <div className="border-t border-neutral-800 mt-5 pt-4 flex justify-between">
                    <span className="text-sm text-neutral-400">
                      Final ranking score
                    </span>
                    <span className="font-semibold">
                      {recommendationTrace.selected.score}
                    </span>
                  </div>
                </div>

                {recommendationTrace.candidates.length > 0 && (
                  <div>
                    <p className="text-xs uppercase tracking-wider text-neutral-500">
                      Candidate ranking
                    </p>

                    <div className="mt-3 space-y-2">
                      {recommendationTrace.candidates.map(
                        (candidate, index) => {
                          const highestScore =
                            recommendationTrace.candidates[0]?.score || 1;

                          const width =
                            highestScore > 0
                              ? Math.max(
                                  0,
                                  (candidate.score / highestScore) * 100
                                )
                              : 0;

                          return (
                            <div
                              key={candidate.post_id}
                              className="py-3 border-b border-neutral-900"
                            >
                              <div className="flex justify-between">
                                <div className="flex gap-3">
                                  <span className="text-neutral-600">
                                    {index + 1}
                                  </span>
                                  <span className="text-sm">
                                    {candidate.title}
                                  </span>
                                </div>

                                <span className="text-sm font-mono text-neutral-400">
                                  {candidate.score}
                                </span>
                              </div>

                              <div className="h-1 bg-neutral-900 rounded mt-2">
                                <div
                                  className="h-1 bg-neutral-500 rounded"
                                  style={{ width: `${width}%` }}
                                />
                              </div>
                            </div>
                          );
                        }
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}

            {analysisTab === "audit" && feedAudit && (
              <div className="space-y-6 mt-6">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                  <div>
                    <p className="text-xs uppercase tracking-wider text-neutral-500">
                      Feed diversity
                    </p>

                    <p className="text-4xl font-semibold mt-1">
                      {feedAudit.metrics.diversity_score}
                    </p>

                    <div className="h-2 bg-neutral-800 rounded mt-2">
                      <div
                        className="h-2 bg-white rounded"
                        style={{
                          width: `${feedAudit.metrics.diversity_score}%`,
                        }}
                      />
                    </div>
                  </div>

                  <div>
                    <p className="text-xs uppercase tracking-wider text-neutral-500">
                      Feed concentration
                    </p>

                    <p className="text-4xl font-semibold mt-1">
                      {feedAudit.metrics.concentration_score}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs uppercase tracking-wider text-neutral-500">
                      Dominant topic
                    </p>

                    <p className="text-xl mt-1">
                      {feedAudit.metrics.dominant_topic ?? "None yet"}
                    </p>
                  </div>
                </div>

                <div>
                  <h3 className="font-semibold">What the algorithm sees</h3>

                  <div className="mt-3 space-y-2">
                    {feedAudit.metrics.top_topics.map((topic) => (
                      <div
                        key={topic.topic}
                        className="flex justify-between text-sm"
                      >
                        <span>{topic.topic}</span>
                        <span className="text-neutral-400">
                          {topic.share}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="border-t border-neutral-800 pt-5">
                  <p className="text-xs uppercase tracking-wider text-neutral-500 mb-2">
                    Claude interpretation
                  </p>

                  <p className="leading-relaxed text-neutral-200">
                    {feedAudit.ai_analysis.summary}
                  </p>
                </div>

                <div>
                  <p className="text-sm font-medium mb-2">Patterns detected</p>

                  <ul className="space-y-2 text-sm text-neutral-300">
                    {feedAudit.ai_analysis.dominant_patterns.map((pattern) => (
                      <li key={pattern}>• {pattern}</li>
                    ))}
                  </ul>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div>
                    <p className="text-xs uppercase tracking-wider text-neutral-500">
                      Feed narrowing
                    </p>

                    <p className="text-lg capitalize mt-1">
                      {feedAudit.ai_analysis.narrowing_level}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs uppercase tracking-wider text-neutral-500 mb-2">
                      Change your feed
                    </p>

                    <p className="text-sm text-neutral-300">
                      {feedAudit.ai_analysis.suggested_action}
                    </p>
                  </div>
                </div>

                <div className="bg-neutral-950 p-4 rounded-xl">
                  <p className="text-xs uppercase tracking-wider text-neutral-500 mb-2">
                    Mirror
                  </p>

                  <p className="italic text-neutral-200">
                    {feedAudit.ai_analysis.user_reflection}
                  </p>
                </div>
              </div>
            )}
            </>
          )}
        </section>
      </div>
    </main>
  );
}
