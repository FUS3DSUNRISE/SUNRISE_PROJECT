"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getFeedbackAnalytics, getUserFriendlyErrorMessage, type FeedbackAnalytics, type FeedbackRating } from "@/services/api";

type LoadState = "loading" | "ready" | "error";

const ratingLabels: Record<FeedbackRating, string> = {
  positive: "Positive",
  neutral: "Neutral",
  negative: "Negative",
};

const ratingColors: Record<FeedbackRating, string> = {
  positive: "#22c55e",
  neutral: "#f59e0b",
  negative: "#f43f5e",
};

const emptyAnalytics: FeedbackAnalytics = {
  total_feedback: 0,
  success_rate: 0,
  average_accuracy_score: null,
  average_quality_score: null,
  ratings: {},
  comments: [],
};

const formatScore = (score: number | null) => (score === null ? "N/A" : `${score.toFixed(2)} / 5`);
const formatDate = (value: string | null) => {
  if (!value) return "Unknown date";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Unknown date";

  return new Intl.DateTimeFormat("en", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZoneName: "short",
  }).format(date);
};

export default function AnalyticsPage() {
  const [state, setState] = useState<LoadState>("loading");
  const [analytics, setAnalytics] = useState<FeedbackAnalytics>(emptyAnalytics);
  const [error, setError] = useState<string | null>(null);
  const [showComments, setShowComments] = useState(false);

  useEffect(() => {
    let isMounted = true;

    async function loadAnalytics() {
      try {
        const data = await getFeedbackAnalytics();
        if (!isMounted) return;
        setAnalytics(data);
        setState("ready");
      } catch (err) {
        if (!isMounted) return;
        setError(getUserFriendlyErrorMessage(err, "Could not load analytics"));
        setState("error");
      }
    }

    loadAnalytics();

    return () => {
      isMounted = false;
    };
  }, []);

  const ratingData = useMemo(
    () =>
      (Object.keys(ratingLabels) as FeedbackRating[]).map((rating) => ({
        name: ratingLabels[rating],
        rating,
        value: analytics.ratings[rating] ?? 0,
      })),
    [analytics.ratings]
  );

  const scoreData = useMemo(
    () => [
      {
        name: "Accuracy",
        score: analytics.average_accuracy_score ?? 0,
      },
      {
        name: "Quality",
        score: analytics.average_quality_score ?? 0,
      },
    ],
    [analytics.average_accuracy_score, analytics.average_quality_score]
  );

  const successRate = Number(analytics.success_rate ?? 0);
  const issueRate = Math.max(0, Number((100 - successRate).toFixed(2)));
  const hasFeedback = analytics.total_feedback > 0;

  if (state === "loading") {
    return <PageShell title="Analytics Dashboard" subtitle="Loading feedback statistics..." />;
  }

  if (state === "error") {
    return (
      <PageShell title="Analytics Dashboard" subtitle="Feedback statistics are unavailable right now.">
        <div className="mt-8 rounded-lg border border-red-500/30 bg-red-500/10 p-5 text-red-100">
          {error}
        </div>
      </PageShell>
    );
  }

  return (
    <PageShell
      title="Analytics Dashboard"
      subtitle="A lightweight view of user feedback across generated 3D models."
    >
      <div className="mt-8 grid grid-cols-1 gap-4 md:grid-cols-4">
        <MetricCard title="Total Feedback" value={analytics.total_feedback.toString()} />
        <MetricCard title="Success Rate" value={`${successRate}%`} />
        <MetricCard title="Accuracy" value={formatScore(analytics.average_accuracy_score)} />
        <MetricCard title="Quality" value={formatScore(analytics.average_quality_score)} />
      </div>

      {!hasFeedback ? (
        <div className="mt-8 rounded-lg border border-white/10 bg-[#0b1020]/70 p-8 text-center">
          <h2 className="text-xl font-semibold text-white">No feedback yet</h2>
          <p className="mx-auto mt-3 max-w-xl text-sm leading-6 text-white/60">
            Submit feedback on a generated model, then refresh this page to see the statistics update.
          </p>
          <Link
            href="/"
            className="mt-6 inline-flex rounded-lg bg-[#ff8a2c] px-5 py-3 text-sm font-bold text-black transition hover:bg-[#ff9b4d]"
          >
            Generate a model
          </Link>
        </div>
      ) : (
        <>
          <div className="mt-8 grid grid-cols-1 gap-5 lg:grid-cols-[minmax(0,1fr)_380px]">
            <section className="rounded-lg border border-white/10 bg-[#0b1020]/70 p-5">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h2 className="text-lg font-semibold text-white">Average Scores</h2>
                  <p className="mt-1 text-sm text-white/50">Accuracy and quality ratings from 1 to 5.</p>
                </div>
              </div>
              <div className="mt-6 h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={scoreData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
                    <XAxis dataKey="name" stroke="rgba(255,255,255,0.55)" tickLine={false} />
                    <YAxis domain={[0, 5]} stroke="rgba(255,255,255,0.55)" tickLine={false} />
                    <Tooltip
                      cursor={{ fill: "rgba(255,255,255,0.04)" }}
                      contentStyle={{ background: "#111827", border: "1px solid rgba(255,255,255,0.12)" }}
                    />
                    <Bar dataKey="score" fill="#ff8a2c" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </section>

            <section className="rounded-lg border border-white/10 bg-[#0b1020]/70 p-5">
              <h2 className="text-lg font-semibold text-white">Rating Mix</h2>
              <p className="mt-1 text-sm text-white/50">Positive, neutral, and negative feedback.</p>
              <div className="mt-6 h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={ratingData} dataKey="value" nameKey="name" innerRadius={64} outerRadius={105} paddingAngle={3}>
                      {ratingData.map((entry) => (
                        <Cell key={entry.rating} fill={ratingColors[entry.rating]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{ background: "#111827", border: "1px solid rgba(255,255,255,0.12)" }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="grid grid-cols-3 gap-2">
                {ratingData.map((entry) => (
                  <div key={entry.rating} className="rounded-lg border border-white/10 bg-white/[0.03] p-3">
                    <div className="h-2 w-8 rounded-full" style={{ backgroundColor: ratingColors[entry.rating] }} />
                    <p className="mt-2 text-xs text-white/50">{entry.name}</p>
                    <p className="text-lg font-bold text-white">{entry.value}</p>
                  </div>
                ))}
              </div>
            </section>
          </div>

          <section className="mt-5 rounded-lg border border-white/10 bg-[#0b1020]/70 p-5">
            <h2 className="text-lg font-semibold text-white">Feedback Outcome</h2>
            <p className="mt-1 text-sm text-white/50">A quick success vs. needs-review split from the analytics endpoint.</p>
            <div className="mt-5 h-4 overflow-hidden rounded-full bg-white/10">
              <div className="h-full bg-[#22c55e]" style={{ width: `${successRate}%` }} />
            </div>
            <div className="mt-3 flex flex-wrap gap-4 text-sm text-white/65">
              <span>Success: {successRate}%</span>
              <span>Needs review: {issueRate}%</span>
            </div>
          </section>

          <section className="mt-5 rounded-lg border border-white/10 bg-[#0b1020]/70 p-5">
            <button
              type="button"
              onClick={() => setShowComments((current) => !current)}
              className="flex w-full cursor-pointer flex-col gap-3 text-left sm:flex-row sm:items-center sm:justify-between"
              aria-expanded={showComments}
            >
              <div>
                <h2 className="text-lg font-semibold text-white">User Comments</h2>
                <p className="mt-1 text-sm text-white/50">
                  {showComments ? "Hide submitted generation feedback comments." : "Show submitted generation feedback comments."}
                </p>
              </div>

              <span className="inline-flex items-center gap-2 text-sm text-white/60">
                {analytics.comments.length} comments
                <span className="text-lg leading-none text-[#ff8a2c]">{showComments ? "-" : "+"}</span>
              </span>
            </button>

            {showComments && (
              analytics.comments.length === 0 ? (
                <div className="mt-5 rounded-lg border border-white/10 bg-white/[0.03] p-5 text-sm text-white/55">
                  No written comments yet.
                </div>
              ) : (
                <div className="mt-5 space-y-3">
                  {analytics.comments.map((item) => (
                    <article key={item.id} className="rounded-lg border border-white/10 bg-white/[0.03] p-4">
                      <div className="flex flex-wrap items-center gap-3 text-xs text-white/45">
                        <span className="capitalize text-white/70">{item.rating}</span>
                        <span>Accuracy: {item.accuracy_score ?? "N/A"}</span>
                        <span>Quality: {item.quality_score ?? "N/A"}</span>
                        <span>Feedback: {formatDate(item.created_at)}</span>
                      </div>
                      <p className="mt-3 text-sm leading-6 text-white/85">{item.comment}</p>
                      {item.prompt && (
                        <p className="mt-3 truncate text-xs text-white/40">
                          Prompt #{item.prompt_id}: {item.prompt}
                        </p>
                      )}
                      {item.modification_command && (
                        <p className="mt-2 truncate text-xs text-[#ff8a2c]/75">
                          Modification: {item.modification_command}
                        </p>
                      )}
                    </article>
                  ))}
                </div>
              )
            )}
          </section>
        </>
      )}
    </PageShell>
  );
}

function PageShell({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children?: ReactNode;
}) {
  return (
    <main className="min-h-screen bg-[#050608] px-6 py-8 text-white sm:px-10">
      <div className="mx-auto max-w-6xl">
        <div className="flex flex-col gap-5 border-b border-white/10 pb-6 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[#ff8a2c]">Feedback</p>
            <h1 className="mt-2 text-3xl font-bold sm:text-4xl">{title}</h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-white/60">{subtitle}</p>
          </div>
          <Link href="/" className="rounded-lg border border-white/10 px-4 py-2 text-sm text-white/80 transition hover:bg-white/[0.06]">
            Back to main page
          </Link>
        </div>
        {children}
      </div>
    </main>
  );
}

function MetricCard({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-lg border border-white/10 bg-[#0b1020]/70 p-5">
      <p className="text-sm text-white/50">{title}</p>
      <p className="mt-3 text-2xl font-bold text-white">{value}</p>
    </div>
  );
}
