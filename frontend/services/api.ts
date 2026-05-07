const BASE_URL = "http://localhost:5000";

export type FormattedParameters = {
    size: {
        width: number;
        height: number;
        depth: number;
    };
    geometry: {
        complexity: number;
        smoothness: number;
    };
    material: {
        material_type: string;
        roughness: number;
        metallic: number;
    };
};

type GeneratePayload = {
    prompt: string;
    parameters: FormattedParameters;
};

type ModifyPayload = {
    command: string;
    parameters: FormattedParameters;
};

type PromptResponse = {
    id: number;
    prompt: string;
    status: string;
    result_path: string | null;
    error_message: string | null;
    user_id?: number;
    category?: string;
};

export type FeedbackRating = "positive" | "neutral" | "negative";

type FeedbackPayload = {
    rating: FeedbackRating;
    model_score?: number;
    accuracy_score?: number;
    quality_score?: number;
    comment?: string;
};

type FeedbackResponse = {
    id: number;
    prompt_id: number;
    user_id: number;
    rating: FeedbackRating;
    accuracy_score: number | null;
    quality_score: number | null;
    comment: string | null;
};

export type FeedbackAnalytics = {
    total_feedback: number;
    success_rate: number;
    average_accuracy_score: number | null;
    average_quality_score: number | null;
    ratings: Partial<Record<FeedbackRating, number>>;
};

export async function createPrompt(payload: GeneratePayload): Promise<PromptResponse> {
    const res = await fetch(`${BASE_URL}/prompts`, {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
    });

    const data = await res.json();

    if (!res.ok) {
        throw new Error(data.error || data.message || "Failed to create prompt");
    }

    return {
        id: data.id,
        prompt: data.prompt,
        status: data.status,
        result_path: data.result_path ?? null,
        error_message: data.error_message ?? null,
        user_id: data.user_id,
        category: data.category,
    };
}

export async function getPrompt(id: number): Promise<PromptResponse> {
    const res = await fetch(`${BASE_URL}/prompts/${id}`, {
        credentials: "include",
    });

    if (!res.ok) {
        throw new Error("Failed to fetch prompt");
    }

    const data = await res.json();

    return {
        id: data.id,
        prompt: data.prompt,
        status: data.status,
        result_path: data.result_path ?? null,
        error_message: data.error_message ?? null,
        user_id: data.user_id,
    };
}

export async function pollPrompt(
    id: number,
    onProcessing: () => void
): Promise<PromptResponse> {
    let status = "queued";

    while (status === "queued" || status === "processing") {
        const data = await getPrompt(id);
        status = data.status;

        if (status === "processing") {
            onProcessing();
        }

        if (status === "completed") {
            if (!data.result_path) {
                console.warn("Generation completed but result_path is missing");
            }
            return data;
        }

        if (status === "failed") {
            throw new Error(data.error_message || "Generation failed");
        }

        await new Promise((resolve) => setTimeout(resolve, 2000));
    }

    throw new Error("Unexpected prompt status.");
}

export async function generateModel(
    payload: GeneratePayload,
    onProcessing: () => void = () => { }
): Promise<PromptResponse> {
    const created = await createPrompt(payload);
    return await pollPrompt(created.id, onProcessing);
}

// Modify button integration
export async function modifyModel(
    id: number,
    payload: ModifyPayload,
    onProcessing: () => void = () => { }
): Promise<PromptResponse> {
    const res = await fetch(`${BASE_URL}/prompts/${id}/modify`, {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
    });

    const data = await res.json();

    if (!res.ok) {
        throw new Error(data.error || data.message || "Failed to modify model");
    }

    // We are waiting for the completion of the new model generation
    return await pollPrompt(data.id, onProcessing);
}

export function getDownloadUrl(id: number) {
    return `${BASE_URL}/prompts/${id}/download`;
}

export function getPreviewUrl(id: number) {
    return `${BASE_URL}/prompts/${id}/file`;
}

export async function getPreviewBlobUrl(id: number): Promise<string> {
    const res = await fetch(`${BASE_URL}/prompts/${id}/file`, {
        credentials: "include",
    });

    if (!res.ok) {
        throw new Error("Failed to fetch preview file");
    }

    const blob = await res.blob();
    return URL.createObjectURL(blob);
}

export async function signupUser(email: string, password: string) {
    const res = await fetch(`${BASE_URL}/auth/signup`, {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
    });

    const data = (await res.json()) as { error?: string };

    if (!res.ok) {
        throw new Error(data.error || "Signup failed");
    }

    return data;
}

export async function loginUser(email: string, password: string) {
    const res = await fetch(`${BASE_URL}/auth/login`, {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
    });

    const data = (await res.json()) as { error?: string };

    if (!res.ok) {
        throw new Error(data.error || "Login failed");
    }

    return data;
}

export async function getCurrentUser() {
    const res = await fetch(`${BASE_URL}/auth/me`, {
        credentials: "include",
    });

    const data = (await res.json()) as { error?: string };

    if (!res.ok) {
        throw new Error(data.error || "Failed to fetch current user");
    }

    return data;
}

export async function logoutUser() {
    const res = await fetch(`${BASE_URL}/auth/logout`, {
        method: "POST",
        credentials: "include",
    });

    const data = (await res.json()) as { error?: string };

    if (!res.ok) {
        throw new Error(data.error || "Logout failed");
    }

    return data;
}

export async function getMyPrompts() {
    const res = await fetch(`${BASE_URL}/prompts/me`, {
        credentials: "include",
    });

    const data = (await res.json()) as { error?: string };

    if (!res.ok) {
        throw new Error(data.error || "Failed to fetch user prompts");
    }

    return data;
}

export async function submitFeedback(
    promptId: number,
    payload: FeedbackPayload
): Promise<FeedbackResponse> {
    const res = await fetch(`${BASE_URL}/prompts/${promptId}/feedback`, {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
    });

    const data = (await res.json()) as { error?: string };

    if (!res.ok) {
        const error = new Error(data.error || "Failed to submit feedback") as Error & {
            status?: number;
        };
        error.status = res.status;
        throw error;
    }

    return data as FeedbackResponse;
}

export async function getFeedbackAnalytics(): Promise<FeedbackAnalytics> {
    const res = await fetch(`${BASE_URL}/prompts/feedback/analytics`, {
        credentials: "include",
    });

    const data = (await res.json()) as { error?: string };

    if (!res.ok) {
        throw new Error(data.error || "Failed to fetch feedback analytics");
    }

    return data as FeedbackAnalytics;
}
