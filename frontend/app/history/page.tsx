"use client";

import Link from "next/link";
import HistoryPanel from "@/components/HistoryPanel";
import { useAuthStore } from "@/state/authStore";

export default function HistoryPage() {
    const user = useAuthStore((s) => s.user);

    return (
        <main className="min-h-screen bg-[#050608] px-8 py-12 text-white">
            <div className="mx-auto max-w-5xl">
                <div className="mb-8 flex items-center justify-between gap-6">
                    <div>
                        <p className="text-sm font-semibold uppercase tracking-[0.22em] text-[#ff8a2c]">
                            User History
                        </p>
                        <h1 className="mt-2 text-4xl font-extrabold">Prompt History</h1>
                        <p className="mt-3 text-white/60">
                            {user
                                ? `Previous prompts and refinement versions for ${user.email}`
                                : "Log in to view saved prompts and refinement versions."}
                        </p>
                    </div>

                    <Link
                        href="/"
                        className="shrink-0 rounded-xl border border-white/10 bg-white/[0.04] px-5 py-3 text-sm font-medium text-white transition hover:bg-white/[0.07]"
                    >
                        Back
                    </Link>
                </div>

                <HistoryPanel />
            </div>
        </main>
    );
}
