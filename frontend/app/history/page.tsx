"use client";

import Link from "next/link";
import { useAuthStore } from "@/state/authStore";

type HistoryItem = {
    id: number;
    prompt: string;
    status: "completed" | "processing" | "failed";
    modelLabel: string;
};

const mockHistory: HistoryItem[] = [
    { id: 62, prompt: "green chair", status: "completed", modelLabel: "Chair" },
    { id: 61, prompt: "orange crystal", status: "processing", modelLabel: "Crystal" },
    { id: 60, prompt: "wooden table", status: "completed", modelLabel: "Table" },
    { id: 59, prompt: "cute tiger figure", status: "failed", modelLabel: "Tiger" },
];

function getStatusClass(status: HistoryItem["status"]) {
    if (status === "completed") return "text-green-400";
    if (status === "processing") return "text-yellow-400";
    return "text-red-400";
}

function getStatusDotClass(status: HistoryItem["status"]) {
    if (status === "completed") return "bg-green-400";
    if (status === "processing") return "bg-yellow-400";
    return "bg-red-400";
}

export default function HistoryPage() {
    const user = useAuthStore((s) => s.user);

    if (!user) {
        return (
            <main className="min-h-screen bg-[#050608] px-8 py-12 text-white">
                <div className="mx-auto max-w-4xl">
                    <div className="rounded-[24px] border border-white/10 bg-[#0b1020]/50 p-8 shadow-inner">
                        <h1 className="text-3xl font-bold">History</h1>
                        <p className="mt-4 text-white/60">
                            You need to be logged in to view history.
                        </p>

                        <Link
                            href="/"
                            className="mt-6 inline-block rounded-xl border border-white/10 bg-white/[0.04] px-5 py-3 text-sm font-medium text-white transition hover:bg-white/[0.07]"
                        >
                            Back to Home
                        </Link>
                    </div>
                </div>
            </main>
        );
    }

    return (
        <main className="min-h-screen bg-[#050608] px-8 py-12 text-white">
            <div className="mx-auto max-w-5xl">
                <div className="mb-8 flex items-center justify-between">
                    <div>
                        <p className="text-sm font-semibold uppercase tracking-[0.22em] text-[#ff8a2c]">
                            User History
                        </p>
                        <h1 className="mt-2 text-4xl font-extrabold">Prompt History</h1>
                        <p className="mt-3 text-white/60">
                            Previous prompts and mock generation results for {user.email}
                        </p>
                    </div>

                    <Link
                        href="/"
                        className="rounded-xl border border-white/10 bg-white/[0.04] px-5 py-3 text-sm font-medium text-white transition hover:bg-white/[0.07]"
                    >
                        Back
                    </Link>
                </div>

                <div className="rounded-[24px] border border-white/10 bg-[#0b1020]/50 p-6 shadow-inner">
                    <div className="space-y-4">
                        {mockHistory.map((item) => (
                            <div
                                key={item.id}
                                className="flex items-center gap-4 rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-4"
                            >
                                <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-xl border border-white/10 bg-[#11131f] text-xs font-semibold uppercase tracking-wide text-white/70">
                                    {item.modelLabel}
                                </div>

                                <div className="min-w-0 flex-1">
                                    <p className="truncate text-sm font-medium text-white">
                                        {item.prompt}
                                    </p>
                                    <p className="mt-1 text-xs text-white/40">
                                        Prompt ID: {item.id}
                                    </p>
                                </div>

                                <div className="shrink-0 text-right">
                                    <div className="flex items-center justify-end gap-2">
                                        <span
                                            className={`h-2.5 w-2.5 rounded-full ${getStatusDotClass(item.status)}`}
                                        />
                                        <span
                                            className={`text-xs font-medium capitalize ${getStatusClass(item.status)}`}
                                        >
                                            {item.status}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </main>
    );
}