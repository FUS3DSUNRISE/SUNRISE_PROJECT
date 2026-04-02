"use client";

import { useGenerationStore } from "@/state/generationStore";

export default function GenerateButton() {
    const setStatus = useGenerationStore((s) => s.setStatus);

    return (
        <button
            onClick={() => setStatus("loading")}
            className="mt-4 w-full bg-black text-white py-2 rounded"
        >
            Generate
        </button>
    );
}