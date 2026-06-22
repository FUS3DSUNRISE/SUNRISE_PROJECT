"use client";

import { useEffect, useMemo, useState, type MouseEvent } from "react";
import {
    deletePromptHistory,
    deletePromptVersion,
    getMyPrompts,
    getPrompt,
    getUserFriendlyErrorMessage,
    type PromptResponse,
    type PromptVersionSummary,
} from "@/services/api";
import { useAuthStore } from "@/state/authStore";

type HistorySortOrder = "newest" | "oldest";

type HistoryPanelProps = {
    activePromptId?: number | null;
    className?: string;
    onSelectPrompt?: (prompt: PromptResponse) => void;
};

type PendingDelete =
    | { type: "history"; promptId: number; title: string; description: string }
    | { type: "version"; promptId: number; title: string; description: string };

function getStatusClass(status: string) {
    if (status === "completed") return "text-green-400";
    if (status === "queued" || status === "processing" || status === "awaiting_clarification") {
        return "text-yellow-400";
    }
    return "text-red-400";
}

function getStatusDotClass(status: string) {
    if (status === "completed") return "bg-green-400";
    if (status === "queued" || status === "processing" || status === "awaiting_clarification") {
        return "bg-yellow-400";
    }
    return "bg-red-400";
}

function getModelLabel(item: Pick<PromptVersionSummary, "result_path" | "id">) {
    if (!item.result_path) return `#${item.id}`;

    const fileName = decodeURIComponent(item.result_path.split(/[\\/]/).pop() || "");
    return fileName.replace(/\.(glb|gltf|obj)$/i, "") || `#${item.id}`;
}

function getSortValue(item: PromptVersionSummary) {
    if (!item.created_at) return item.id;

    const timestamp = new Date(item.created_at).getTime();
    return Number.isNaN(timestamp) ? item.id : timestamp;
}

function sortNewestFirst(prompts: PromptVersionSummary[]) {
    return [...prompts].sort((a, b) => getSortValue(b) - getSortValue(a));
}

function sortPrompts(prompts: PromptVersionSummary[], order: HistorySortOrder) {
    const sorted = sortNewestFirst(prompts);
    return order === "newest" ? sorted : sorted.reverse();
}

function getPromptTitle(item: PromptVersionSummary) {
    return item.prompt || getModelLabel(item) || `Prompt ${item.id}`;
}

function formatGeneratedAt(createdAt: string | null | undefined) {
    if (!createdAt) return null;

    const date = new Date(createdAt);
    if (Number.isNaN(date.getTime())) return null;

    return {
        date: new Intl.DateTimeFormat("en-US", {
            month: "short",
            day: "numeric",
            year: "numeric",
        }).format(date),
        time: new Intl.DateTimeFormat("en-US", {
            hour: "2-digit",
            minute: "2-digit",
            hour12: false,
        }).format(date),
    };
}

function formatParametersSummary(item: PromptVersionSummary) {
    const parameters = item.parameters;
    if (!parameters) return null;

    const materialType = parameters.material.material_type.toLowerCase();

    return [
        `${parameters.size.width}x${parameters.size.height}x${parameters.size.depth}`,
        materialType,
    ].join(" - ");
}

