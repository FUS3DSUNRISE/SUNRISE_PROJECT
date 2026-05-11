"use client";

import { useEffect, useMemo, useState } from "react";
import { BackendError, getUserFriendlyErrorMessage, submitFeedback, type FeedbackRating } from "@/services/api";
import styles from "./FeedbackWidget.module.css";

type FeedbackWidgetProps = {
    promptId: number;
    disabledReason?: string;
    onSubmitted?: () => void;
};

type SubmitState = "idle" | "submitting" | "submitted" | "error";
type ThankYouState = "hidden" | "visible" | "leaving";

const storageKeyFor = (promptId: number) => `sunrise-feedback-submitted-${promptId}`;
const ratingOptions = Array.from({ length: 5 }, (_, index) => index + 1);

export const hasStoredFeedback = (promptId: number) =>
    typeof window !== "undefined" && Boolean(localStorage.getItem(storageKeyFor(promptId)));

const ratingFromScore = (score: number): FeedbackRating => {
    if (score >= 4) return "positive";
    if (score <= 2) return "negative";
    return "neutral";
};

export default function FeedbackWidget({ promptId, disabledReason, onSubmitted }: FeedbackWidgetProps) {
    const [qualityScore, setQualityScore] = useState<number | null>(null);
    const [accuracyScore, setAccuracyScore] = useState<number | null>(null);
    const [isCommentOpen, setIsCommentOpen] = useState(false);
    const [comment, setComment] = useState("");
    const [submitState, setSubmitState] = useState<SubmitState>(() =>
        hasStoredFeedback(promptId) ? "submitted" : "idle"
    );
    const [thankYouState, setThankYouState] = useState<ThankYouState>("hidden");
    const [message, setMessage] = useState<string | null>(null);

    const isSubmitted = submitState === "submitted";
    const isShowingThanks = isSubmitted && thankYouState !== "hidden";
    const isDemo = Boolean(disabledReason);
    const isBlocked = submitState === "submitting" || isSubmitted || isDemo;

    const selectedLabel = useMemo(() => {
        if (!qualityScore) return "Choose a score";
        if (qualityScore >= 4) return "Excellent";
        if (qualityScore >= 3) return "Helpful";
        return "Needs work";
    }, [qualityScore]);

    useEffect(() => {
        if (thankYouState !== "visible") return;

        const fadeTimeout = window.setTimeout(() => setThankYouState("leaving"), 2600);
        const hideTimeout = window.setTimeout(() => setThankYouState("hidden"), 3200);

        return () => {
            window.clearTimeout(fadeTimeout);
            window.clearTimeout(hideTimeout);
        };
    }, [thankYouState]);

    if (isSubmitted && !isShowingThanks) {
        return null;
    }

    const handleSubmit = async () => {
        if (!qualityScore || !accuracyScore || isBlocked) return;

        setSubmitState("submitting");
        setMessage(null);

        try {
            await submitFeedback(promptId, {
                rating: ratingFromScore(qualityScore),
                quality_score: qualityScore,
                accuracy_score: accuracyScore,
                comment: comment.trim() || undefined,
            });

            localStorage.setItem(storageKeyFor(promptId), "true");
            setSubmitState("submitted");
            setMessage("Feedback submitted.");
            setThankYouState("visible");
            onSubmitted?.();
        } catch (error) {
            const duplicate = error instanceof BackendError && error.status === 409;
            if (duplicate) {
                localStorage.setItem(storageKeyFor(promptId), "true");
                setSubmitState("submitted");
                setMessage(getUserFriendlyErrorMessage(error, "Feedback already submitted for this result."));
                setThankYouState("visible");
                onSubmitted?.();
                return;
            }

            const message = getUserFriendlyErrorMessage(error, "Could not submit feedback.");
            setSubmitState("error");
            setMessage(message);
        }
    };

    const feedbackClassName = [
        styles.feedback,
        isShowingThanks ? styles.submitted : "",
        thankYouState === "leaving" ? styles.fadingOut : "",
    ].filter(Boolean).join(" ");

    return (
        <section
            data-tour="feedback"
            className={feedbackClassName}
            aria-label="Rate this generated model"
            aria-live={isShowingThanks ? "polite" : undefined}
        >
            {isShowingThanks ? (
                <div className={styles.submittedSummary}>
                    <span className={styles.successIcon} aria-hidden="true" />
                    <div className={styles.heading}>
                        <p className={styles.eyebrow}>Feedback received</p>
                        <p className={styles.title}>Thank you for helping us improve this model.</p>
                        <p className={styles.statusText}>{message || "Your rating has been saved."}</p>
                    </div>
                </div>
            ) : (
                <>
                    <div className={styles.header}>
                        <div className={styles.heading}>
                            <p className={styles.eyebrow}>Rate this model</p>
                            <p className={styles.title}>How would you rate the quality and accuracy of this 3D model?</p>
                            <p className={styles.statusText}>{disabledReason || selectedLabel}</p>
                        </div>
                    </div>

                    <div className={styles.ratingGroup}>
                        <div className={styles.metricHeader}>
                            <p className={styles.metricLabel}>Quality</p>
                            <p className={styles.metricDescription}>Visual quality and detail</p>
                        </div>
                        <div className={styles.ratingControl}>
                            <div className={styles.ratingScale} role="radiogroup" aria-label="Quality rating from 1 to 5">
                                {ratingOptions.map((score) => (
                                    <button
                                        key={score}
                                        type="button"
                                        className={`${styles.scoreButton} ${qualityScore === score ? styles.scoreActive : ""}`}
                                        onClick={() => setQualityScore(score)}
                                        disabled={isBlocked}
                                        role="radio"
                                        aria-checked={qualityScore === score}
                                    >
                                        {score}
                                    </button>
                                ))}
                            </div>

                            <div className={styles.scaleLabels} aria-hidden="true">
                                <span>Poor</span>
                                <span>Excellent</span>
                            </div>
                        </div>
                    </div>

                    <div className={styles.ratingGroup}>
                        <div className={styles.metricHeader}>
                            <p className={styles.metricLabel}>Accuracy</p>
                            <p className={styles.metricDescription}>How well it matches the prompt</p>
                        </div>
                        <div className={styles.ratingControl}>
                            <div className={styles.ratingScale} role="radiogroup" aria-label="Accuracy rating from 1 to 5">
                                {ratingOptions.map((score) => (
                                    <button
                                        key={score}
                                        type="button"
                                        className={`${styles.scoreButton} ${accuracyScore === score ? styles.scoreActive : ""}`}
                                        onClick={() => setAccuracyScore(score)}
                                        disabled={isBlocked}
                                        role="radio"
                                        aria-checked={accuracyScore === score}
                                    >
                                        {score}
                                    </button>
                                ))}
                            </div>

                            <div className={styles.scaleLabels} aria-hidden="true">
                                <span>Poor</span>
                                <span>Excellent</span>
                            </div>
                        </div>
                    </div>

                    {qualityScore && accuracyScore && (
                        <div className={styles.commentPanel}>
                            <div className={styles.panelContent}>
                                <button
                                    type="button"
                                    className={styles.feedbackToggle}
                                    onClick={() => setIsCommentOpen((current) => !current)}
                                    disabled={isBlocked}
                                    aria-expanded={isCommentOpen}
                                    aria-controls={`feedback-comment-${promptId}`}
                                >
                                    <span className={styles.feedbackIcon} aria-hidden="true" />
                                    <span>Add feedback (optional)</span>
                                </button>

                                {isCommentOpen && (
                                    <>
                                        <label className={styles.commentLabel} htmlFor={`feedback-comment-${promptId}`}>
                                            Your feedback helps us improve
                                        </label>
                                        <textarea
                                            id={`feedback-comment-${promptId}`}
                                            value={comment}
                                            onChange={(event) => setComment(event.target.value)}
                                            placeholder="Add an optional comment..."
                                            rows={2}
                                            maxLength={500}
                                            disabled={isBlocked}
                                            className={styles.comment}
                                        />
                                    </>
                                )}
                                <p className={`${styles.message} ${submitState === "error" ? styles.error : ""}`}>
                                    {message || disabledReason || "Rate this model to help others and improve our AI."}
                                </p>
                            </div>
                            <button
                                type="button"
                                onClick={handleSubmit}
                                disabled={isBlocked}
                                className={styles.submitButton}
                            >
                                <span className={styles.submitCheck} aria-hidden="true" />
                                {submitState === "submitting" ? "Submitting..." : "Submit Ratings"}
                            </button>
                        </div>
                    )}
                </>
            )}
        </section>
    );
}
