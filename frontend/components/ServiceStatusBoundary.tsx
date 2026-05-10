"use client";

import type { ReactNode } from "react";
import ServiceUnavailableScreen from "@/components/ServiceUnavailableScreen";
import { useServiceStatusStore } from "@/state/serviceStatusStore";

export default function ServiceStatusBoundary({ children }: { children: ReactNode }) {
    const status = useServiceStatusStore((state) => state.status);

    return (
        <>
            {children}
            {status === "unavailable" && <ServiceUnavailableScreen />}
        </>
    );
}
