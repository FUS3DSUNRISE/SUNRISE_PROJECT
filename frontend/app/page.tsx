"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useGenerationStore } from "@/state/generationStore";
import GenerateButton from "@/components/GenerateButton";
import AuthModal from "@/components/AuthModal";
import PreviewCanvas from "@/components/PreviewCanvas";
import FeedbackWidget, { hasStoredFeedback } from "@/components/FeedbackWidget";
import ImportAssetPanel, { type LocalAsset } from "@/components/ImportAssetPanel";
import GuidedTour, { type GuidedTourStep } from "@/components/GuidedTour";
import logo from "../public/logo.png";
import { getDownloadUrl, getPreviewBlobUrl, modifyModel } from "@/services/api";
import ParameterPanel from "@/components/ParameterPanel";
import { useAuthStore } from "@/state/authStore";

const demoModels = [
    { label: "Tiger", path: "/models/tiger.glb" },
    { label: "Backpack", path: "/models/backpack.glb" },
    { label: "Chair", path: "/models/chair.glb" },
    { label: "Crystal", path: "/models/crystal.glb" },
    { label: "Dinosaur", path: "/models/dinosaur.glb" },
    { label: "Table", path: "/models/table.glb" },
];

const MAX_PROMPT_LENGTH = 120;
const TOUR_STORAGE_KEY = "scailab-guided-tour-seen-v3";

const promptExamples = [
    "Create a simple wooden pallet",
    "Create a classic kitchen table",
    "Create a chair",
];

const guidedTourSteps: GuidedTourStep[] = [
    {
        target: "[data-tour='auth-actions']",
        title: "Log in or create an account",
        body: "Log in or sign up before generating or importing assets so your files, downloads, and feedback stay connected to your account.",
    },
    {
        target: "[data-tour='parameters']",
        title: "Configure the settings before generating",
        body: "Please specify the size, geometry, smoothness, and material values here. These settings will complement your text query to ensure the 3D result matches your idea as closely as possible.",
    },
    {
        target: "[data-tour='preview']",
        title: "Your current 3D model",
        body: "This field displays the active object. Use the cursor to rotate the model and assess the results.",
    },
    {
        target: "[data-tour='feedback']",
        title: "Rate the generated model",
        body: "After reviewing the result, score its quality and accuracy. You can also add an optional comment for analytics.",
    },
    {
        target: "[data-tour='examples']",
        title: "Start with an example",
        body: "Use the ready-made model for practice. It’s quick and easy, and lets you try out all the features without having to create your own object from scratch.",
    },
    {
        target: "[data-tour='import']",
        title: "Upload your own model",
        body: "Authorised users can import files. Once uploaded, you will be able to modify the object using text queries.",
    },
    {
        target: "[data-tour='prompt']",
        title: "Create a text query",
        body: "Just describe the model. If you’re not sure where to start, use the ready-made examples and tips to get your first result in no time.",
    },
    {
        target: "[data-tour='generate']",
        title: "Generate the first version",
        body: "Submit your request to view the result in 3D. As soon as the model is ready, you can download it or make further edits using the new features that will appear below.",
    },
    {
        target: "[data-tour='download']",
        title: "Download the finished file",
        body: "When the asset is ready, use this button to save the generated GLB file locally.",
    },
    
    {
        target: "[data-tour='modify']",
        title: "Iterate with modification prompts",
        body: "After you generate, import, or load a demo, ask for targeted edits like making it taller, smoother, metallic, or more stylized.",
    },
];

type ModifyTarget =
    | {
        kind: "generated";
        id: number;
        name: string;
    }
    | {
        kind: "local";
        name: string;
    };

function getModelFileName(path: string | null | undefined) {
    if (!path) return "Generated model";

    return decodeURIComponent(path.split(/[\\/]/).pop() || "Generated model");
}

