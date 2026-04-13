"use client";

import { useState } from "react";
import Image from "next/image";
import { useGenerationStore } from "@/state/generationStore";
import GenerateButton from "@/components/GenerateButton";
import AuthModal from "@/components/AuthModal";
import PreviewCanvas from "@/components/PreviewCanvas";
import logo from "../public/logo.png";

const demoModels = [
    { label: "Tiger", path: "/models/tiger.glb" },
    { label: "Backpack", path: "/models/backpack.glb" },
    { label: "Chair", path: "/models/chair.glb" },
    { label: "Crystal", path: "/models/crystal.glb" },
    { label: "Dinosaur", path: "/models/dinosaur.glb" },
    { label: "Table", path: "/models/table.glb" },
];

export default function Home() {
    const status = useGenerationStore((s) => s.status);
    const prompt = useGenerationStore((s) => s.prompt);
    const setPrompt = useGenerationStore((s) => s.setPrompt);
    const errorMessage = useGenerationStore((s) => s.errorMessage);
    const resultPath = useGenerationStore((s) => s.resultPath); // ADDED: extract path
    const reset = useGenerationStore((s) => s.reset);

    const [authModal, setAuthModal] = useState<null | "login" | "signup">(null);
    const [selectedModel, setSelectedModel] = useState("/models/tiger.glb");
    const [showExamples, setShowExamples] = useState(false);

    const selectedModelLabel =
        demoModels.find((model) => model.path === selectedModel)?.label ?? "Tiger";

    // ADDED: Determine what to show in the 3D window.
    // If the generation is successful and there is a path, we show the generated one. Otherwise, we show the demo model.
    const currentModelToDisplay = status === "success" && resultPath ? resultPath : selectedModel;

    return (
        <main className="min-h-screen bg-transparent text-white">
            <div className="mx-auto max-w-[1440px] px-6 py-6">
                <header className="sticky top-0 z-50 flex items-center justify-between border-b border-white/10 bg-[#050608]/80 px-8 py-5 backdrop-blur-xl">
                    <div className="flex items-center">
                        <Image
                            src={logo}
                            alt="ScaiLab"
                            className="h-8 w-auto object-contain"
                            priority
                        />
                    </div>

                    <nav className="flex items-center gap-6 text-[15px] text-white/90">
                        <a
                            href="https://www.scailab.se/"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="transition hover:text-white"
                        >
                            Contact
                        </a>

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
                    </nav>
                </header>

                <section className="grid min-h-[calc(100vh-120px)] grid-cols-1 items-center gap-10 px-8 py-10 xl:grid-cols-[1.15fr_0.85fr] xl:gap-12">
                    <div className="flex flex-col">
                        <div className="relative min-h-[420px] overflow-hidden rounded-[26px] border border-white/5 bg-[radial-gradient(circle_at_top,rgba(70,80,255,0.12),transparent_40%),#0b1020] p-4 shadow-inner lg:min-h-[520px]">
                            <div className="absolute left-1/2 top-12 z-10 -translate-x-1/2 rounded-xl border border-white/10 bg-[#2b2d42]/80 px-5 py-3 text-[16px] text-white/80 shadow-lg">
                                {status === "submitted"
                                    ? "Submitting..."
                                    : status === "processing"
                                        ? "Generating..."
                                        : "Hover to preview 3D model"}
                            </div>

                            {/* UPDATED: Passing a dynamic variable instead of selectedModel */}
                            <div className="h-[380px] w-full lg:h-[460px]">
                                <PreviewCanvas modelPath={currentModelToDisplay} />
                            </div>

                            <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.04)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.04)_1px,transparent_1px)] bg-[size:60px_60px] opacity-25" />
                        </div>

                        <div className="relative mt-6 w-fit">
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

                    <div className="flex max-w-[640px] flex-col justify-center">
                        <p className="mb-4 text-sm font-semibold uppercase tracking-[0.2em] text-[#ff8a2c]">
                            Synthetic assets, real workflow
                        </p>

                        <h1 className="max-w-[620px] text-4xl font-extrabold leading-[0.95] tracking-tight sm:text-5xl xl:text-6xl">
                            The Easiest Way to Create 3D Models
                        </h1>

                        <p className="mt-5 max-w-[560px] text-lg text-white/75 sm:text-xl">
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

                        {/* UPDATED: Successful download block */}
                        {status === "success" && resultPath && (
                            <div className="mt-12">
                                <div className="w-full rounded-[20px] border border-white/10 bg-[#11131f]/70 px-8 py-7 text-center shadow-[0_10px_25px_rgba(0,0,0,0.25)]">
                                    <a
                                        href={resultPath}
                                        download="generated_model.glb"
                                        className="flex w-full items-center justify-center rounded-[14px] border border-white/10 bg-[#171927] px-6 py-4 text-[22px] font-medium text-white transition hover:bg-white/5"
                                    >
                                        ↓ Download Model (glb)
                                    </a>

                                    <p className="mt-6 text-[20px] text-white/75">
                                        Formats: GLB / FBX / OBJ
                                    </p>
                                    <p className="mt-3 text-[20px] text-white/75">
                                        Estimated Time: 3-5 min
                                    </p>
                                </div>
                            </div>
                        )}

                        {/* UPDATED: Error block */}
                        {status === "error" && (
                            <div className="mt-8">
                                <div className="w-full rounded-[16px] border border-red-500/30 bg-red-500/10 px-6 py-4 text-center text-red-400">
                                    {errorMessage ??
                                        "Oops! Something went wrong while generating the model. Please check your prompt and try again."}
                                </div>
                            </div>
                        )}

                        <div className="mt-10 flex justify-center gap-6 border-t border-white/10 pt-6">
                            <button
                                onClick={() => {
                                    // Simulate the backend: pass the path to the current demo model
                                    useGenerationStore.getState().setResultPath(selectedModel); 
                                    useGenerationStore.getState().setStatus("success");
                                }}
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
                                onClick={() => reset()}
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