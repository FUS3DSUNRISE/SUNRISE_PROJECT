"use client";

import { useCallback, useEffect, useMemo, useState, type CSSProperties } from "react";

export type GuidedTourStep = {
    target: string;
    title: string;
    body: string;
};

type GuidedTourProps = {
    steps: GuidedTourStep[];
    isOpen: boolean;
    onClose: () => void;
};

type HighlightRect = {
    top: number;
    left: number;
    width: number;
    height: number;
};

const PADDING = 10;

function clamp(value: number, min: number, max: number) {
    return Math.min(Math.max(value, min), max);
}

export default function GuidedTour({ steps, isOpen, onClose }: GuidedTourProps) {
    const [currentStep, setCurrentStep] = useState(0);
    const [highlightRect, setHighlightRect] = useState<HighlightRect | null>(null);

    const step = steps[currentStep];
    const progressLabel = `${currentStep + 1} of ${steps.length}`;

    const closeTour = useCallback(() => {
        setCurrentStep(0);
        setHighlightRect(null);
        onClose();
    }, [onClose]);

    useEffect(() => {
        if (!isOpen || !step) return;

        let animationFrame = 0;

        const updatePosition = () => {
            const target = document.querySelector<HTMLElement>(step.target);

            if (!target) {
                setHighlightRect(null);
                return;
            }

            target.scrollIntoView({
                block: "center",
                inline: "center",
                behavior: "smooth",
            });

            animationFrame = window.requestAnimationFrame(() => {
                const rect = target.getBoundingClientRect();
                setHighlightRect({
                    top: rect.top - PADDING,
                    left: rect.left - PADDING,
                    width: rect.width + PADDING * 2,
                    height: rect.height + PADDING * 2,
                });
            });
        };

        updatePosition();

        window.addEventListener("resize", updatePosition);
        window.addEventListener("scroll", updatePosition, true);

        return () => {
            window.cancelAnimationFrame(animationFrame);
            window.removeEventListener("resize", updatePosition);
            window.removeEventListener("scroll", updatePosition, true);
        };
    }, [currentStep, isOpen, step]);

    useEffect(() => {
        if (!isOpen) return;

        const handleKeyDown = (event: KeyboardEvent) => {
            if (event.key === "Escape") {
                closeTour();
            }

            if (event.key === "ArrowRight") {
                setCurrentStep((value) => Math.min(value + 1, steps.length - 1));
            }

            if (event.key === "ArrowLeft") {
                setCurrentStep((value) => Math.max(value - 1, 0));
            }
        };

        window.addEventListener("keydown", handleKeyDown);

        return () => window.removeEventListener("keydown", handleKeyDown);
    }, [closeTour, isOpen, steps.length]);

    const tooltipStyle = useMemo<CSSProperties>(() => {
        if (!highlightRect) {
            return {
                left: "50%",
                top: "50%",
                transform: "translate(-50%, -50%)",
            };
        }

        const tooltipWidth = Math.min(360, window.innerWidth - 32);
        const sideSpace = window.innerWidth - highlightRect.left - highlightRect.width;
        const placeRight = sideSpace >= tooltipWidth + 24;
        const placeLeft = highlightRect.left >= tooltipWidth + 24;
        const top = clamp(highlightRect.top, 20, window.innerHeight - 260);

        if (placeRight) {
            return {
                left: highlightRect.left + highlightRect.width + 18,
                top,
                width: tooltipWidth,
            };
        }

        if (placeLeft) {
            return {
                left: highlightRect.left - tooltipWidth - 18,
                top,
                width: tooltipWidth,
            };
        }

        return {
            left: clamp(highlightRect.left, 16, window.innerWidth - tooltipWidth - 16),
            top: clamp(highlightRect.top + highlightRect.height + 16, 16, window.innerHeight - 260),
            width: tooltipWidth,
        };
    }, [highlightRect]);

    if (!isOpen || !step) return null;

    const isFirst = currentStep === 0;
    const isLast = currentStep === steps.length - 1;

    return (
        <div className="fixed inset-0 z-[100]">
            <div className="absolute inset-0 bg-black/25" />

            {highlightRect && (
                <div
                    className="pointer-events-none absolute rounded-[22px] border-2 border-[#ff8a2c] bg-transparent shadow-[0_0_0_9999px_rgba(0,0,0,0.36),0_0_0_6px_rgba(255,138,44,0.16),0_0_42px_rgba(255,138,44,0.5)] transition-all duration-200"
                    style={{
                        top: highlightRect.top,
                        left: highlightRect.left,
                        width: highlightRect.width,
                        height: highlightRect.height,
                    }}
                />
            )}

            <section
                role="dialog"
                aria-modal="true"
                aria-label="Product walkthrough"
                className="absolute rounded-[20px] border border-white/10 bg-[#0f1320] p-5 text-white shadow-2xl"
                style={tooltipStyle}
            >
                <div className="flex items-center justify-between gap-4">
                    <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[#ff8a2c]">
                        Step {progressLabel}
                    </p>
                    <button
                        type="button"
                        onClick={closeTour}
                        className="flex h-9 w-9 items-center justify-center rounded-full border border-white/10 bg-white/[0.04] text-xl leading-none text-white/70 transition hover:bg-white/[0.08] hover:text-white"
                        aria-label="Close walkthrough"
                    >
                        x
                    </button>
                </div>

                <h2 className="mt-4 text-xl font-semibold leading-tight text-white">
                    {step.title}
                </h2>
                <p className="mt-3 text-sm leading-6 text-white/70">{step.body}</p>

                <div className="mt-5 flex items-center gap-2">
                    {steps.map((item, index) => (
                        <button
                            key={item.target}
                            type="button"
                            onClick={() => setCurrentStep(index)}
                            className={`h-2.5 rounded-full transition-all ${
                                index === currentStep
                                    ? "w-8 bg-[#ff8a2c]"
                                    : "w-2.5 bg-white/25 hover:bg-white/45"
                            }`}
                            aria-label={`Go to step ${index + 1}`}
                        />
                    ))}
                </div>

                <div className="mt-6 flex items-center justify-between gap-3">
                    <button
                        type="button"
                        onClick={() => setCurrentStep((value) => Math.max(value - 1, 0))}
                        disabled={isFirst}
                        className="rounded-[14px] border border-white/10 px-4 py-3 text-sm font-medium text-white/75 transition hover:bg-white/[0.06] disabled:cursor-not-allowed disabled:opacity-40"
                    >
                        Back
                    </button>
                    <button
                        type="button"
                        onClick={() => {
                            if (isLast) {
                                closeTour();
                                return;
                            }

                            setCurrentStep((value) => value + 1);
                        }}
                        className="rounded-[14px] bg-[#ff8a2c] px-5 py-3 text-sm font-bold text-black transition hover:bg-[#ff9b4d]"
                    >
                        {isLast ? "Finish" : "Next"}
                    </button>
                </div>
            </section>
        </div>
    );
}
