"use client";

import { useEffect, useMemo, useState } from "react";
import { deletePrompt, getMyPrompts, getPrompt, getUserFriendlyErrorMessage, renamePrompt, type PromptResponse, type PromptVersionSummary } from "@/services/api";
import { useAuthStore } from "@/state/authStore";

type HistorySortOrder = "newest" | "oldest";

type HistoryPanelProps = {
    activePromptId?: number | null;
    className?: string;
    onSelectPrompt?: (prompt: PromptResponse) => void;
};

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
    const [openMenuId, setOpenMenuId] = useState<number | null>(null);
    const [loadingPrompts, setLoadingPrompts] = useState(false);
    const [loadingVersions, setLoadingVersions] = useState(false);
    const [loadingPromptId, setLoadingPromptId] = useState<number | null>(null);
    const [busyActionPromptId, setBusyActionPromptId] = useState<number | null>(null);
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
            setOpenMenuId(null);
            return;
        }

        try {
            setExpandedPromptId(promptId);
            setOpenMenuId(null);
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

    const handleRenamePrompt = async (item: PromptVersionSummary) => {
        const nextName = window.prompt("Rename generation", getPromptTitle(item));
        const trimmedName = nextName?.trim();

        if (!trimmedName || trimmedName === getPromptTitle(item)) {
            setOpenMenuId(null);
            return;
        }

        try {
            setBusyActionPromptId(item.id);
            setError(null);
            const renamedPrompt = await renamePrompt(item.id, trimmedName);

            setPrompts((currentPrompts) =>
                currentPrompts.map((promptItem) =>
                    promptItem.id === item.id
                        ? { ...promptItem, prompt: renamedPrompt.prompt }
                        : promptItem
                )
            );
            setVersions((currentVersions) =>
                currentVersions.map((version) =>
                    version.id === item.id
                        ? { ...version, prompt: renamedPrompt.prompt }
                        : version
                )
            );
            setOpenMenuId(null);
        } catch (renameError) {
            const message = getUserFriendlyErrorMessage(renameError, "Failed to rename prompt");
            setError(message);
        } finally {
            setBusyActionPromptId(null);
        }
    };

    const handleDeletePrompt = async (item: PromptVersionSummary) => {
        const confirmed = window.confirm(`Delete "${getPromptTitle(item)}" and its versions?`);

        if (!confirmed) {
            setOpenMenuId(null);
            return;
        }

        try {
            setBusyActionPromptId(item.id);
            setError(null);
            const result = await deletePrompt(item.id);
            const deletedIds = new Set(result.deleted_ids);

            setPrompts((currentPrompts) =>
                currentPrompts.filter((promptItem) => !deletedIds.has(promptItem.id))
            );
            setVersions((currentVersions) =>
                currentVersions.filter((version) => !deletedIds.has(version.id))
            );

            if (expandedPromptId && deletedIds.has(expandedPromptId)) {
                setExpandedPromptId(null);
            }

            setOpenMenuId(null);
        } catch (deleteError) {
            const message = getUserFriendlyErrorMessage(deleteError, "Failed to delete prompt");
            setError(message);
        } finally {
            setBusyActionPromptId(null);
        }
    };

    return (
        <div className={`mt-6 flex min-h-0 flex-col overflow-hidden rounded-[26px] border border-white/5 bg-[#0b1020]/70 shadow-inner ${className}`}>
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
                                className={`relative rounded-2xl border bg-white/[0.03] transition ${isActive
                                        ? "border-[#ff8a2c]/80"
                                        : "border-white/10 hover:bg-white/[0.05]"
                                    }`}
                            >
                                <button
                                    type="button"
                                    onClick={() => loadVersions(item.id)}
                                    className="block w-full cursor-pointer px-4 py-3 pr-12 text-left"
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
                                    onClick={(event) => {
                                        event.stopPropagation();
                                        setOpenMenuId((currentId) => currentId === item.id ? null : item.id);
                                    }}
                                    className="absolute right-2 top-3 flex h-8 w-8 cursor-pointer items-center justify-center rounded-lg text-white/45 transition hover:bg-white/[0.07] hover:text-white"
                                    aria-label={`Prompt ${item.id} actions`}
                                >
                                    <span className="text-lg leading-none">...</span>
                                </button>

                                {openMenuId === item.id && (
                                    <div className="absolute right-2 top-12 z-30 w-32 rounded-xl border border-white/10 bg-[#0f1320] p-1 shadow-2xl">
                                        <button
                                            type="button"
                                            onClick={() => handleDeletePrompt(item)}
                                            disabled={busyActionPromptId === item.id}
                                            className="block w-full cursor-pointer rounded-lg px-3 py-2 text-left text-sm text-red-300 transition hover:bg-white/[0.07] disabled:cursor-wait disabled:opacity-50"
                                        >
                                            Delete
                                        </button>
                                        <button
                                            type="button"
                                            onClick={() => handleRenamePrompt(item)}
                                            disabled={busyActionPromptId === item.id}
                                            className="block w-full cursor-pointer rounded-lg px-3 py-2 text-left text-sm text-white/80 transition hover:bg-white/[0.07] disabled:cursor-wait disabled:opacity-50"
                                        >
                                            Rename
                                        </button>
                                    </div>
                                )}

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
                                                        <button
                                                            key={version.id}
                                                            type="button"
                                                            onClick={() => selectVersion(version.id)}
                                                            disabled={loadingPromptId === version.id}
                                                            className={`flex w-full cursor-pointer items-center justify-between gap-3 rounded-xl border px-3 py-3 text-left transition disabled:cursor-wait disabled:opacity-70 ${versionIsActive
                                                                    ? "border-[#ff8a2c]/80 bg-[#ff8a2c]/10"
                                                                    : "border-white/10 bg-[#0f111a] hover:bg-white/[0.05]"
                                                                }`}
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
        </div>
    );
}
