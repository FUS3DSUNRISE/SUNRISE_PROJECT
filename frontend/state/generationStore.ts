import { create } from "zustand";

export type GenerationStatus =
    | "idle"
    | "submitted"
    | "processing"
    | "success"
    | "error";

export interface GenerationResult {
    id: number;
    prompt: string;
    status: string;
    result_path: string | null;
    error_message: string | null;
    user_id?: number;
    username?: string;
}

interface GenerationStore {
    prompt: string;
    status: GenerationStatus;
    errorMessage: string | null;
<<<<<<< HEAD
    resultPath: string | null; // ADDED: will store file path
=======
    result: GenerationResult | null;
>>>>>>> 16332e81f9ab4d3db1e4c7596c736e0b2b1f32e1

    setPrompt: (prompt: string) => void;
    setStatus: (status: GenerationStatus) => void;
    setErrorMessage: (message: string | null) => void;
<<<<<<< HEAD
    setResultPath: (path: string | null) => void; // ADDED: Update feature
=======
    setResult: (result: GenerationResult | null) => void;
>>>>>>> 16332e81f9ab4d3db1e4c7596c736e0b2b1f32e1
    reset: () => void;
}

export const useGenerationStore = create<GenerationStore>((set) => ({
    prompt: "",
    status: "idle",
    errorMessage: null,
<<<<<<< HEAD
    resultPath: null, // ADDED: initial value
=======
    result: null,
>>>>>>> 16332e81f9ab4d3db1e4c7596c736e0b2b1f32e1

    setPrompt: (prompt) => set({ prompt }),
    setStatus: (status) => set({ status }),
    setErrorMessage: (errorMessage) => set({ errorMessage }),
<<<<<<< HEAD
    setResultPath: (resultPath) => set({ resultPath }), // ADDED
=======
    setResult: (result) => set({ result }),
>>>>>>> 16332e81f9ab4d3db1e4c7596c736e0b2b1f32e1

    reset: () =>
        set({
            prompt: "",
            status: "idle",
            errorMessage: null,
<<<<<<< HEAD
            resultPath: null, // ADDED: Cleanup on reset
=======
            result: null,
>>>>>>> 16332e81f9ab4d3db1e4c7596c736e0b2b1f32e1
        }),
}));