export default function HistoryPanel({ activePromptId, className = "", onSelectPrompt }: HistoryPanelProps) {
    const user = useAuthStore((s) => s.user);
    const [prompts, setPrompts] = useState<PromptVersionSummary[]>([]);
    const [versions, setVersions] = useState<PromptVersionSummary[]>([]);
    const [expandedPromptId, setExpandedPromptId] = useState<number | null>(null);
    const [searchQuery, setSearchQuery] = useState("");
    const [sortOrder, setSortOrder] = useState<HistorySortOrder>("newest");
    const [loadingPrompts, setLoadingPrompts] = useState(false);
    const [loadingVersions, setLoadingVersions] = useState(false);
    const [loadingPromptId, setLoadingPromptId] = useState<number | null>(null);
    const [deletingPromptId, setDeletingPromptId] = useState<number | null>(null);
    const [deletingHistoryId, setDeletingHistoryId] = useState<number | null>(null);
    const [pendingDelete, setPendingDelete] = useState<PendingDelete | null>(null);
    const [error, setError] = useState<string | null>(null);

    const visiblePrompts = useMemo(() => {
        const normalizedQuery = searchQuery.trim().toLowerCase();
        const filteredPrompts = normalizedQuery
            ? prompts.filter((item) => {
                const searchableText = [
                    item.id,
                    item.prompt,
                    item.modification_command,
                    item.status,
                    item.result_path,
                    getModelLabel(item),
                ].join(" ").toLowerCase();

                return searchableText.includes(normalizedQuery);
            })
            : prompts;

        return sortPrompts(filteredPrompts, sortOrder);
    }, [prompts, searchQuery, sortOrder]);

    useEffect(() => {
        let isMounted = true;

        async function loadPrompts() {
            if (!user) {
                setPrompts([]);
                setVersions([]);
                setExpandedPromptId(null);
                return;
            }

            try {
                setLoadingPrompts(true);
                setError(null);
                const data = await getMyPrompts();

                if (isMounted) {
                    setPrompts(data.prompts);

                    const promptsWithoutDates = data.prompts.filter((item) => !item.created_at);

                    if (promptsWithoutDates.length > 0) {
                        Promise.allSettled(
                            promptsWithoutDates.map((item) => getPrompt(item.id))
                        ).then((results) => {
                            if (!isMounted) return;

                            const promptsById = new Map<number, PromptResponse>();

                            results.forEach((result) => {
                                if (result.status === "fulfilled") {
                                    promptsById.set(result.value.id, result.value);
                                }
                            });

                            if (promptsById.size === 0) return;

                            setPrompts((currentPrompts) =>
                                currentPrompts.map((item) => {
                                    const detail = promptsById.get(item.id);

                                    if (!detail) return item;

                                    return {
                                        ...item,
                                        prompt: detail.prompt,
                                        result_path: detail.result_path,
                                        error_message: detail.error_message,
                                        parameters: detail.parameters,
                                        modification_command: detail.modification_command,
                                        created_at: detail.created_at,
                                    };
                                })
                            );
                        });
                    }
                }
            } catch (loadError) {
                if (isMounted) {
                    const message = getUserFriendlyErrorMessage(loadError, "Failed to load prompt history");
                    setError(message);
                }
            } finally {
                if (isMounted) {
                    setLoadingPrompts(false);
                }
            }
        }

        loadPrompts();

        return () => {
            isMounted = false;
        };
    }, [user, activePromptId]);

    const loadVersions = async (promptId: number) => {
        if (expandedPromptId === promptId) {
            setExpandedPromptId(null);
            setVersions([]);
            return;
        }

        try {
            setExpandedPromptId(promptId);
            setLoadingVersions(true);
            setError(null);
            const detail = await getPrompt(promptId);
            const nextVersions = detail.version_history?.length
                ? detail.version_history
                : [{
                    id: detail.id,
                    parent_prompt_id: detail.parent_prompt_id,
                    prompt: detail.prompt,
                    status: detail.status,
                    result_path: detail.result_path,
                    error_message: detail.error_message,
                    parameters: detail.parameters,
                    modification_command: detail.modification_command,
                    created_at: detail.created_at,
                }];

            setVersions(nextVersions);
        } catch (loadError) {
            setVersions([]);
            const message = getUserFriendlyErrorMessage(loadError, "Failed to load versions");
            setError(message);
        } finally {
            setLoadingVersions(false);
        }
    };

    const versionList = useMemo(() => {
        const sortedVersions = [...versions].sort((a, b) => getSortValue(a) - getSortValue(b));
        return sortOrder === "newest" ? sortedVersions.reverse() : sortedVersions;
    }, [versions, sortOrder]);

    const selectVersion = async (promptId: number) => {
        if (!onSelectPrompt) return;

        try {
            setLoadingPromptId(promptId);
            setError(null);
            const detail = await getPrompt(promptId);
            onSelectPrompt(detail);
        } catch (loadError) {
            const message = getUserFriendlyErrorMessage(loadError, "Failed to load this version");
            setError(message);
        } finally {
            setLoadingPromptId(null);
        }
    };

    const refreshPrompts = async () => {
        const data = await getMyPrompts();
        setPrompts(data.prompts);
        return data.prompts;
    };

    const refreshExpandedVersions = async (promptId: number | null) => {
        if (!promptId) return;

        try {
            const detail = await getPrompt(promptId);
            setVersions(detail.version_history ?? []);
        } catch {
            setExpandedPromptId(null);
            setVersions([]);
        }
    };

    const handleDeleteHistory = async (
        event: MouseEvent<HTMLButtonElement>,
        promptId: number
    ) => {
        event.stopPropagation();

        setPendingDelete({
            type: "history",
            promptId,
            title: "Delete history card?",
            description: "This will remove the selected card and all of its saved versions.",
        });
    };

    const deleteHistory = async (promptId: number) => {

        try {
            setDeletingHistoryId(promptId);
            setError(null);
            const result = await deletePromptHistory(promptId);
            const deletedIds = new Set(result.deleted_ids ?? [promptId]);

            setPrompts((currentPrompts) =>
                currentPrompts.filter((item) => !deletedIds.has(item.id))
            );
            setVersions((currentVersions) =>
                currentVersions.filter((item) => !deletedIds.has(item.id))
            );

            if (expandedPromptId && deletedIds.has(expandedPromptId)) {
                setExpandedPromptId(null);
                setVersions([]);
            }
        } catch (deleteError) {
            const message = getUserFriendlyErrorMessage(deleteError, "Failed to delete this history card");
            setError(message);
        } finally {
            setDeletingHistoryId(null);
        }
    };

    const handleDeleteVersion = async (
        event: MouseEvent<HTMLButtonElement>,
        promptId: number
    ) => {
        event.stopPropagation();

        setPendingDelete({
            type: "version",
            promptId,
            title: "Delete this version?",
            description: "This version will be removed from history. Other versions stay available.",
        });
    };

    const deleteVersion = async (promptId: number) => {

        try {
            setDeletingPromptId(promptId);
            setError(null);
            await deletePromptVersion(promptId);
            await refreshPrompts();

            if (expandedPromptId === promptId) {
                setExpandedPromptId(null);
                setVersions([]);
            } else {
                await refreshExpandedVersions(expandedPromptId);
            }
        } catch (deleteError) {
            const message = getUserFriendlyErrorMessage(deleteError, "Failed to delete this version");
            setError(message);
        } finally {
            setDeletingPromptId(null);
        }
    };

    const confirmPendingDelete = async () => {
        if (!pendingDelete) return;

        const deleteRequest = pendingDelete;
        setPendingDelete(null);

        if (deleteRequest.type === "history") {
            await deleteHistory(deleteRequest.promptId);
            return;
        }

        await deleteVersion(deleteRequest.promptId);
    };

    const deleteConfirmation = pendingDelete ? (
        <div className="absolute inset-0 z-20 flex items-start justify-center bg-black/35 px-4 pt-5 backdrop-blur-sm">
            <div
                className="w-full max-w-md rounded-2xl border border-white/10 bg-[#030407] px-4 py-3.5 shadow-2xl shadow-black/60"
                role="alertdialog"
                aria-modal="true"
                aria-labelledby="history-delete-title"
                aria-describedby="history-delete-description"
            >
                <div className="mb-3 flex min-w-0 items-start gap-3">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-red-400/25 bg-red-500/10 text-red-200">
                        <svg
                            aria-hidden="true"
                            viewBox="0 0 24 24"
                            className="h-4 w-4"
                            fill="none"
                            stroke="currentColor"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth="2"
                        >
                            <path d="M3 6h18" />
                            <path d="M8 6V4h8v2" />
                            <path d="M19 6l-1 14H6L5 6" />
                            <path d="M10 11v5" />
                            <path d="M14 11v5" />
                        </svg>
                    </div>
                    <div className="min-w-0">
                        <h3 id="history-delete-title" className="text-sm font-semibold text-white">
                            {pendingDelete.title}
                        </h3>
                        <p id="history-delete-description" className="mt-1 text-xs leading-5 text-white/55">
                            {pendingDelete.description}
                        </p>
                    </div>
                </div>

                <div className="flex justify-end gap-2">
                    <button
                        type="button"
                        onClick={() => setPendingDelete(null)}
                        className="h-9 rounded-xl border border-white/10 bg-white/[0.04] px-4 text-sm font-medium text-white/75 transition hover:bg-white/[0.08]"
                    >
                        Cancel
                    </button>
                    <button
                        type="button"
                        onClick={confirmPendingDelete}
                        className="h-9 rounded-xl border border-red-300/35 bg-red-500/15 px-4 text-sm font-semibold text-red-100 transition hover:border-red-300/60 hover:bg-red-500/25"
                    >
                        Delete
                    </button>
                </div>
            </div>
        </div>
    ) : null;

    return (
        <>
        <div className={`relative mt-6 flex min-h-0 flex-col overflow-hidden rounded-[26px] border border-white/5 bg-[#0b1020]/70 shadow-inner ${className}`}>
            <div className="px-5 pb-4 pt-5">
                <div className="mb-4 flex items-center justify-between gap-4">
                    <div>
                        <h2 className="text-lg font-semibold text-white">History</h2>
                        <p className="mt-1 text-xs text-white/45">Saved prompts and refinement branches</p>
                    </div>
                </div>

                {user && (
                    <div className="flex gap-2">
                        <div className="relative min-w-0 flex-1">
                            <svg
                                aria-hidden="true"
                                viewBox="0 0 24 24"
                                className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/35"
                                fill="none"
                                stroke="currentColor"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth="2"
                            >
                                <path d="m21 21-4.3-4.3" />
                                <circle cx="11" cy="11" r="7" />
                            </svg>
                            <input
                                type="search"
                                value={searchQuery}
                                onChange={(event) => setSearchQuery(event.target.value)}
                                placeholder="Search history"
                                className="h-11 w-full rounded-xl border border-white/10 bg-white/[0.04] pl-10 pr-3 text-sm text-white outline-none transition placeholder:text-white/35 focus:border-[#ff8a2c]/70"
                            />
                        </div>

                        <select
                            value={sortOrder}
                            onChange={(event) => setSortOrder(event.target.value as HistorySortOrder)}
                            className="h-11 shrink-0 cursor-pointer rounded-xl border border-white/10 bg-[#11131f] px-3 text-sm font-medium text-white outline-none transition focus:border-[#ff8a2c]/70"
                            aria-label="History order"
                        >
                            <option value="newest">Newest</option>
                            <option value="oldest">Oldest</option>
                        </select>
                    </div>
                )}
            </div>

            <div className="min-h-0 flex-1 overflow-y-auto px-5 pb-4 [scrollbar-color:#5a5a5a_#151515] [scrollbar-width:thin] [&::-webkit-scrollbar]:w-2 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-[#5a5a5a] [&::-webkit-scrollbar-thumb:hover]:bg-[#6a6a6a] [&::-webkit-scrollbar-track]:rounded-full [&::-webkit-scrollbar-track]:bg-[#151515]">
                {!user ? (
                <div className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-5 text-sm text-white/55">
                    Log in to see your saved prompt history.
                </div>
            ) : loadingPrompts ? (
                <div className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-5 text-sm text-white/55">
                    Loading history...
                </div>
            ) : visiblePrompts.length === 0 ? (
                <div className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-5 text-sm text-white/55">
                    {searchQuery.trim() ? "No matching prompts found." : "No saved prompts yet."}
                </div>
            ) : (
                <div className="space-y-3">
                    {visiblePrompts.map((item) => {
                        const isExpanded = expandedPromptId === item.id;
                        const isActive = activePromptId === item.id;
                        const generatedAt = formatGeneratedAt(item.created_at);

                        return (
                            <div
                                key={item.id}
                                className={`group/card relative rounded-2xl border bg-white/[0.03] transition ${isActive
                                        ? "border-[#ff8a2c]/80"
                                        : "border-white/10 hover:bg-white/[0.05]"
                                    }`}
                            >
                                <button
                                    type="button"
                                    onClick={() => loadVersions(item.id)}
                                    className="block w-full cursor-pointer py-3 pl-4 pr-12 text-left"
                                >
                                    <div className="flex items-start justify-between gap-4">
                                        <div className="min-w-0">
                                            <p className="truncate text-sm font-semibold text-white">
                                                {getPromptTitle(item)}
                                            </p>
                                            <p className="mt-1 text-xs text-white/40">
                                                Prompt ID: {item.id}
                                            </p>
                                            {item.modification_command && (
                                                <p className="mt-1 truncate text-xs text-white/55">
                                                    Modification: {item.modification_command}
                                                </p>
                                            )}
                                        </div>
                                        <div className="flex items-center justify-end gap-2">
                                            <span className={`h-2.5 w-2.5 rounded-full ${getStatusDotClass(item.status)}`} />
                                            <span className={`text-xs font-medium capitalize ${getStatusClass(item.status)}`}>
                                                {item.status.replaceAll("_", " ")}
                                            </span>
                                        </div>
                                    </div>

                                    <div className="mt-2 flex items-center justify-between gap-3">
                                        {generatedAt ? (
                                            <div className="flex min-w-0 items-center gap-3 whitespace-nowrap text-[11px] text-white/40">
                                                <span className="inline-flex shrink-0 items-center gap-1">
                                                    <svg
                                                        aria-hidden="true"
                                                        viewBox="0 0 24 24"
                                                        className="h-3.5 w-3.5"
                                                        fill="none"
                                                        stroke="currentColor"
                                                        strokeLinecap="round"
                                                        strokeLinejoin="round"
                                                        strokeWidth="2"
                                                    >
                                                        <path d="M8 2v4" />
                                                        <path d="M16 2v4" />
                                                        <rect x="3" y="4" width="18" height="18" rx="2" />
                                                        <path d="M3 10h18" />
                                                    </svg>
                                                    {generatedAt.date}
                                                </span>
                                                <span className="inline-flex shrink-0 items-center gap-1">
                                                    <svg
                                                        aria-hidden="true"
                                                        viewBox="0 0 24 24"
                                                        className="h-3.5 w-3.5"
                                                        fill="none"
                                                        stroke="currentColor"
                                                        strokeLinecap="round"
                                                        strokeLinejoin="round"
                                                        strokeWidth="2"
                                                    >
                                                        <circle cx="12" cy="12" r="9" />
                                                        <path d="M12 7v5l3 2" />
                                                    </svg>
                                                    {generatedAt.time}
                                                </span>
                                            </div>
                                        ) : (
                                            <span className="text-[11px] text-white/30">Date unavailable</span>
                                        )}
                                        <span className="shrink-0 text-xs text-white/35">
                                            {isExpanded ? "Hide versions" : "Versions"}
                                        </span>
                                    </div>
                                </button>
                                <button
                                    type="button"
                                    onClick={(event) => handleDeleteHistory(event, item.id)}
                                    disabled={deletingHistoryId === item.id}
                                    className="absolute right-3 top-[4px] inline-flex h-8 w-8 items-center justify-center text-white/80 opacity-0 transition hover:text-white focus-visible:opacity-100 disabled:cursor-wait disabled:opacity-60 group-hover/card:opacity-100"
                                    aria-label={`Delete history card ${item.id}`}
                                    title="Delete history card"
                                >
                                    <svg
                                        aria-hidden="true"
                                        viewBox="0 0 24 24"
                                        className="h-3.5 w-3.5"
                                        fill="none"
                                        stroke="currentColor"
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth="2"
                                    >
                                        <path d="M3 6h18" />
                                        <path d="M8 6V4h8v2" />
                                        <path d="M19 6l-1 14H6L5 6" />
                                        <path d="M10 11v5" />
                                        <path d="M14 11v5" />
                                    </svg>
                                </button>

                                {isExpanded && (
                                    <div className="border-t border-white/10 px-4 pb-4 pt-3">
                                        {loadingVersions ? (
                                            <p className="text-sm text-white/45">Loading versions...</p>
                                        ) : (
                                            <div className="space-y-2">
                                                {versionList.map((version, index) => {
                                                    const versionIsActive = activePromptId === version.id;
                                                    const versionGeneratedAt = formatGeneratedAt(version.created_at);
                                                    const versionParameterSummary = formatParametersSummary(version);
                                                    return (
                                                        <div
                                                            key={version.id}
                                                            className={`group/version flex w-full items-center gap-3 rounded-xl border p-2 transition ${versionIsActive
                                                                    ? "border-[#ff8a2c]/80 bg-[#ff8a2c]/10"
                                                                    : "border-white/10 bg-[#0f111a] hover:bg-white/[0.05]"
                                                                }`}
                                                        >
                                                            <button
                                                                type="button"
                                                                onClick={() => selectVersion(version.id)}
                                                                disabled={loadingPromptId === version.id || deletingPromptId === version.id}
                                                                className="flex min-w-0 flex-1 cursor-pointer items-center justify-between gap-3 rounded-lg px-1 py-1 text-left transition disabled:cursor-wait disabled:opacity-70"
                                                            >
                                                                <div className="min-w-0">
                                                                    <p className="truncate text-sm font-medium text-white">
                                                                        Version {sortOrder === "newest" ? versionList.length - index : index + 1}
                                                                        {version.parent_prompt_id ? " refinement" : " original"}
                                                                    </p>
                                                                    <p className="mt-1 text-xs text-white/40">
                                                                        Prompt ID: {version.id}
                                                                    </p>
                                                                    {version.prompt && (
                                                                        <p className="mt-1 truncate text-xs text-white/55">
                                                                            Prompt: {version.prompt}
                                                                        </p>
                                                                    )}
                                                                    {version.modification_command && (
                                                                        <p className="mt-1 truncate text-xs text-white/55">
                                                                            Modification: {version.modification_command}
                                                                        </p>
                                                                    )}
                                                                    {versionParameterSummary && (
                                                                        <p className="mt-1 truncate text-[11px] text-white/35">
                                                                            Parameters: {versionParameterSummary}
                                                                        </p>
                                                                    )}
                                                                    {versionGeneratedAt ? (
                                                                        <p className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-white/35">
                                                                            <span>{versionGeneratedAt.date}</span>
                                                                            <span>{versionGeneratedAt.time}</span>
                                                                        </p>
                                                                    ) : (
                                                                        <p className="mt-1 text-[11px] text-white/25">
                                                                            Date unavailable
                                                                        </p>
                                                                    )}
                                                                </div>
                                                                <span className={`shrink-0 text-xs font-medium capitalize ${getStatusClass(version.status)}`}>
                                                                    {loadingPromptId === version.id ? "Loading" : version.status.replaceAll("_", " ")}
                                                                </span>
                                                            </button>
                                                            <button
                                                                type="button"
                                                                onClick={(event) => handleDeleteVersion(event, version.id)}
                                                                disabled={deletingPromptId === version.id}
                                                                className="inline-flex h-8 w-8 shrink-0 items-center justify-center text-white/80 opacity-0 transition hover:text-white focus-visible:opacity-100 disabled:cursor-wait disabled:opacity-60 group-hover/version:opacity-100"
                                                                aria-label={`Delete version ${version.id}`}
                                                                title="Delete version"
                                                            >
                                                                <svg
                                                                    aria-hidden="true"
                                                                    viewBox="0 0 24 24"
                                                                    className="h-3.5 w-3.5"
                                                                    fill="none"
                                                                    stroke="currentColor"
                                                                    strokeLinecap="round"
                                                                    strokeLinejoin="round"
                                                                    strokeWidth="2"
                                                                >
                                                                    <path d="M3 6h18" />
                                                                    <path d="M8 6V4h8v2" />
                                                                    <path d="M19 6l-1 14H6L5 6" />
                                                                    <path d="M10 11v5" />
                                                                    <path d="M14 11v5" />
                                                                </svg>
                                                            </button>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
                )}

                {error && (
                    <div className="mt-4 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
                        {error}
                    </div>
                )}
            </div>

            {user && (
                <div className="shrink-0 border-t border-white/10 bg-[#0f1320]/95 px-5 py-4 shadow-[0_-10px_24px_rgba(0,0,0,0.28)]">
                    <div className="flex items-center justify-between gap-3 text-sm">
                        <span className="pl-8 text-white/45">Generations</span>
                        <span className="font-semibold text-white">
                            {visiblePrompts.length}
                            {visiblePrompts.length !== prompts.length ? ` / ${prompts.length}` : ""}
                        </span>
                    </div>
                </div>
            )}
            {deleteConfirmation}
        </div>
        </>
    );
}
