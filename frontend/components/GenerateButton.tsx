"use client";

import { useState } from "react";
import { useGenerationStore } from "@/state/generationStore";
import { generateModel } from "@/services/api";

export default function GenerateButton() {
    const prompt = useGenerationStore((s) => s.prompt);
    const status = useGenerationStore((s) => s.status);
    const setStatus = useGenerationStore((s) => s.setStatus);
    const setErrorMessage = useGenerationStore((s) => s.setErrorMessage);
    const setResult = useGenerationStore((s) => s.setResult);

    const [showSpinner, setShowSpinner] = useState(false);

    const handleGenerate = async () => {
        if (!prompt.trim()) {
            setStatus("error");
            setErrorMessage("Please enter a prompt before generating.");
            return;
        }

        try {
            setErrorMessage(null);
            setShowSpinner(true);

            // STEP 1: submitted
            setStatus("submitted");

            await new Promise((resolve) => setTimeout(resolve, 500));

            // STEP 2: processing
            setStatus("processing");

            // STEP 3: call API 
            const result = await generateModel(prompt);
            setResult(result);

            // STEP 4: success
            setStatus("success");
        } catch {
            setStatus("error");
            setErrorMessage("Something went wrong during generation.");
        } finally {
            setShowSpinner(false);
        }
    };

    const buttonText =
        status === "submitted"
            ? "Generating..." 
            : status === "processing"
                ? "Processing..." 
                : status === "success"
                    ? "Generate Another" 
                    : status === "error"
                        ? "Try Again"
                        : "Generate 3D Model";

    return (
        <button
            onClick={handleGenerate}
            disabled={status === "submitted" || status === "processing"}
            className="w-full rounded-[18px] bg-[#ff8a2c] px-8 py-4 text-[20px] font-semibold text-black shadow-[0_12px_30px_rgba(255,138,44,0.28)] transition hover:bg-[#ff9b4d] disabled:cursor-not-allowed disabled:opacity-70">
            <span className="flex items-center justify-center gap-3">
                {showSpinner && (
                    <span className="h-6 w-6 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                )}
                {buttonText}
            </span>
        </button>
    );
}