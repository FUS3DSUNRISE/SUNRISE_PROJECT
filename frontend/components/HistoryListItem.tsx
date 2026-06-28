"use client";

import { useEffect, useRef, useState, type KeyboardEvent, type MouseEvent } from "react";

type Props = {
    title: string;
    timestamp?: string | null;
    status?: string;
    isActive?: boolean;
    isExpanded?: boolean;
    isDeleting?: boolean;
    onOpen?: () => void;
    onRename?: (title: string) => void;
    onDelete?: (event: MouseEvent<HTMLButtonElement>) => void;
};

const paths = {
    edit: ["M12 20h9", "M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"],
    trash: ["M3 6h18", "M8 6V4h8v2", "M19 6l-1 14H6L5 6", "M10 11v5", "M14 11v5"],
};

function Icon({ name }: { name: keyof typeof paths }) {
    return (
        <svg aria-hidden="true" viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2">
            {paths[name].map((d) => <path key={d} d={d} />)}
        </svg>
    );
}

export default function HistoryListItem({
    title,
    timestamp,
    status,
    isActive,
    isExpanded,
    isDeleting,
    onOpen,
    onRename,
    onDelete,
}: Props) {
    const [editing, setEditing] = useState(false);
    const [draft, setDraft] = useState(title);
    const inputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        if (editing) inputRef.current?.select();
    }, [editing]);

    const save = () => {
        const next = draft.trim();
        if (next && next !== title) onRename?.(next);
        setEditing(false);
    };

    const startEdit = (event: MouseEvent<HTMLButtonElement>) => {
        event.stopPropagation();
        setDraft(title);
        setEditing(true);
    };

    const onInputKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
        if (event.key === "Enter") save();
        if (event.key === "Escape") {
            setDraft(title);
            setEditing(false);
        }
    };

    const onRowKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
        if (event.target === event.currentTarget && ["Enter", " "].includes(event.key)) {
            event.preventDefault();
            onOpen?.();
        }
    };

    return (
        <div
            className={`group/history-item relative rounded-lg border bg-white/[0.03] transition ${isActive ? "border-[#ff8a2c]/80" : "border-white/10 hover:bg-white/[0.05]"}`}
            role="button"
            tabIndex={editing ? -1 : 0}
            onClick={() => !editing && onOpen?.()}
            onKeyDown={onRowKeyDown}
        >
            <div className="px-3 py-2.5 pr-11">
                <div className="flex min-w-0 items-center gap-1.5">
                    {editing ? (
                        <input
                            ref={inputRef}
                            value={draft}
                            onClick={(event) => event.stopPropagation()}
                            onChange={(event) => setDraft(event.target.value)}
                            onBlur={save}
                            onKeyDown={onInputKeyDown}
                            className="h-7 min-w-0 flex-1 rounded-md border border-[#ff8a2c]/60 bg-[#090b12] px-2 text-sm font-semibold text-white outline-none focus:border-[#ffb266]"
                            aria-label="Rename history item"
                        />
                    ) : (
                        <>
                            <p className="min-w-0 flex-1 truncate text-sm font-semibold text-white">{title}</p>
                            <button type="button" onClick={startEdit} className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-white/35 opacity-0 transition hover:bg-white/[0.06] hover:text-white focus-visible:opacity-100 group-hover/history-item:opacity-100" aria-label={`Rename ${title}`} title="Rename">
                                <Icon name="edit" />
                            </button>
                        </>
                    )}
                </div>
                <div className="mt-1 flex min-w-0 items-center gap-2 text-xs text-white/40">
                    <span className="min-w-0 truncate">{timestamp || "Date unavailable"}</span>
                    {status && (
                        <>
                            <span className="h-1 w-1 shrink-0 rounded-full bg-white/25" />
                            <span className="shrink-0 capitalize">{status.replaceAll("_", " ")}</span>
                        </>
                    )}
                </div>
                <span className="mt-1 block text-xs text-white/35">{isExpanded ? "Hide versions" : "Versions"}</span>
            </div>

            <button
                type="button"
                onClick={(event) => {
                    event.stopPropagation();
                    onDelete?.(event);
                }}
                disabled={isDeleting}
                className="absolute right-2 top-2 inline-flex h-7 w-7 items-center justify-center rounded-md text-white/35 opacity-0 transition hover:bg-red-500/10 hover:text-red-100 focus-visible:opacity-100 disabled:cursor-wait disabled:opacity-60 group-hover/history-item:opacity-100"
                aria-label={`Delete ${title}`}
                title="Delete"
            >
                <Icon name="trash" />
            </button>
        </div>
    );
}
