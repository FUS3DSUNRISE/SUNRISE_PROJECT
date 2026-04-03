import { create } from "zustand";

type Status = "idle" | "submitted" | "processing" | "success" | "error";

interface Store {
    status: Status;
    setStatus: (s: Status) => void;
}

export const useGenerationStore = create<Store>((set) => ({
    status: "idle",
    setStatus: (status) => set({ status }),
}));