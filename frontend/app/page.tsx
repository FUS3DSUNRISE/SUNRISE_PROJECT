"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { useGenerationStore } from "@/state/generationStore";
import GenerateButton from "@/components/GenerateButton";
import AuthModal from "@/components/AuthModal";
import PreviewCanvas from "@/components/PreviewCanvas";
import logo from "../public/logo.png";
import {
    getDownloadUrl,
    getPreviewBlobUrl,
} from "@/services/api";
import ParameterPanel, { ModelParameters } from "@/components/ParameterPanel";
import { useAuthStore } from "@/state/authStore";

const demoModels = [
    { label: "Tiger", path: "/models/tiger.glb" },
    { label: "Backpack", path: "/models/backpack.glb" },
    { label: "Chair", path: "/models/chair.glb" },
    { label: "Crystal", path: "/models/crystal.glb" },
    { label: "Dinosaur", path: "/models/dinosaur.glb" },
    { label: "Table", path: "/models/table.glb" },
];

const defaultParameters: ModelParameters = {
    size: {
        width: 1.5,
        height: 1.5,
        depth: 1.5,
    },
    geometry: {
        complexity: 5,
        smoothness: 50,
    },
    material: {
        type: "plastic",
        roughness: 0.5,
        metallic: 0.2,
    },
};

