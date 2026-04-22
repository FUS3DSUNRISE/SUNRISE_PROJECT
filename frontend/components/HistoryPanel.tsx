"use client";

type HistoryItem = {
    id: number;
    prompt: string;
    status: "completed" | "processing" | "failed";
    modelLabel: string;
};

const mockHistory: HistoryItem[] = [
    {
        id: 62,
        prompt: "green chair",
        status: "completed",
        modelLabel: "Chair",
    },
    {
        id: 61,
        prompt: "orange crystal",
        status: "processing",
        modelLabel: "Crystal",
    },
    {
        id: 60,
        prompt: "wooden table",
        status: "completed",
        modelLabel: "Table",
    },
    {
        id: 59,
        prompt: "cute tiger figure",
        status: "failed",
        modelLabel: "Tiger",
    },
];

function getStatusClass(status: HistoryItem["status"]) {
    if (status === "completed") return "text-green-400";
    if (status === "processing") return "text-yellow-400";
    return "text-red-400";
}

function getStatusDotClass(status: HistoryItem["status"]) {
    if (status === "completed") return "bg-green-400";
    if (status === "processing") return "bg-yellow-400";
    return "bg-red-400";
}

export default function HistoryPanel() {
    return (
        <div className="mt-6 rounded-[26px] border border-white/5 bg-[#0b1020]/70 p-5 shadow-inner">
            <div className="mb-4 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-white">History</h2>
                <span className="text-xs uppercase tracking-[0.2em] text-white/35">
                    Mock data
                </span>
            </div>

            <div className="space-y-3">
                {mockHistory.map((item) => (
                    <div
                        key={item.id}
                        className="flex items-center gap-4 rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-4 transition hover:bg-white/[0.05]"
                    >
                        <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-xl border border-white/10 bg-[#11131f] text-xs font-semibold uppercase tracking-wide text-white/70">
                            {item.modelLabel}
                        </div>

                        <div className="min-w-0 flex-1">
                            <p className="truncate text-sm font-medium text-white">
                                {item.prompt}
                            </p>
                            <p className="mt-1 text-xs text-white/40">
                                Prompt ID: {item.id}
                            </p>
                        </div>

                        <div className="shrink-0 text-right">
                            <div className="flex items-center justify-end gap-2">
                                <span
                                    className={`h-2.5 w-2.5 rounded-full ${getStatusDotClass(item.status)}`}
                                />
                                <span
                                    className={`text-xs font-medium capitalize ${getStatusClass(item.status)}`}
                                >
                                    {item.status}
                                </span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}