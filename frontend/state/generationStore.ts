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
    result: GenerationResult | null;


    setPrompt: (prompt: string) => void;
    setStatus: (status: GenerationStatus) => void;
    setErrorMessage: (message: string | null) => void;
    setResult: (result: GenerationResult | null) => void;
    reset: () => void;
}


export const useGenerationStore = create<GenerationStore>((set) => ({
    prompt: "",
    status: "idle",
    errorMessage: null,
    result: null,


    setPrompt: (prompt) => set({ prompt }),
    setStatus: (status) => set({ status }),
    setErrorMessage: (errorMessage) => set({ errorMessage }),
    setResult: (result) => set({ result }),


    reset: () =>
        set({
            prompt: "",
            status: "idle",
            errorMessage: null,
            result: null,
        }),
}));
