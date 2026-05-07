"use client";

import { useState } from "react";
import { useGenerationStore } from "@/state/generationStore";
import { generateModel } from "@/services/api";
import { useAuthStore } from "@/state/authStore";

type GenerateButtonProps = {
    disabled?: boolean;
};

const MAX_PROMPT_LENGTH = 120;
const FORBIDDEN_CHARACTERS_REGEX = /[<>[\]{}]/;

export default function GenerateButton({ disabled = false }: GenerateButtonProps) {
    const prompt = useGenerationStore((s) => s.prompt);
    const parameters = useGenerationStore((s) => s.parameters);
    const status = useGenerationStore((s) => s.status);
    const setStatus = useGenerationStore((s) => s.setStatus);
    const setErrorMessage = useGenerationStore((s) => s.setErrorMessage);
    const setResult = useGenerationStore((s) => s.setResult);

    const user = useAuthStore((s) => s.user);

    const [showSpinner, setShowSpinner] = useState(false);

    const getFormattedParameters = () => ({
        size: parameters.size,
        geometry: parameters.geometry,
        material: {
            material_type:
                parameters.material.type.charAt(0).toUpperCase() +
                parameters.material.type.slice(1),
            roughness: parameters.material.roughness,
            metallic: parameters.material.metallic,
        },
    });

    const handleGenerate = async () => {
        if (!prompt.trim()) {
            setStatus("error");
            setErrorMessage("Prompt cannot be empty.");
            return;
        }

        if (prompt.length > MAX_PROMPT_LENGTH) {
            setStatus("error");
            setErrorMessage(`Prompt is too long. Maximum length is ${MAX_PROMPT_LENGTH} characters.`);
            return;
        }

        if (FORBIDDEN_CHARACTERS_REGEX.test(prompt)) {
            setStatus("error");
            setErrorMessage("Prompt contains forbidden characters: < > [ ] { }");
            return;
        }

        if (!user) {
            setStatus("error");
            setErrorMessage("You must be logged in before generating a model.");
            return;
        }

        try {
            setErrorMessage(null);
            setShowSpinner(true);

            const payload = {
                prompt,
                parameters: getFormattedParameters(),
            };

            setStatus("submitted");
            await new Promise((resolve) => setTimeout(resolve, 500));

            const result = await generateModel(payload, () => {
                setStatus("processing");
            });

            setResult(result);
            setStatus("success");
        } catch (error: unknown) {
            console.error("Generation failed:", error);
            setResult(null);
            setStatus("error");
            setErrorMessage(
                error instanceof Error
                    ? error.message
                    : "Something went wrong during generation."
            );
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
            disabled={disabled || status === "submitted" || status === "processing"}
            className="w-full rounded-[18px] bg-[#ff8a2c] px-8 py-4 text-[20px] font-semibold text-black shadow-[0_12px_30px_rgba(255,138,44,0.28)] transition hover:bg-[#ff9b4d] disabled:cursor-not-allowed disabled:opacity-50"
        >
            <span className="flex items-center justify-center gap-3">
                {showSpinner && (
                    <span className="h-6 w-6 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                )}
                {buttonText}
            </span>
        </button>
    );
}
