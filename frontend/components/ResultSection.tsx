"use client";

import { useGenerationStore } from "@/state/generationStore";

export default function ResultSection() {
    const status = useGenerationStore((s) => s.status);

    return (
        <div className="mt-4">
            {status === "idle" && <p>Waiting for input...</p>}
            {status === "loading" && <p>Generating...</p>}
            {status === "success" && <p>Model ready</p>}
            {status === "error" && <p>Error occurred</p>}
        </div>
    );
}