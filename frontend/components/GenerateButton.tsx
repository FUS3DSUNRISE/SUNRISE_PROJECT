"use client";

import { useState } from "react";
import { useGenerationStore } from "@/state/generationStore";
import { generateModel } from "@/services/api";
import { useAuthStore } from "@/state/authStore";

export default function GenerateButton() {
    const prompt = useGenerationStore((s) => s.prompt);
    const status = useGenerationStore((s) => s.status);
    const setStatus = useGenerationStore((s) => s.setStatus);
    const setErrorMessage = useGenerationStore((s) => s.setErrorMessage);
<<<<<<< HEAD
    const setResultPath = useGenerationStore((s) => s.setResultPath);
=======
    const setResult = useGenerationStore((s) => s.setResult);
    const user = useAuthStore((s) => s.user);
>>>>>>> 16332e81f9ab4d3db1e4c7596c736e0b2b1f32e1

    const [showSpinner, setShowSpinner] = useState(false);

    const handleGenerate = async () => {
        // Check for empty text
        if (!prompt.trim()) {
            setStatus("error");
            setErrorMessage("Please enter a prompt before generating.");
            return;
        }
        if (!user) {
            setStatus("error");
            setErrorMessage("You must be logged in before generating a model.");
            return;
        }

        // Validation for maximum length (255 characters)
        if (prompt.length > 255) {
            setStatus("error");
            setErrorMessage(`Prompt is too long (${prompt.length}/255 characters). Please shorten it.`);
            return;
        }

        try {
            setErrorMessage(null);
            setResultPath(null); // Clearing the previous result
            setShowSpinner(true);

            setStatus("submitted");

            // API call (pollPrompt updates the status to processing)
            const result = await generateModel(prompt, () => {
                setStatus("processing");
            });

            // If the backend returned success, we keep the real path
            if (result && result.result_path) {
                setResultPath(result.result_path);
                setStatus("success");
            } else {
                throw new Error("Server did not return a file path.");
            }

<<<<<<< HEAD
        } catch (error: any) {
            // Displaying the real error from the backend
=======
            // STEP 3: call API 
            const result = await generateModel(prompt);
            setResult(result);

            // STEP 4: success
            setStatus("success");
        } catch {
            setResult(null);
>>>>>>> 16332e81f9ab4d3db1e4c7596c736e0b2b1f32e1
            setStatus("error");
            setErrorMessage(error.message || "Something went wrong during generation.");
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