export default function Home() {
    const status = useGenerationStore((s) => s.status);
    const prompt = useGenerationStore((s) => s.prompt);
    const setPrompt = useGenerationStore((s) => s.setPrompt);
    const errorMessage = useGenerationStore((s) => s.errorMessage);
    const result = useGenerationStore((s) => s.result);

    const user = useAuthStore((s) => s.user);
    const logout = useAuthStore((s) => s.logout);

    const [authModal, setAuthModal] = useState<null | "login" | "signup">(null);
    const [selectedModel, setSelectedModel] = useState("/models/tiger.glb");
    const [showExamples, setShowExamples] = useState(false);
    const [showUserMenu, setShowUserMenu] = useState(false);
    const [parameters, setParameters] = useState<ModelParameters>(defaultParameters);
    const [previewBlobUrl, setPreviewBlobUrl] = useState<string | null>(null);

    useEffect(() => {
        console.log("Parameter JSON:", parameters);
    }, [parameters]);

    useEffect(() => {
        let objectUrl: string | null = null;
        let isMounted = true;

        async function loadPreview() {
            if (status === "success" && result) {
                try {
                    objectUrl = await getPreviewBlobUrl(result.id);
                    if (isMounted) {
                        setPreviewBlobUrl(objectUrl);
                    }
                } catch (error) {
                    console.error("Preview load failed:", error);
                    if (isMounted) {
                        setPreviewBlobUrl(null);
                    }
                }
            } else {
                setPreviewBlobUrl(null);
            }
        }

        loadPreview();

        return () => {
            isMounted = false;
            if (objectUrl) {
                URL.revokeObjectURL(objectUrl);
            }
        };
    }, [status, result]);

    const selectedModelLabel =
        demoModels.find((model) => model.path === selectedModel)?.label ?? "Tiger";
    
    const previewModelPath =
        status === "success" && result?.result_path
            ? getPreviewUrl(result.id)
            : selectedModel;


    const userInitial = user?.email?.[0]?.toUpperCase() ?? "U";

    return (
        <main className="min-h-screen bg-transparent text-white">
            <header className="sticky top-0 z-50 border-b border-white/10 bg-[#050608]/80 backdrop-blur-xl">
                <div className="flex w-full items-center justify-between px-10 py-5 xl:px-16">
                    <div className="flex items-center">
                        <Image
                            src={logo}
                            alt="ScaiLab"
                            className="h-8 w-auto object-contain"
                            priority
                        />
                    </div>

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
                                    <div className="absolute right-0 top-[calc(100%+12px)] z-40 w-[280px] rounded-2xl border border-white/10 bg-[#0f1320]/95 p-4 shadow-[0_20px_60px_rgba(0,0,0,0.45)] backdrop-blur-xl">
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

            <div className="w-full px-8 py-8 xl:px-12">
                <section className="grid w-full grid-cols-1 gap-6 xl:grid-cols-[440px_920px_620px] xl:items-start">
                    <div className="rounded-[26px] border border-white/5 bg-[#0b1020]/70 p-4 shadow-inner">
                        <ParameterPanel value={parameters} onChange={setParameters} />
                    </div>

                    <div className="flex flex-col">
                        <div className="relative mt-10 overflow-hidden rounded-[26px] border border-white/5 bg-[radial-gradient(circle_at_top,rgba(70,80,255,0.12),transparent_40%),#0b1020] p-4 shadow-inner">
                            <div className="absolute left-1/2 top-8 z-10 -translate-x-1/2 rounded-xl border border-white/10 bg-[#2b2d42]/80 px-5 py-3 text-[16px] text-white/80 shadow-lg">
                                {status === "submitted"
                                    ? "Submitting..."
                                    : status === "processing"
                                        ? "Generating..."
                                        : "Hover to preview 3D model"}
                            </div>

                            <div className="h-[620px] w-full">
                                <PreviewCanvas modelPath={previewModelPath} />
                            </div>

                            <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.04)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.04)_1px,transparent_1px)] bg-[size:60px_60px] opacity-25" />
                        </div>

                        <div className="relative mt-5 w-fit">
                            <button
                                onClick={() => setShowExamples((prev) => !prev)}
                                className="rounded-xl border border-white/10 bg-white/[0.04] px-5 py-3 text-sm font-medium text-white/85 transition hover:border-[#ff8a2c]/60 hover:bg-white/[0.07] hover:text-white"
                            >
                                Load example
                            </button>

                            {showExamples && (
                                <div className="absolute left-0 top-[calc(100%+12px)] z-30 w-[320px] rounded-2xl border border-white/10 bg-[#0f1320]/95 p-4 shadow-[0_20px_60px_rgba(0,0,0,0.45)] backdrop-blur-xl">
                                    <div className="mb-3 flex items-center justify-between">
                                        <div>
                                            <p className="text-sm font-semibold text-white">
                                                Demo examples
                                            </p>
                                            <p className="mt-1 text-xs text-white/50">
                                                Current: {selectedModelLabel}
                                            </p>
                                        </div>

                                        <button
                                            onClick={() => setShowExamples(false)}
                                            className="text-sm text-white/45 transition hover:text-white"
                                        >
                                            ✕
                                        </button>
                                    </div>

                                    <div className="grid grid-cols-2 gap-3">
                                        {demoModels.map((model) => {
                                            const isActive = selectedModel === model.path;

                                            return (
                                                <button
                                                    key={model.path}
                                                    onClick={() => {
                                                        setSelectedModel(model.path);
                                                        setShowExamples(false);
                                                    }}
                                                    className={`rounded-xl border px-4 py-3 text-sm font-medium transition ${isActive
                                                            ? "border-[#ff8a2c] bg-[#ff8a2c] text-black shadow-[0_8px_24px_rgba(255,138,44,0.25)]"
                                                            : "border-white/10 bg-white/[0.03] text-white/75 hover:border-white/20 hover:bg-white/[0.06] hover:text-white"
                                                        }`}
                                                >
                                                    {model.label}
                                                </button>
                                            );
                                        })}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="mt-20 rounded-[26px] border border-white/5 bg-[#0b1020]/70 p-6 shadow-inner">
                        <p className="mb-4 text-sm font-semibold uppercase tracking-[0.2em] text-[#ff8a2c]">
                            Synthetic assets, real workflow
                        </p>

                        <h1 className="max-w-[720px] text-5xl font-extrabold leading-[0.95] tracking-tight xl:text-6xl">
                            The Easiest Way
                            <br />
                            to Create 3D Models
                        </h1>

                        <p className="mt-6 max-w-[380px] text-lg text-white/75 sm:text-xl">
                            Type a prompt and generate 3D models instantly.
                        </p>

                        <div className="mt-10">
                            <label htmlFor="prompt" className="sr-only">
                                Text prompt
                            </label>

                            <input
                                id="prompt"
                                type="text"
                                value={prompt}
                                onChange={(e) => setPrompt(e.target.value)}
                                placeholder="Describe the 3D model you'd like to create..."
                                disabled={status === "submitted" || status === "processing"}
                                className="w-full rounded-[20px] border border-white/10 bg-[#11131f]/80 px-5 py-4 text-base text-white placeholder:text-white/35 outline-none transition focus:border-[#ff8a2c] focus:ring-2 focus:ring-[#ff8a2c]/30 disabled:opacity-50"
                            />
                        </div>

                        <div className="mt-8">
                            <GenerateButton />
                        </div>

                        {status === "success" && result && (
                            <div className="mt-12">
                                <div className="w-full rounded-[20px] border border-white/10 bg-[#11131f]/70 px-8 py-7 text-center shadow-[0_10px_25px_rgba(0,0,0,0.25)]">
                                    
                                    {/* Check if a file exists (result_path) */}
                                    {result.result_path ? (
                                        <>
                                            <div className="mb-4 flex items-center justify-center gap-2 text-green-400">
                                                <span className="h-2 w-2 rounded-full bg-green-400 animate-pulse" />
                                                <span className="text-sm font-medium uppercase tracking-wider">Asset status: Ready</span>
                                            </div>
                                            <a
                                                href={getDownloadUrl(result.id)}
                                                className="flex w-full items-center justify-center rounded-[14px] border border-white/10 bg-[#171927] px-6 py-4 text-[22px] font-medium text-white transition hover:bg-white/5 hover:border-[#ff8a2c]/50"
                                            >
                                                ↓ Download Model (glb)
                                            </a>
                                        </>
                                    ) : (
                                        <div className="rounded-xl border border-yellow-500/30 bg-yellow-500/10 p-4">
                                            <p className="text-yellow-500 font-medium">Completed — Asset pending</p>
                                            <p className="text-sm text-white/50 mt-1">The model is ready, but the file is still being uploaded to the server. Please wait a moment.</p>
                                        </div>
                                    )}

                                    <div className="mt-6 flex flex-col gap-2 border-t border-white/5 pt-6">
                                        <p className="text-[14px] text-white/45">
                                            ID: <span className="text-white/70">{result.id}</span>
                                        </p>
                                        <p className="text-[14px] text-white/45">
                                            Status: <span className="text-green-500 capitalize">{result.status}</span>
                                        </p>
                                    </div>
                                </div>
                            </div>
                        )}

                        {status === "error" && (
                            <div className="mt-8">
                                <div className="w-full rounded-[16px] border border-red-500/30 bg-red-500/10 px-6 py-4 text-center">
                                    <p className="text-red-400 font-semibold text-lg mb-1">Generation Failed</p>
                                    <p className="text-red-400/80 text-sm">
                                        {errorMessage || result?.error_message || "An unexpected error occurred. Please check your prompt or try again later."}
                                    </p>
                                    <p className="mt-3 text-xs text-white/30 uppercase tracking-widest">Error Details: {result?.id ? `ID ${result.id}` : "Missing Asset"}</p>
                                </div>
                            </div>
                        )}

                        <div className="mt-10 flex justify-center gap-6 border-t border-white/10 pt-6">
                            <button
                                onClick={() => useGenerationStore.getState().setStatus("success")}
                                className="text-sm text-green-500/70 transition hover:text-green-400"
                            >
                                [Dev Test: Success]
                            </button>

                            <button
                                onClick={() => useGenerationStore.getState().setStatus("error")}
                                className="text-sm text-red-500/70 transition hover:text-red-400"
                            >
                                [Dev Test: Error]
                            </button>

                            <button
                                onClick={() => {
                                reset();
                                setPrompt(""); 
                            }}
                                className="text-sm text-gray-500 transition hover:text-white"
>
                                [Dev Test: Reset to Idle]
                            </button>
                        </div>
                    </div>
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