export default function Home() {
    const {
        status,
        prompt,
        setPrompt,
        errorMessage,
        result,
        reset,
        parameters,
        setParameters,
        modifyCommand,
        setModifyCommand,
        setErrorMessage,
    } = useGenerationStore();

    const user = useAuthStore((s) => s.user);
    const logout = useAuthStore((s) => s.logout);

    const [authModal, setAuthModal] = useState<null | "login" | "signup">(null);
    const [selectedModel, setSelectedModel] = useState("/models/tiger.glb");
    const [showExamples, setShowExamples] = useState(false);
    const [showUserMenu, setShowUserMenu] = useState(false);
    const [previewBlobUrl, setPreviewBlobUrl] = useState<string | null>(null);
    const [localAsset, setLocalAsset] = useState<(LocalAsset & { previewUrl: string }) | null>(null);
    const [importedAssetName, setImportedAssetName] = useState<string | null>(null);
    const [assetResetSignal, setAssetResetSignal] = useState(0);
    const [isTourOpen, setIsTourOpen] = useState(false);
    const [exampleIndex, setExampleIndex] = useState(0);
    const [showPromptExamples, setShowPromptExamples] = useState(false);
    const [feedbackSubmittedPromptId, setFeedbackSubmittedPromptId] = useState<number | null>(null);

    useEffect(() => {
        const hasSeenTour = window.localStorage.getItem(TOUR_STORAGE_KEY);

        if (!hasSeenTour) {
            const timeoutId = window.setTimeout(() => setIsTourOpen(true), 700);
            return () => window.clearTimeout(timeoutId);
        }
    }, []);

    useEffect(() => {
        const intervalId = window.setInterval(() => {
            setExampleIndex((current) => (current + 1) % promptExamples.length);
        }, 3600);

        return () => window.clearInterval(intervalId);
    }, []);

    const closeTour = () => {
        window.localStorage.setItem(TOUR_STORAGE_KEY, "true");
        setIsTourOpen(false);
    };

    useEffect(() => {
        let objectUrl: string | null = null;
        let isMounted = true;

        async function loadPreview() {
            if (status === "success" && result && result.id !== 999) {
                try {
                    objectUrl = await getPreviewBlobUrl(result.id);
                    if (isMounted) setPreviewBlobUrl(objectUrl);
                } catch (error) {
                    console.error("Preview load failed:", error);
                    if (isMounted) setPreviewBlobUrl(null);
                }
            } else if (status === "success" && result && result.id === 999) {
                if (isMounted) setPreviewBlobUrl(result.result_path);
            } else {
                setPreviewBlobUrl(null);
            }
        }

        loadPreview();

        return () => {
            isMounted = false;
            if (objectUrl && objectUrl.startsWith("blob:")) {
                URL.revokeObjectURL(objectUrl);
            }
        };
    }, [status, result]);

    const activeLocalAsset = user ? localAsset : null;
    const previewModelPath = activeLocalAsset?.previewUrl ?? previewBlobUrl ?? selectedModel;
    const previewModelType = activeLocalAsset?.type;
    const userInitial = user?.email?.[0]?.toUpperCase() ?? "U";
    const generatedModelName =
        result?.id === 999
            ? demoModels.find((model) => model.path === result.result_path)?.label ?? getModelFileName(result.result_path)
            : getModelFileName(result?.result_path);
    const modifyTarget: ModifyTarget | null = activeLocalAsset
        ? importedAssetName
            ? { kind: "local", name: importedAssetName }
            : null
        : status === "success" && result
            ? { kind: "generated", id: result.id, name: generatedModelName }
            : null;
    const canModifyCurrentTarget = Boolean(modifyTarget);
    const canDownloadCurrentResult = status === "success" && Boolean(result?.result_path) && !activeLocalAsset;
    const hasRatedCurrentResult = Boolean(
        result?.id && (feedbackSubmittedPromptId === result.id || hasStoredFeedback(result.id))
    );
    const canRateCurrentResult =
        status === "success" &&
        Boolean(result?.result_path) &&
        !activeLocalAsset &&
        !hasRatedCurrentResult;
    const shouldShowResultPanel =
        status === "error" ||
        Boolean(modifyTarget) ||
        (status === "success" && result && !activeLocalAsset);
    const activeTourSteps = guidedTourSteps.filter((step) => {
        if (step.target === "[data-tour='auth-actions']") {
            return !user;
        }

        if (step.target === "[data-tour='download']") {
            return canDownloadCurrentResult;
        }

        if (step.target === "[data-tour='feedback']") {
            return canRateCurrentResult;
        }

        if (step.target === "[data-tour='modify']") {
            return canModifyCurrentTarget;
        }

        return true;
    });

    const isGenerateDisabled = prompt.length > MAX_PROMPT_LENGTH;
    const isModifyBusy = status === "submitted" || status === "processing";

    const getFormattedParameters = () => ({
        size: parameters.size,
        geometry: parameters.geometry,
        material: {
            material_type:
                parameters.material.type.charAt(0).toUpperCase() +
                parameters.material.type.slice(1),
            roughness: parameters.material.roughness,
            metallic: parameters.material.metallic,
        },
    });

    const handleModify = async () => {
        if (!modifyCommand.trim()) return;

        if (!canModifyCurrentTarget || !modifyTarget) return;

        if (modifyTarget.kind === "local" || modifyTarget.id === 999) {
            console.log("Modify preview model", {
                file: modifyTarget.name,
                command: modifyCommand,
            });
            setModifyCommand("");
            setErrorMessage(null);
            return;
        }

        try {
            const store = useGenerationStore.getState();
            store.setStatus("submitted");
            setErrorMessage(null);

            const payload = {
                command: modifyCommand,
                parameters: getFormattedParameters(),
            };

            const newResult = await modifyModel(modifyTarget.id, payload, () => {
                store.setStatus("processing");
            });

            store.setResult(newResult);
            store.setStatus("success");
            setModifyCommand("");
        } catch (error) {
            console.error("Modification failed:", error);
            useGenerationStore.getState().setStatus("error");
            setErrorMessage(
                error instanceof Error
                    ? error.message
                    : "Modification failed. Please try again."
            );
        }
    };

    const handleLocalAssetSelected = (asset: LocalAsset) => {
        const previewUrl = URL.createObjectURL(asset.file);

        setLocalAsset((currentAsset) => {
            if (currentAsset?.previewUrl) {
                URL.revokeObjectURL(currentAsset.previewUrl);
            }

            return {
                ...asset,
                previewUrl,
            };
        });
        setImportedAssetName(null);
        setModifyCommand("");
    };

    const clearLocalAsset = () => {
        setLocalAsset((currentAsset) => {
            if (currentAsset?.previewUrl) {
                URL.revokeObjectURL(currentAsset.previewUrl);
            }

            return null;
        });
        setImportedAssetName(null);
        setAssetResetSignal((current) => current + 1);
    };

    const handleUseAsset = (asset: LocalAsset) => {
        if (activeLocalAsset) {
            setImportedAssetName(activeLocalAsset.name);
            setErrorMessage(null);
        }

        console.log("Use this asset", {
            name: asset.name,
            type: asset.type,
            size: asset.size,
            lastModified: asset.lastModified,
            previewUrl: activeLocalAsset?.previewUrl ?? null,
            file: asset.file,
        });
    };

    useEffect(() => {
        return () => {
            if (localAsset?.previewUrl) {
                URL.revokeObjectURL(localAsset.previewUrl);
            }
        };
    }, [localAsset?.previewUrl]);

    return (
        <main className="min-h-screen overflow-x-hidden bg-[#050608] text-white">
            <header className="sticky top-0 z-50 border-b border-white/10 bg-[#050608]/80 backdrop-blur-xl">
                <div className="flex w-full items-center justify-between px-8 py-5 xl:px-12">
                    <Image
                        src={logo}
                        alt="ScaiLab"
                        className="h-8 w-auto object-contain"
                        priority
                    />

                    <nav className="relative flex items-center gap-6 text-[15px] text-white/90">
                        <button
                            type="button"
                            onClick={() => setIsTourOpen(true)}
                            className="text-sm font-medium text-white/75 transition hover:text-[#ff8a2c]"
                        >
                            Walkthrough
                        </button>
                        <a
                            href="https://www.scailab.se/"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="transition hover:text-white"
                        >
                            Contact
                        </a>

                        {!user ? (
                            <div data-tour="auth-actions" className="flex items-center gap-6">
                                <button
                                    onClick={() => setAuthModal("login")}
                                    className="transition hover:text-white"
                                >
                                    Login
                                </button>
                                <button
                                    onClick={() => setAuthModal("signup")}
                                    className="rounded-xl border border-[#8a5b22] px-5 py-3 text-[#f2c27c] transition hover:bg-white/5"
                                >
                                    Sign Up Free
                                </button>
                            </div>
                        ) : (
                            <div className="relative">
                                <button
                                    onClick={() => setShowUserMenu((prev) => !prev)}
                                    className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/[0.04] px-4 py-2.5 transition hover:bg-white/[0.07]"
                                >
                                    <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#ff8a2c] font-semibold text-black">
                                        {userInitial}
                                    </div>
                                    <div className="max-w-[180px] text-left">
                                        <p className="truncate text-sm font-medium text-white">
                                            {user.email}
                                        </p>
                                        <p className="text-xs text-white/50">Logged in</p>
                                    </div>
                                </button>

                                {showUserMenu && (
                                    <div className="absolute right-0 top-[calc(100%+12px)] z-40 w-[280px] rounded-2xl border border-white/10 bg-[#0f1320]/95 p-4 shadow-xl backdrop-blur-xl">
                                        <div className="flex items-center gap-3">
                                            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[#ff8a2c] text-lg font-semibold text-black">
                                                {userInitial}
                                            </div>
                                            <div>
                                                <p className="text-sm text-white/50">Signed in as</p>
                                                <p className="max-w-[180px] truncate font-medium text-white">
                                                    {user.email}
                                                </p>
                                            </div>
                                        </div>

                                        <div className="mt-4 border-t border-white/10 pt-4">
                                            <Link
                                                href="/history"
                                                onClick={() => setShowUserMenu(false)}
                                                className="mb-3 block w-full rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm font-medium text-white transition hover:bg-white/[0.07]"
                                            >
                                                View History
                                            </Link>

                                            <button
                                                onClick={() => {
                                                    if (localAsset?.previewUrl) {
                                                        URL.revokeObjectURL(localAsset.previewUrl);
                                                    }
                                                    setLocalAsset(null);
                                                    logout();
                                                    setShowUserMenu(false);
                                                }}
                                                className="w-full rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm font-medium text-red-300 transition hover:bg-red-500/20"
                                            >
                                                Log out
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </nav>
                </div>
            </header>

            <div className="px-8 py-8 xl:px-12">
                <section className="grid grid-cols-1 items-start gap-8 xl:grid-cols-[360px_minmax(0,1fr)_420px]">
                    <aside
                        data-tour="parameters"
                        className="self-start rounded-[24px] border border-white/10 bg-[#0b1020]/50 p-4 shadow-inner"
                    >
                        <ParameterPanel value={parameters} onChange={setParameters} />
                    </aside>

                    <section className="min-w-0">
                        <div className="rounded-[24px] border border-white/10 bg-[#0b1020]/50 p-5 shadow-inner">
                            <div
                                data-tour="preview"
                                className="relative overflow-hidden rounded-[20px] bg-[radial-gradient(circle_at_top,rgba(70,80,255,0.12),transparent_40%),#091028]"
                            >
                                <div className="absolute left-1/2 top-6 z-10 -translate-x-1/2 rounded-xl border border-white/10 bg-[#2b2d42]/80 px-5 py-3 text-sm text-white/80">
                                    {status === "submitted"
                                        ? "Submitting..."
                                        : status === "processing"
                                            ? "Generating..."
                                            : "Hover to preview 3D model"}
                                </div>

                                <div className="h-[560px] w-full">
                                    <PreviewCanvas modelPath={previewModelPath} modelType={previewModelType} />
                                </div>

                                {status === "success" && result?.result_path && !activeLocalAsset && (
                                    <FeedbackWidget
                                        key={result.id}
                                        promptId={result.id}
                                        onSubmitted={() => setFeedbackSubmittedPromptId(result.id)}
                                        disabledReason={
                                            result.id === 999
                                                ? "Demo models are not saved to the database."
                                                : undefined
                                        }
                                    />
                                )}
                            </div>

                            <div data-tour="examples" className="mt-5">
                                <button
                                    onClick={() => setShowExamples((prev) => !prev)}
                                    className="rounded-xl border border-white/10 bg-white/[0.04] px-5 py-3 text-sm font-medium text-white/85 transition hover:border-[#ff8a2c]/60 hover:bg-white/[0.07]"
                                >
                                    Load example
                                </button>

                                {showExamples && (
                                    <div className="absolute z-30 mt-3 w-[320px] rounded-2xl border border-white/10 bg-[#0f1320]/95 p-4 shadow-2xl backdrop-blur-xl">
                                        <div className="mb-3 text-sm font-semibold text-white">
                                            Demo examples
                                        </div>
                                        <div className="grid grid-cols-2 gap-3">
                                            {demoModels.map((model) => (
                                                <button
                                                    key={model.path}
                                                    onClick={() => {
                                                        setSelectedModel(model.path);
                                                        setShowExamples(false);
                                                    }}
                                                    className={`rounded-xl border px-4 py-3 text-sm transition ${selectedModel === model.path
                                                            ? "border-[#ff8a2c] bg-[#ff8a2c] text-black"
                                                            : "border-white/10 bg-white/[0.02] text-white/75 hover:bg-white/[0.05]"
                                                        }`}
                                                >
                                                    {model.label}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </section>

                    <aside className="self-start rounded-[24px] border border-white/10 bg-[#0b1020]/50 p-5 shadow-inner sm:p-6">
                        <div>
                            <p className="mb-3 text-xs font-semibold uppercase tracking-[0.22em] text-[#ff8a2c]">
                                Synthetic assets, real workflow
                            </p>
                            <h1 className="text-4xl font-extrabold leading-[1.02] sm:text-5xl xl:text-5xl">
                                The Easiest Way
                                <br />
                                to Create 3D Models
                            </h1>
                            <p className="mt-5 text-base text-white/70">
                                Type a prompt and generate 3D models instantly.
                            </p>
                        </div>

                        <div className="mt-8 rounded-[26px] border border-white/5 bg-[#0b1020]/70 p-5 shadow-inner sm:p-6">
                            <div data-tour="import">
                                <ImportAssetPanel
                                    key={assetResetSignal}
                                    isLocked={!user}
                                    lockedMessage="Please log in before importing a 3D asset."
                                    onAssetSelected={handleLocalAssetSelected}
                                    onUseAsset={handleUseAsset}
                                />
                            </div>

                            <section
                                data-tour="prompt"
                                className="mt-6 rounded-[18px] border border-white/10 bg-[#11131f]/70 px-5 py-4"
                            >
                                <div className="flex min-h-[44px] items-center justify-between gap-4">
                                    <div className="min-w-0 flex-1">
                                        <label
                                            htmlFor="prompt"
                                            className="text-xs font-semibold uppercase tracking-[0.18em] text-[#ff8a2c]"
                                        >
                                            Prompt
                                        </label>
                                        <h2 className="mt-1 truncate text-lg font-semibold text-white">
                                            Describe a 3D model
                                        </h2>
                                    </div>
                                    <span className="shrink-0 text-xs text-white/35">
                                        {prompt.length}/{MAX_PROMPT_LENGTH}
                                    </span>
                                </div>

                                <input
                                    id="prompt"
                                    type="text"
                                    value={prompt}
                                    onChange={(e) => {
                                        setPrompt(e.target.value);
                                        if (status === "error") {
                                            setErrorMessage(null);
                                        }
                                    }}
                                    placeholder={promptExamples[exampleIndex]}
                                    maxLength={MAX_PROMPT_LENGTH}
                                    disabled={status === "submitted" || status === "processing"}
                                    className="mt-4 w-full rounded-[18px] border border-white/10 bg-[#0f111a] px-5 py-4 text-white outline-none focus:border-[#ff8a2c]"
                                />

                                {prompt.length > MAX_PROMPT_LENGTH && (
                                    <p className="mt-3 text-sm text-red-400">
                                        Prompt is too long. Maximum length is {MAX_PROMPT_LENGTH} characters.
                                    </p>
                                )}

                                <div className="mt-3">
                                    <button
                                        type="button"
                                        onClick={() => setShowPromptExamples((prev) => !prev)}
                                        className="rounded-xl border border-white/10 bg-white/[0.04] px-4 py-2.5 text-xs font-medium text-white/75 transition hover:border-[#ff8a2c]/60 hover:bg-white/[0.07] hover:text-white"
                                    >
                                        {showPromptExamples ? "Hide prompt examples" : "Show prompt examples"}
                                    </button>

                                    {showPromptExamples && (
                                        <div className="mt-3 rounded-2xl border border-white/10 bg-[#0f1320]/95 p-4 shadow-2xl backdrop-blur-xl">
                                            <div className="mb-3 text-sm font-semibold text-white">
                                                Prompt examples
                                            </div>
                                            <div className="space-y-2">
                                                {promptExamples.map((example) => (
                                                    <button
                                                        key={example}
                                                        type="button"
                                                        onClick={() => {
                                                            setPrompt(example);
                                                            setShowPromptExamples(false);
                                                        }}
                                                        disabled={status === "submitted" || status === "processing"}
                                                        className="w-full rounded-xl border border-white/10 bg-white/[0.02] px-4 py-3 text-left text-sm text-white/75 transition hover:bg-white/[0.05] disabled:cursor-not-allowed disabled:opacity-50"
                                                    >
                                                        {example}
                                                    </button>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </section>

                            <div data-tour="generate" className="mt-6">
                                <GenerateButton
                                    disabled={isGenerateDisabled}
                                    onGenerateStart={clearLocalAsset}
                                />
                            </div>

                            {shouldShowResultPanel ? (
                                <div className="mt-8 border-t border-white/10 pt-8">
                                    {status === "success" && result && !activeLocalAsset && (
                                        <div className="space-y-6">
                                            <div className="rounded-[20px] border border-white/10 bg-[#11131f]/70 px-6 py-6 text-center">
                                                {result.result_path ? (
                                                    <>
                                                        <div className="mb-4 flex items-center justify-center gap-2 text-green-400">
                                                            <span className="h-2 w-2 animate-pulse rounded-full bg-green-400" />
                                                            <span className="text-xs font-medium uppercase tracking-[0.16em]">
                                                                Asset status: ready
                                                            </span>
                                                        </div>

                                                        <div className="flex flex-col gap-3 sm:flex-row">
                                                            <a
                                                                data-tour="download"
                                                                href={result.id === 999 ? result.result_path : getDownloadUrl(result.id)}
                                                                download={result.id === 999 ? "demo-model.glb" : undefined}
                                                                className="flex flex-1 items-center justify-center rounded-[14px] border border-white/10 bg-[#171927] px-4 py-4 text-base font-medium text-white transition hover:bg-white/5"
                                                            >
                                                                ↓ Download
                                                            </a>
                                                        </div>
                                                    </>
                                                ) : (
                                                    <div className="rounded-xl border border-yellow-500/30 bg-yellow-500/10 p-4">
                                                        <p className="font-medium text-yellow-500">
                                                            Completed — Asset pending
                                                        </p>
                                                        <p className="text-sm text-white/50">
                                                            Please wait while the file uploads...
                                                        </p>
                                                    </div>
                                                )}

                                                <div className="mt-6 border-t border-white/5 pt-6 text-sm text-white/45">
                                                    <p>
                                                        ID: <span className="text-white/70">{result.id}</span>
                                                    </p>
                                                    <p>
                                                        Status:{" "}
                                                        <span className="capitalize text-green-500">
                                                            {result.status}
                                                        </span>
                                                    </p>
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {modifyTarget && (
                                        <div
                                            data-tour="modify"
                                            className="rounded-xl border border-[#ff8a2c] bg-[#0b1020]/50 p-5"
                                        >
                                            <p className="mb-2 text-sm font-semibold uppercase text-[#ff8a2c]">
                                                Modify target
                                            </p>
                                            <div className="mb-4 rounded-lg border border-white/10 bg-[#0f111a] px-4 py-3">
                                                <p className="text-xs uppercase tracking-[0.14em] text-white/35">
                                                    Current file
                                                </p>
                                                <p className="mt-1 truncate text-sm font-medium text-white">
                                                    {modifyTarget.name}
                                                </p>
                                                <p className="mt-2 text-xs text-white/45">
                                                    {modifyTarget.kind === "local"
                                                        ? "This imported file will be modified."
                                                        : modifyTarget.id === 999
                                                            ? "This preview file will be modified."
                                                            : "This generated file will be modified."}
                                                </p>
                                            </div>
                                            <div className="flex flex-col gap-3 sm:flex-row">
                                                <input
                                                    type="text"
                                                    value={modifyCommand}
                                                    onChange={(e) => setModifyCommand(e.target.value)}
                                                    placeholder="e.g., Make it taller..."
                                                    disabled={isModifyBusy}
                                                    className="min-w-0 flex-1 rounded-lg border border-white/10 bg-[#0f111a] px-4 py-3 text-sm text-white outline-none focus:border-[#ff8a2c]"
                                                />
                                                <button
                                                    onClick={handleModify}
                                                    disabled={!modifyCommand.trim() || isModifyBusy || !canModifyCurrentTarget}
                                                    className="shrink-0 rounded-lg bg-[#ff8a2c] px-6 py-3 text-sm font-bold text-black transition hover:bg-[#ff9b4d] disabled:cursor-not-allowed disabled:opacity-50"
                                                >
                                                    {isModifyBusy ? "Modifying..." : "Modify"}
                                                </button>
                                            </div>
                                        </div>
                                    )}

                                    {status === "error" && (
                                        <div className="rounded-[16px] border border-red-500/30 bg-red-500/10 px-6 py-4 text-center">
                                            <p className="font-semibold text-red-400">Generation Failed</p>
                                            <p className="text-sm text-red-400/80">
                                                {errorMessage || "An unexpected error occurred."}
                                            </p>
                                        </div>
                                    )}
                                </div>
                            ) : null}

                            <div className="mt-8 border-t border-white/10 pt-6">
                                <div className="flex flex-wrap justify-center gap-4 sm:gap-6">
                                    <button
                                        onClick={() => {
                                            clearLocalAsset();
                                            const store = useGenerationStore.getState();
                                            store.setResult({
                                                id: 999,
                                                prompt: store.prompt || "Mock generated model",
                                                status: "completed",
                                                result_path: selectedModel,
                                                error_message: null,
                                            });
                                            store.setStatus("success");
                                        }}
                                        className="text-xs text-green-500/50 hover:text-green-400"
                                    >
                                        [Test Success]
                                    </button>
                                    <button
                                        onClick={() => {
                                            clearLocalAsset();
                                            useGenerationStore.getState().setStatus("error");
                                        }}
                                        className="text-xs text-red-500/50 hover:text-red-400"
                                    >
                                        [Test Error]
                                    </button>
                                    <button
                                        onClick={() => {
                                            clearLocalAsset();
                                            reset();
                                            setPrompt("");
                                            setErrorMessage(null);
                                        }}
                                        className="text-xs text-gray-500 hover:text-white"
                                    >
                                        [Reset]
                                    </button>
                                    <Link
                                        href="/analytics"
                                        className="text-xs text-[#ff8a2c]/70 hover:text-[#ff8a2c]"
                                    >
                                        [Analytics]
                                    </Link>
                                </div>
                            </div>
                        </div>
                    </aside>
                </section>
            </div>

            {authModal && (
                <AuthModal
                    type={authModal}
                    onCloseAction={() => setAuthModal(null)}
                />
            )}

            <GuidedTour
                steps={activeTourSteps}
                isOpen={isTourOpen}
                onClose={closeTour}
            />
        </main>
    );
}
