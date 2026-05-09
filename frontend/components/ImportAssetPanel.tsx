"use client";

import type { DragEvent } from "react";
import { useState } from "react";
import { importAsset, type ImportedAssetResponse } from "@/services/api";

const SUPPORTED_EXTENSIONS = [".glb", ".gltf", ".obj"] as const;
const ACCEPTED_FILE_TYPES = SUPPORTED_EXTENSIONS.join(",");

type UploadStatus = "idle" | "uploading" | "ready" | "error";

export type LocalAsset = {
    name: string;
    type: string;
    size: number;
    lastModified: number;
    file: File;
};

function getFileExtension(fileName: string) {
    const lastDotIndex = fileName.lastIndexOf(".");
    return lastDotIndex === -1 ? "" : fileName.slice(lastDotIndex).toLowerCase();
}

function getAssetType(fileName: string) {
    const extension = getFileExtension(fileName);
    return extension ? extension.replace(".", "").toUpperCase() : "Unknown";
}

function validateAssetFile(file: File) {
    const extension = getFileExtension(file.name);

    if (SUPPORTED_EXTENSIONS.includes(extension as (typeof SUPPORTED_EXTENSIONS)[number])) {
        return null;
    }

    const readableFormats = SUPPORTED_EXTENSIONS.map((item) => item.toUpperCase()).join(", ");
    return `"${file.name}" is not supported. Please choose a 3D asset in ${readableFormats} format.`;
}

type ImportAssetPanelProps = {
    isLocked?: boolean;
    lockedMessage?: string;
    onAssetSelected?: (asset: LocalAsset) => void;
    onAssetImported?: (asset: LocalAsset, importedAsset: ImportedAssetResponse) => void;
    onInterpretationError?: (message: string, metadata?: ImportedAssetResponse["metadata"]) => void;
    onUseAsset?: (asset: LocalAsset) => void;
};

