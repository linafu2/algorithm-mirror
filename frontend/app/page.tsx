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

export default function Home() {
  const [currentPost, setCurrentPost] = useState<Post | null>(null);
  const [interactions, setInteractions] = useState<Interaction[]>([]);
  const [profile, setProfile] = useState<Record<string, number>>({});
  const [algorithmReason, setAlgorithmReason] = useState<AlgorithmReason | null>(
    null
  );
  const [claudeExplanation, setClaudeExplanation] = useState("");
  const [loadingFeed, setLoadingFeed] = useState(true);
  const [loadingAction, setLoadingAction] = useState(false);
  const [loadingExplanation, setLoadingExplanation] = useState(false);
  const [error, setError] = useState("");

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
    setClaudeExplanation("");

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

  async function explainFeed() {
    setLoadingExplanation(true);
    setError("");

    try {
      const res = await fetch(`${API}/explain`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          profile,
          recent_interactions: interactions.slice(-5),
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail ?? "Claude could not explain your feed.");
      }

      setClaudeExplanation(data.explanation);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Claude request failed.");
    } finally {
      setLoadingExplanation(false);
    }
  }

  return (
    <main className="min-h-screen bg-neutral-950 text-white p-8">
      <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6">
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
                You have seen all mock posts. Ask Claude to summarize your
                session and review your visible profile on the right.
              </p>
            </div>
          )}
        </section>

        <aside className="bg-neutral-900 rounded-2xl p-6 space-y-6">
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
                        <span>{value > 0 ? "+" : ""}{value.toFixed(1)}</span>
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

          <div>
            <button
              onClick={explainFeed}
              disabled={loadingExplanation}
              className="w-full px-4 py-3 rounded-xl bg-white text-black font-medium disabled:opacity-50"
            >
              {loadingExplanation
                ? "Asking Claude..."
                : "Ask Claude to explain my feed"}
            </button>

            {claudeExplanation && (
              <div className="mt-4 p-4 rounded-xl bg-neutral-950 text-neutral-200 text-sm leading-relaxed">
                {claudeExplanation}
              </div>
            )}
          </div>
        </aside>
      </div>
    </main>
  );
}
