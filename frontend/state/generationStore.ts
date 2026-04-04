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

    setPrompt: (prompt: string) => void;
    setStatus: (status: GenerationStatus) => void;
    setErrorMessage: (message: string | null) => void;
    reset: () => void;
}

export const useGenerationStore = create<GenerationStore>((set) => ({
    prompt: "",
    status: "idle",
    errorMessage: null,

    setPrompt: (prompt) => set({ prompt }),
    setStatus: (status) => set({ status }),
    setErrorMessage: (errorMessage) => set({ errorMessage }),

    reset: () =>
        set({
            prompt: "",
            status: "idle",
            errorMessage: null,
        }),
}));