export default function ImportAssetPanel({
    isLocked = false,
    lockedMessage = "Log in to import assets.",
    onAssetSelected,
    onAssetImported,
    onInterpretationError,
    onUseAsset,
}: ImportAssetPanelProps) {
    const [isExpanded, setIsExpanded] = useState(false);
    const [isDragging, setIsDragging] = useState(false);
    const [selectedAsset, setSelectedAsset] = useState<LocalAsset | null>(null);
    const [uploadStatus, setUploadStatus] = useState<UploadStatus>("idle");
    const [validationMessage, setValidationMessage] = useState<string | null>(null);

    const handleFile = async (file: File | undefined) => {
        if (isLocked) {
            setValidationMessage(lockedMessage);
            return;
        }

        if (!file) return;

        const error = validateAssetFile(file);

        if (error) {
            setSelectedAsset(null);
            setUploadStatus("idle");
            setValidationMessage(error);
            return;
        }

        const nextAsset = {
            name: file.name,
            type: getAssetType(file.name),
            size: file.size,
            lastModified: file.lastModified,
            file,
        };

        setSelectedAsset(nextAsset);
        setUploadStatus("uploading");
        setValidationMessage(null);
        onAssetSelected?.(nextAsset);

        try {
            const importedAsset = await importAsset(file);
            setUploadStatus("ready");
            onAssetImported?.(nextAsset, importedAsset);
        } catch (error) {
            const metadata =
                error instanceof Error && "metadata" in error
                    ? (error as Error & { metadata?: ImportedAssetResponse["metadata"] }).metadata
                    : undefined;
            const message =
                error instanceof Error
                    ? error.message
                    : "Cannot interpret asset. Please check the file format or integrity.";

            setUploadStatus("error");
            setValidationMessage(message);
            onInterpretationError?.(message, metadata);
        }
    };

    const handleDrop = (event: DragEvent<HTMLLabelElement>) => {
        event.preventDefault();
        setIsDragging(false);

        if (isLocked) {
            setValidationMessage(lockedMessage);
            return;
        }

        handleFile(event.dataTransfer.files[0]);
    };

    const statusLabel =
        isLocked
            ? "Login required"
            : uploadStatus === "uploading"
            ? "Uploading..."
            : uploadStatus === "ready"
                ? "Ready to import"
                : uploadStatus === "error"
                    ? "Import failed"
                : "No file selected";

    return (
        <section className="rounded-[18px] border border-white/10 bg-[#11131f]/70">
            <button
                type="button"
                onClick={() => setIsExpanded((current) => !current)}
                className="flex min-h-[70px] w-full items-center justify-between gap-4 px-5 py-3 text-left"
                aria-expanded={isExpanded}
            >
                <div className="min-w-0 flex-1">
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#ff8a2c]">
                        Import asset
                    </p>
                    <h2 className="mt-1 truncate text-lg font-semibold text-white">Add a 3D file</h2>
                </div>

                <span className="flex shrink-0 items-center gap-3">
                    <span
                        className={`rounded-full px-3 py-1 text-xs font-medium ${
                            uploadStatus === "ready"
                                ? "bg-green-500/15 text-green-300"
                                : uploadStatus === "uploading"
                                    ? "bg-yellow-500/15 text-yellow-300"
                                    : uploadStatus === "error"
                                        ? "bg-red-500/15 text-red-300"
                                        : "bg-white/10 text-white/60"
                        }`}
                    >
                        {statusLabel}
                    </span>
                    <span className="flex h-8 w-8 items-center justify-center rounded-full border border-white/10 bg-white/[0.03] text-lg leading-none text-white/70">
                        {isExpanded ? "-" : "+"}
                    </span>
                </span>
            </button>

            {isExpanded && (
                <div className="px-5 pb-5">
                    <label
                        onDragEnter={(event) => {
                            event.preventDefault();
                            if (isLocked) return;
                            setIsDragging(true);
                        }}
                        onDragOver={(event) => {
                            event.preventDefault();
                            if (isLocked) return;
                            setIsDragging(true);
                        }}
                        onDragLeave={(event) => {
                            event.preventDefault();
                            setIsDragging(false);
                        }}
                        onDrop={handleDrop}
                        className={`flex min-h-[148px] flex-col items-center justify-center rounded-[18px] border border-dashed px-5 py-6 text-center transition ${
                            isLocked
                                ? "cursor-not-allowed border-white/10 bg-white/[0.02] opacity-70"
                                : isDragging
                                ? "border-[#ff8a2c] bg-[#ff8a2c]/10"
                                : "border-white/15 bg-white/[0.03] hover:border-[#ff8a2c]/70 hover:bg-white/[0.05]"
                        }`}
                    >
                        <input
                            type="file"
                            accept={ACCEPTED_FILE_TYPES}
                            disabled={isLocked}
                            className="sr-only"
                            onChange={(event) => {
                                handleFile(event.target.files?.[0]);
                                event.target.value = "";
                            }}
                        />

                        <span className="flex h-11 w-11 items-center justify-center rounded-full border border-white/10 bg-[#171927] text-lg text-[#ff8a2c]">
                            +
                        </span>
                        <span className="mt-4 text-sm font-medium text-white">
                            {isLocked ? "Log in to import a model" : "Drop a model here or browse files"}
                        </span>
                        <span className="mt-2 text-xs text-white/45">
                            Supported formats: GLB, GLTF, OBJ
                        </span>
                    </label>

                    {validationMessage && (
                        <p
                            role="alert"
                            className="mt-3 rounded-xl border border-red-500/25 bg-red-500/10 px-4 py-3 text-sm leading-6 text-red-200"
                        >
                            {validationMessage}
                        </p>
                    )}

                    {selectedAsset && (
                        <div className="mt-4 rounded-[16px] border border-white/10 bg-[#0f111a] p-4">
                            <div className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-[minmax(0,1fr)_90px]">
                                <div className="min-w-0">
                                    <p className="text-xs uppercase tracking-[0.14em] text-white/35">
                                        File name
                                    </p>
                                    <p className="mt-1 truncate font-medium text-white">
                                        {selectedAsset.name}
                                    </p>
                                </div>
                                <div>
                                    <p className="text-xs uppercase tracking-[0.14em] text-white/35">
                                        Type
                                    </p>
                                    <p className="mt-1 font-medium text-white">
                                        {selectedAsset.type}
                                    </p>
                                </div>
                            </div>

                            <div className="mt-4 border-t border-white/10 pt-4">
                                <div className="flex items-center gap-2 text-sm text-white/70" aria-live="polite">
                                    <span
                                        className={`h-2.5 w-2.5 rounded-full ${
                                            uploadStatus === "ready"
                                                ? "bg-green-400"
                                                : uploadStatus === "error"
                                                    ? "bg-red-400"
                                                    : "animate-pulse bg-yellow-400"
                                        }`}
                                    />
                                    Upload status: {statusLabel}
                                </div>
                            </div>

                            {uploadStatus === "ready" && (
                                <button
                                    type="button"
                                    onClick={() => onUseAsset?.(selectedAsset)}
                                    disabled={isLocked}
                                    className="mt-4 w-full rounded-[14px] bg-[#ff8a2c] px-4 py-3 text-sm font-semibold text-black transition hover:bg-[#ff9b4d] disabled:cursor-not-allowed disabled:opacity-50"
                                >
                                    Use this asset
                                </button>
                            )}
                        </div>
                    )}
                </div>
            )}
        </section>
    );
}
