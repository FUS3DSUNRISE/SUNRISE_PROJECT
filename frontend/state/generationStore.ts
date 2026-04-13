import { create } from "zustand";

export type GenerationStatus =
    | "idle"
    | "submitted"
    | "processing"
    | "success"
    | "error";

interface GenerationStore {
    prompt: string;
    status: GenerationStatus;
    errorMessage: string | null;
    resultPath: string | null; // ADDED: will store file path

    setPrompt: (prompt: string) => void;
    setStatus: (status: GenerationStatus) => void;
    setErrorMessage: (message: string | null) => void;
    setResultPath: (path: string | null) => void; // ADDED: Update feature
    reset: () => void;
}

export const useGenerationStore = create<GenerationStore>((set) => ({
    prompt: "",
    status: "idle",
    errorMessage: null,
    resultPath: null, // ADDED: initial value

    setPrompt: (prompt) => set({ prompt }),
    setStatus: (status) => set({ status }),
    setErrorMessage: (errorMessage) => set({ errorMessage }),
    setResultPath: (resultPath) => set({ resultPath }), // ADDED

    reset: () =>
        set({
            prompt: "",
            status: "idle",
            errorMessage: null,
            resultPath: null, // ADDED: Cleanup on reset
        }),
}));