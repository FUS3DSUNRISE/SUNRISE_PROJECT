"use client";

import { useGenerationStore } from "@/state/generationStore";

export default function GenerateButton() {
    const status = useGenerationStore((s) => s.status);
    const setStatus = useGenerationStore((s) => s.setStatus);

    // Function that is triggered when clicked
    const handleClick = () => {
        setStatus("submitted");
        
        // This will be where the request to the backend will be sent in the future.
        // For now, we're just simulating a transition to "processing" after 2 seconds.
        setTimeout(() => {
            setStatus("processing");
        }, 2000);
    };

    // Determine what text to display on the button
    let buttonText = "Generate 3D Model";
    if (status === "submitted") buttonText = "Submitting...";
    if (status === "processing") buttonText = "Processing...";
    if (status === "success") buttonText = "Generate Another";
    if (status === "error") buttonText = "Try Again";

    return (
        <button
            onClick={handleClick}
            disabled={status === "submitted" || status === "processing"}
            className="min-w-[560px] rounded-[20px] bg-[#4f5dff] px-10 py-5 text-[24px] font-semibold text-white shadow-[0_12px_30px_rgba(79,93,255,0.35)] transition hover:bg-[#5d69ff] disabled:opacity-50 disabled:cursor-not-allowed"
        >
            {buttonText}
        </button>
    );
}