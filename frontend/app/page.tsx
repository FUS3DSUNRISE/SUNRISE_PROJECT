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
    size: { width: 1.5, height: 1.5, depth: 1.5 },
    geometry: { complexity: 5, smoothness: 50 },
    material: { type: "plastic", roughness: 0.5, metallic: 0.2 },
};

export default function Home() {
    // 1. Added 'reset' here
    const { status, prompt, setPrompt, errorMessage, result, reset } = useGenerationStore();

    const user = useAuthStore((s) => s.user);
    const logout = useAuthStore((s) => s.logout);

    const [authModal, setAuthModal] = useState<null | "login" | "signup">(null);
    const [selectedModel, setSelectedModel] = useState("/models/tiger.glb");
    const [showExamples, setShowExamples] = useState(false);
    const [showUserMenu, setShowUserMenu] = useState(false);
    const [parameters, setParameters] = useState<ModelParameters>(defaultParameters);
    const [previewBlobUrl, setPreviewBlobUrl] = useState<string | null>(null);
    const [modifyCommand, setModifyCommand] = useState("");

    useEffect(() => {
        let objectUrl: string | null = null;
        let isMounted = true;

        async function loadPreview() {
            if (status === "success" && result) {
                try {
                    objectUrl = await getPreviewBlobUrl(result.id);
                    if (isMounted) setPreviewBlobUrl(objectUrl);
                } catch (error) {
                    console.error("Preview load failed:", error);
                    if (isMounted) setPreviewBlobUrl(null);
                }
            } else {
                setPreviewBlobUrl(null);
            }
        }

        loadPreview();

        return () => {
            isMounted = false;
            if (objectUrl) URL.revokeObjectURL(objectUrl);
        };
    }, [status, result]);

    const selectedModelLabel = demoModels.find((m) => m.path === selectedModel)?.label ?? "Tiger";
    
    // 2. Fixed duplicate declaration
    const previewModelPath = previewBlobUrl ?? selectedModel;
    const userInitial = user?.email?.[0]?.toUpperCase() ?? "U";

    return (
        <main className="min-h-screen bg-transparent text-white">
            <header className="sticky top-0 z-50 border-b border-white/10 bg-[#050608]/80 backdrop-blur-xl">
                <div className="flex w-full items-center justify-between px-10 py-5 xl:px-16">
                    <Image src={logo} alt="ScaiLab" className="h-8 w-auto object-contain" priority />

                    <nav className="relative flex items-center gap-6 text-[15px] text-white/90">
                        <a href="https://www.scailab.se/" target="_blank" rel="noopener noreferrer" className="transition hover:text-white">
                            Contact
                        </a>

                        {!user ? (
                            <>
                                <button onClick={() => setAuthModal("login")} className="transition hover:text-white">Login</button>
                                <button onClick={() => setAuthModal("signup")} className="rounded-xl border border-[#8a5b22] px-5 py-3 text-[#f2c27c] transition hover:bg-white/5">
                                    Sign Up Free
                                </button>
                            </>
                        ) : (
                            <div className="relative">
                                <button onClick={() => setShowUserMenu((prev) => !prev)} className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/[0.04] px-4 py-2.5 transition hover:bg-white/[0.07]">
                                    <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#ff8a2c] font-semibold text-black">{userInitial}</div>
                                    <div className="max-w-[180px] text-left">
                                        <p className="truncate text-sm font-medium text-white">{user.email}</p>
                                        <p className="text-xs text-white/50">Logged in</p>
                                    </div>
                                </button>
                                {showUserMenu && (
                                    <div className="absolute right-0 top-[calc(100%+12px)] z-40 w-[280px] rounded-2xl border border-white/10 bg-[#0f1320]/95 p-4 shadow-xl backdrop-blur-xl">
                                        <div className="flex items-center gap-3">
                                            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[#ff8a2c] text-lg font-semibold text-black">{userInitial}</div>
                                            <div>
                                                <p className="text-sm text-white/50">Signed in as</p>
                                                <p className="max-w-[180px] truncate font-medium text-white">{user.email}</p>
                                            </div>
                                        </div>
                                        <div className="mt-4 border-t border-white/10 pt-4">
                                            <button onClick={() => { logout(); setShowUserMenu(false); }} className="w-full rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm font-medium text-red-300 transition hover:bg-red-500/20">
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
                <section className="grid w-full grid-cols-1 gap-6 xl:grid-cols-[440px_1fr_420px] xl:items-start">
                    {/* Parameters */}
                    <div className="rounded-[26px] border border-white/5 bg-[#0b1020]/70 p-4 shadow-inner">
                        <ParameterPanel value={parameters} onChange={setParameters} />
                    </div>

                    {/* Preview Area */}
                    <div className="flex flex-col">
                        <div className="relative mt-10 overflow-hidden rounded-[26px] border border-white/5 bg-[#0b1020] p-4 shadow-inner">
                            <div className="absolute left-1/2 top-8 z-10 -translate-x-1/2 rounded-xl border border-white/10 bg-[#2b2d42]/80 px-5 py-3 text-[16px] text-white/80">
                                {status === "submitted" ? "Submitting..." : status === "processing" ? "Generating..." : "Hover to preview 3D model"}
                            </div>
                            <div className="h-[620px] w-full">
                                <PreviewCanvas modelPath={previewModelPath} />
                            </div>
                        </div>

                        <div className="relative mt-5">
                            <button onClick={() => setShowExamples((prev) => !prev)} className="rounded-xl border border-white/10 bg-white/[0.04] px-5 py-3 text-sm text-white/85 transition hover:border-[#ff8a2c]/60">
                                Load example
                            </button>
                            {showExamples && (
                                <div className="absolute left-0 top-[calc(100%+12px)] z-30 w-[320px] rounded-2xl border border-white/10 bg-[#0f1320]/95 p-4 shadow-2xl backdrop-blur-xl">
                                    <div className="grid grid-cols-2 gap-3">
                                        {demoModels.map((model) => (
                                            <button key={model.path} onClick={() => { setSelectedModel(model.path); setShowExamples(false); }} className={`rounded-xl border px-4 py-3 text-sm transition ${selectedModel === model.path ? "border-[#ff8a2c] bg-[#ff8a2c] text-black" : "border-white/10 text-white/75"}`}>
                                                {model.label}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Generation UI */}
                    <div className="mt-20 rounded-[26px] border border-white/5 bg-[#0b1020]/70 p-6 shadow-inner">
                        <p className="mb-4 text-sm font-semibold uppercase tracking-[0.2em] text-[#ff8a2c]">Synthetic assets, real workflow</p>
                        <h1 className="text-5xl font-extrabold leading-tight">The Easiest Way to Create 3D Models</h1>
                        
                        <div className="mt-10">
                            <input
                                type="text"
                                value={prompt}
                                onChange={(e) => setPrompt(e.target.value)}
                                placeholder="Describe the 3D model..."
                                disabled={status === "submitted" || status === "processing"}
                                className="w-full rounded-[20px] border border-white/10 bg-[#11131f]/80 px-5 py-4 text-white outline-none focus:border-[#ff8a2c]"
                            />
                        </div>

                        <div className="mt-8"><GenerateButton /></div>

                        {/* 3. Combined Result Logic */}
                        {status === "success" && result && (
                            <div className="mt-10 space-y-6">
                                <div className="w-full rounded-[20px] border border-white/10 bg-[#11131f]/70 px-8 py-7 text-center">
                                    {result.result_path ? (
                                        <>
                                            <div className="mb-4 flex items-center justify-center gap-2 text-green-400">
                                                <span className="h-2 w-2 rounded-full bg-green-400 animate-pulse" />
                                                <span className="text-sm font-medium uppercase tracking-wider">Asset status: Ready</span>
                                            </div>
                                            <a href={getDownloadUrl(result.id)} className="flex w-full items-center justify-center rounded-[14px] border border-white/10 bg-[#171927] px-6 py-4 text-[22px] font-medium text-white transition hover:bg-white/5">
                                                ↓ Download Model (glb)
                                            </a>
                                        </>
                                    ) : (
                                        <div className="rounded-xl border border-yellow-500/30 bg-yellow-500/10 p-4">
                                            <p className="text-yellow-500 font-medium">Completed — Asset pending</p>
                                            <p className="text-sm text-white/50">Please wait while the file uploads...</p>
                                        </div>
                                    )}

                                    <div className="mt-6 border-t border-white/5 pt-6 text-sm text-white/45">
                                        <p>ID: <span className="text-white/70">{result.id}</span></p>
                                        <p>Status: <span className="text-green-500 capitalize">{result.status}</span></p>
                                    </div>

                                    {/* Modify Section Integrated */}
                                    <div className="mt-8 rounded-xl border border-[#ff8a2c]/30 bg-[#ff8a2c]/5 p-5 text-left">
                                        <p className="mb-3 text-sm font-semibold uppercase text-[#ff8a2c]">Modify this model</p>
                                        <div className="flex gap-3">
                                            <input
                                                type="text"
                                                value={modifyCommand}
                                                onChange={(e) => setModifyCommand(e.target.value)}
                                                placeholder="e.g., Make it taller..."
                                                className="flex-1 rounded-lg border border-white/10 bg-[#0f111a] px-4 py-3 text-sm text-white"
                                            />
                                            <button
                                                onClick={() => alert(`Saved: "${modifyCommand}"`)}
                                                disabled={!modifyCommand.trim()}
                                                className="rounded-lg bg-[#ff8a2c] px-6 py-3 text-sm font-bold text-black disabled:opacity-50"
                                            >
                                                Modify
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {status === "error" && (
                            <div className="mt-8 rounded-[16px] border border-red-500/30 bg-red-500/10 px-6 py-4 text-center">
                                <p className="text-red-400 font-semibold">Generation Failed</p>
                                <p className="text-red-400/80 text-sm">{errorMessage || "An unexpected error occurred."}</p>
                            </div>
                        )}

                        {/* Dev Tools */}
                        <div className="mt-10 flex justify-center gap-6 border-t border-white/10 pt-6">
                            <button onClick={() => useGenerationStore.getState().setStatus("success")} className="text-xs text-green-500/50 hover:text-green-400">[Test Success]</button>
                            <button onClick={() => useGenerationStore.getState().setStatus("error")} className="text-xs text-red-500/50 hover:text-red-400">[Test Error]</button>
                            <button onClick={() => { reset(); setPrompt(""); }} className="text-xs text-gray-500 hover:text-white">[Reset]</button>
                        </div>
                    </div>
                </section>
            </div>

            {authModal && (
                <AuthModal type={authModal} onCloseAction={() => setAuthModal(null)} />
            )}
        </main>
    );
}