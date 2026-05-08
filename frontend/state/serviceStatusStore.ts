import { create } from "zustand";

type ServiceStatus = "available" | "unavailable";

interface ServiceStatusStore {
    status: ServiceStatus;
    message: string | null;
    setUnavailable: (message?: string) => void;
    setAvailable: () => void;
}

export const useServiceStatusStore = create<ServiceStatusStore>((set) => ({
    status: "available",
    message: null,
    setUnavailable: (message) =>
        set({
            status: "unavailable",
            message:
                message ??
                "The backend API is not responding. Check that the service is running, then try again.",
        }),
    setAvailable: () =>
        set({
            status: "available",
            message: null,
        }),
}));
