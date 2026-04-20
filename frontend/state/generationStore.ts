import { create } from "zustand";
import { ModelParameters } from "@/components/ParameterPanel"; // Adding imports

export type GenerationStatus = "idle" | "submitted" | "processing" | "success" | "error";

export interface GenerationResult {
    id: number;
    prompt: string;
    status: string;
    result_path: string | null;
    error_message: string | null;
    user_id?: number;
    username?: string;
}

// Standard parameters
const defaultParameters: ModelParameters = {
    size: { width: 1.5, height: 1.5, depth: 1.5 },
    geometry: { complexity: 5, smoothness: 50 },
    material: { type: "plastic", roughness: 0.5, metallic: 0.2 },
};

interface GenerationStore {
    prompt: string;
    modifyCommand: string; // ADDED
    parameters: ModelParameters; // ADDED
    status: GenerationStatus;
    errorMessage: string | null;
    result: GenerationResult | null;

    setPrompt: (prompt: string) => void;
    setModifyCommand: (command: string) => void; // ADDED
    setParameters: (params: ModelParameters) => void; // ADDED
    setStatus: (status: GenerationStatus) => void;
    setErrorMessage: (message: string | null) => void;
    setResult: (result: GenerationResult | null) => void;
    reset: () => void;
}

export const useGenerationStore = create<GenerationStore>((set) => ({
    prompt: "",
    modifyCommand: "", // ADDED
    parameters: defaultParameters, // ADDED
    status: "idle",
    errorMessage: null,
    result: null,

    setPrompt: (prompt) => set({ prompt }),
    setModifyCommand: (modifyCommand) => set({ modifyCommand }), // ADDED
    setParameters: (parameters) => set({ parameters }), // ADDED
    setStatus: (status) => set({ status }),
    setErrorMessage: (errorMessage) => set({ errorMessage }),
    setResult: (result) => set({ result }),

    reset: () =>
        set({
            prompt: "",
            modifyCommand: "",
            parameters: defaultParameters,
            status: "idle",
            errorMessage: null,
            result: null,
        }),
}));