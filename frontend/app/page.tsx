"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useGenerationStore } from "@/state/generationStore";
import GenerateButton from "@/components/GenerateButton";
import AuthModal from "@/components/AuthModal";
import PreviewCanvas from "@/components/PreviewCanvas";
import logo from "../public/logo.png";
import { getDownloadUrl, getPreviewBlobUrl } from "@/services/api";
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

    const previewModelPath = previewBlobUrl ?? selectedModel;
    const userInitial = user?.email?.[0]?.toUpperCase() ?? "U";

    const isGenerateDisabled = prompt.length > MAX_PROMPT_LENGTH;

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
                        <a
                            href="https://www.scailab.se/"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="transition hover:text-white"
                        >
                            Contact
                        </a>

                        {!user ? (
                            <>
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
                            </>
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
                <section className="grid grid-cols-1 gap-8 xl:grid-cols-[360px_minmax(0,1fr)_420px]">
                    <aside className="rounded-[24px] border border-white/10 bg-[#0b1020]/50 p-4 shadow-inner">
                        <ParameterPanel value={parameters} onChange={setParameters} />
                    </aside>

                    <section className="min-w-0">
                        <div className="rounded-[24px] border border-white/10 bg-[#0b1020]/50 p-5 shadow-inner">
                            <div className="relative overflow-hidden rounded-[20px] bg-[radial-gradient(circle_at_top,rgba(70,80,255,0.12),transparent_40%),#091028]">
                                <div className="absolute left-1/2 top-6 z-10 -translate-x-1/2 rounded-xl border border-white/10 bg-[#2b2d42]/80 px-5 py-3 text-sm text-white/80">
                                    {status === "submitted"
                                        ? "Submitting..."
                                        : status === "processing"
                                            ? "Generating..."
                                            : "Hover to preview 3D model"}
                                </div>

                                <div className="h-[560px] w-full">
                                    <PreviewCanvas modelPath={previewModelPath} />
                                </div>
                            </div>

                            <div className="mt-5">
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

                    <aside className="rounded-[24px] border border-white/10 bg-[#0b1020]/50 p-5 shadow-inner sm:p-6">
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
                            <div>
                                <label htmlFor="prompt" className="sr-only">
                                    Prompt
                                </label>
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
                                    placeholder="Describe the 3D model..."
                                    maxLength={MAX_PROMPT_LENGTH}
                                    disabled={status === "submitted" || status === "processing"}
                                    className="w-full rounded-[18px] border border-white/10 bg-[#11131f]/80 px-5 py-4 text-white outline-none focus:border-[#ff8a2c]"
                                />

                                {prompt.length > MAX_PROMPT_LENGTH && (
                                    <p className="mt-3 text-sm text-red-400">
                                        Prompt is too long. Maximum length is {MAX_PROMPT_LENGTH} characters.
                                    </p>
                                )}

                                <p className="mt-2 text-xs text-white/35">
                                    {prompt.length}/{MAX_PROMPT_LENGTH}
                                </p>
                            </div>

                            <div className="mt-6">
                                <GenerateButton disabled={isGenerateDisabled} />
                            </div>

                            {(status === "success" && result) || status === "error" ? (
                                <div className="mt-8 border-t border-white/10 pt-8">
                                    {status === "success" && result && (
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

                                            {isRefineMode && (
                                                <div className="rounded-xl border border-[#4f5dff] bg-[#0b1020]/50 p-5">
                                                    <p className="mb-3 text-sm font-semibold uppercase text-[#4f5dff]">
                                                        Iterative refinement
                                                    </p>
                                                    <div className="flex flex-col gap-3 sm:flex-row">
                                                        <input
                                                            type="text"
                                                            value={refinePrompt}
                                                            onChange={(e) => setRefinePrompt(e.target.value)}
                                                            placeholder="e.g., Add more realistic textures..."
                                                            className="min-w-0 flex-1 rounded-lg border border-white/10 bg-[#0f111a] px-4 py-3 text-sm text-white outline-none focus:border-[#4f5dff]"
                                                        />
                                                        <button
                                                            onClick={() => {
                                                                const payload = {
                                                                    action: "refine",
                                                                    prompt: refinePrompt,
                                                                    parameters: getFormattedParameters(),
                                                                    target_model_id: result?.id,
                                                                };
                                                                console.log(
                                                                    "Mock API Payload (Refine):",
                                                                    JSON.stringify(payload, null, 2)
                                                                );
                                                                alert("Refinement prompt saved. Parameters formatted! Check console!");
                                                                setRefinePrompt("");
                                                            }}
                                                            disabled={!refinePrompt.trim()}
                                                            className="shrink-0 rounded-lg bg-[#4f5dff] px-6 py-3 text-sm font-bold text-white transition hover:bg-[#5d69ff] disabled:opacity-50"
                                                        >
                                                            Refine
                                                        </button>
                                                    </div>
                                                </div>
                                            )}

                                            <div className="rounded-xl border border-[#ff8a2c] bg-[#0b1020]/50 p-5">
                                                <p className="mb-3 text-sm font-semibold uppercase text-[#ff8a2c]">
                                                    Modify this model
                                                </p>
                                                <div className="flex flex-col gap-3 sm:flex-row">
                                                    <input
                                                        type="text"
                                                        value={modifyCommand}
                                                        onChange={(e) => setModifyCommand(e.target.value)}
                                                        placeholder="e.g., Make it taller..."
                                                        className="min-w-0 flex-1 rounded-lg border border-white/10 bg-[#0f111a] px-4 py-3 text-sm text-white outline-none focus:border-[#ff8a2c]"
                                                    />
                                                    <button
                                                        onClick={() => {
                                                            const formattedParameters = {
                                                                size: parameters.size,
                                                                geometry: parameters.geometry,
                                                                material: {
                                                                    material_type: parameters.material.type.charAt(0).toUpperCase() + parameters.material.type.slice(1),
                                                                    roughness: parameters.material.roughness,
                                                                    metallic: parameters.material.metallic
                                                                }
                                                            };

                                                            const payload = {
                                                                action: "modify",
                                                                command: modifyCommand,
                                                                parameters: getFormattedParameters(),
                                                                target_model_id: result?.id,
                                                            };

                                                            console.log(
                                                                "Mock API Payload (Modify):",
                                                                JSON.stringify(payload, null, 2)
                                                            );
                                                            alert("Command saved. Parameters formatted! Check console!");
                                                        }}
                                                        disabled={!modifyCommand.trim()}
                                                        className="shrink-0 rounded-lg bg-[#ff8a2c] px-6 py-3 text-sm font-bold text-black transition hover:bg-[#ff9b4d] disabled:opacity-50"
                                                    >
                                                        Modify
                                                    </button>
                                                </div>
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
                                        onClick={() => useGenerationStore.getState().setStatus("error")}
                                        className="text-xs text-red-500/50 hover:text-red-400"
                                    >
                                        [Test Error]
                                    </button>
                                    <button
                                        onClick={() => {
                                            reset();
                                            setPrompt("");
                                            setErrorMessage(null);
                                        }}
                                        className="text-xs text-gray-500 hover:text-white"
                                    >
                                        [Reset]
                                    </button>
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
        </main>
    );
}