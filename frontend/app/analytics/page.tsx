"use client";

import { useEffect, useState } from "react";
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

const COLORS = ["#f9a8d4", "#fb7185", "#fbcfe8"];

export default function AnalyticsPage() {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    fetch("http://127.0.0.1:5000/prompts/feedback/analytics", {
      credentials: "include",
    })
      .then((res) => res.json())
      .then((d) => setData(d))
      .catch((err) => setData({ error: err.message }));
  }, []);

  if (!data) {
    return <div className="min-h-screen bg-[#0b0b12] p-10 text-white">Loading...</div>;
  }

  if (data.error) {
    return (
      <div className="min-h-screen bg-[#0b0b12] p-10 text-red-300">
        Error: {data.error}
      </div>
    );
  }

  const ratingData = Object.entries(data.ratings ?? {}).map(([key, value]) => ({
    name: key,
    value: Number(value),
  }));

  const successRate = Number(data.success_rate ?? 0);
  const failingRate = Number((100 - successRate).toFixed(2));

  return (
    <div className="min-h-screen bg-[#0b0b12] p-10 text-white">
      <div className="mb-10">
        <p className="text-sm uppercase tracking-widest text-pink-300">
          LLM Evaluation
        </p>
        <h1 className="mt-2 text-4xl font-bold">Analytics Dashboard</h1>
        <p className="mt-3 text-slate-400">
          Monitor LLM generation quality through user feedback.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-4">
        <Card title="Success Rate" value={`${successRate}%`} />
        <Card title="Failing Rate" value={`${failingRate}%`} />
        <Card title="Accuracy" value={data.average_accuracy_score ?? "N/A"} />
        <Card title="Quality" value={data.average_quality_score ?? "N/A"} />
      </div>

      <div className="mt-10 grid grid-cols-1 gap-8 lg:grid-cols-2">
        <div className="rounded-2xl border border-pink-200/10 bg-[#15151f] p-6 shadow-xl">
          <h2 className="text-xl font-semibold text-pink-100">
            Feedback Distribution
          </h2>

          <div className="mt-6 h-[320px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={ratingData}
                  dataKey="value"
                  nameKey="name"
                  outerRadius={110}
                  label
                >
                  {ratingData.map((_, index) => (
                    <Cell key={index} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-2xl border border-pink-200/10 bg-[#15151f] p-6 shadow-xl">
          <h2 className="text-xl font-semibold text-pink-100">
            LLM Performance
          </h2>

          <div className="mt-6 h-[320px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={[
                  {
                    name: "Generation",
                    success: successRate,
                    fail: failingRate,
                  },
                ]}
              >
                <XAxis dataKey="name" stroke="#fbcfe8" />
                <YAxis stroke="#fbcfe8" />
                <Tooltip />
                <Bar dataKey="success" fill="#f9a8d4" />
                <Bar dataKey="fail" fill="#fb7185" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}

function Card({ title, value }: any) {
  return (
    <div className="rounded-2xl border border-pink-200/10 bg-[#15151f] p-6 shadow-xl">
      <p className="text-sm text-slate-400">{title}</p>
      <p className="mt-3 text-3xl font-bold text-pink-200">{value}</p>
    </div>
  );
}