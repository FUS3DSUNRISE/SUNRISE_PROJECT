"use client";

import { useState } from "react";
import { checkBackendConnection } from "@/services/api";
import { useServiceStatusStore } from "@/state/serviceStatusStore";

export default function ServiceUnavailableScreen() {
    const message = useServiceStatusStore((state) => state.message);
    const [isRetrying, setIsRetrying] = useState(false);

    const handleRetry = async () => {
        setIsRetrying(true);
        await checkBackendConnection();
        setIsRetrying(false);
    };

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/35 backdrop-blur-sm"
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="service-unavailable-title"
        >
            <section className="w-full max-w-xl rounded-2xl border border-white/10 bg-[#0f111a] p-8 text-center text-white shadow-xl">
                <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full border border-[#ff8a2c]/40 bg-[#ff8a2c]/10 text-2xl font-bold text-[#ff8a2c]">
                    !
                </div>

                <p className="mt-6 text-xs font-semibold uppercase tracking-[0.22em] text-[#ff8a2c]">
                    Service Unavailable
                </p>
                <h1 id="service-unavailable-title" className="mt-3 text-3xl font-bold">
                    Backend connection failed
                </h1>
                <p className="mx-auto mt-4 max-w-md text-sm leading-6 text-white/65">
                    {message}
                </p>

                <button
                    type="button"
                    onClick={handleRetry}
                    disabled={isRetrying}
                    className="mt-7 inline-flex items-center justify-center gap-3 rounded-xl bg-[#ff8a2c] px-6 py-3 text-sm font-bold text-black transition hover:bg-[#ff9b4d] disabled:cursor-not-allowed disabled:opacity-70"
                >
                    {isRetrying && (
                        <span className="h-4 w-4 animate-spin rounded-full border-2 border-black/25 border-t-black" />
                    )}
                    {isRetrying ? "Checking connection..." : "Retry connection"}
                </button>
            </section>
        </div>
    );
}
