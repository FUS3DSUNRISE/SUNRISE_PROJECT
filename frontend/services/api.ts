import { useServiceStatusStore } from "@/state/serviceStatusStore";

const DEFAULT_API_BASE_URL = "http://localhost:5000";
const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_BASE_URL?.trim().replace(/\/+$/, "") ||
    DEFAULT_API_BASE_URL;
const PROMPT_PARAMETER_CACHE_KEY = "scailab-prompt-parameters-v1";

function markBackendUnavailable() {
    useServiceStatusStore
        .getState()
        .setUnavailable(
            `Could not reach the backend API at ${API_BASE_URL}. Confirm the backend is running and NEXT_PUBLIC_API_BASE_URL is correct.`
        );
}

function isUnavailableStatus(status: number) {
    return status === 502 || status === 503 || status === 504;
}

async function apiFetch(path: string, init?: RequestInit) {
    try {
        const res = await fetch(`${API_BASE_URL}${path}`, init);

        if (isUnavailableStatus(res.status)) {
            markBackendUnavailable();
        }

        return res;
    } catch (error) {
        markBackendUnavailable();
        throw error;
    }
}

export async function checkBackendConnection() {
    try {
        const res = await fetch(`${API_BASE_URL}/`, {
            method: "GET",
            cache: "no-store",
        });

        if (res.ok) {
            useServiceStatusStore.getState().setAvailable();
            return true;
        }

        markBackendUnavailable();
        return false;
    } catch {
        markBackendUnavailable();
        return false;
    }
}

async function parseJson<T>(res: Response): Promise<T> {
    try {
        return (await res.json()) as T;
    } catch {
        return {} as T;
    }
}

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

type PromptParameterCache = Record<string, FormattedParameters>;

function readPromptParameterCache(): PromptParameterCache {
    if (typeof window === "undefined") return {};

    try {
        const rawCache = window.localStorage.getItem(PROMPT_PARAMETER_CACHE_KEY);
        return rawCache ? JSON.parse(rawCache) as PromptParameterCache : {};
    } catch {
        return {};
    }
}

function writePromptParameterCache(cache: PromptParameterCache) {
    if (typeof window === "undefined") return;

    try {
        window.localStorage.setItem(PROMPT_PARAMETER_CACHE_KEY, JSON.stringify(cache));
    } catch {
        // Best-effort UI synchronization. The backend remains the source of truth.
    }
}

export function cachePromptParameters(promptId: number, parameters: FormattedParameters | null | undefined) {
    if (!parameters) return;

    const cache = readPromptParameterCache();
    cache[String(promptId)] = parameters;
    writePromptParameterCache(cache);
}

export function getCachedPromptParameters(promptId: number) {
    return readPromptParameterCache()[String(promptId)] ?? null;
}

function removeCachedPromptParameters(promptIds: number[]) {
    const cache = readPromptParameterCache();
    promptIds.forEach((promptId) => {
        delete cache[String(promptId)];
    });
    writePromptParameterCache(cache);
}

function withCachedParameters<T extends { id: number; parameters?: FormattedParameters | null }>(prompt: T): T {
    return {
        ...prompt,
        parameters: prompt.parameters ?? getCachedPromptParameters(prompt.id),
    };
}

export type PromptResponse = {
    id: number;
    prompt: string;
    status: string;
    result_path: string | null;
    error_message: string | null;
    parameters?: FormattedParameters | null;
    user_id?: number;
    category?: string;
    username?: string;
    parent_prompt_id?: number | null;
    modification_command?: string | null;
    root_prompt_id?: number;
    created_at?: string | null;
    version_history?: PromptVersionSummary[];
};

export type PromptVersionSummary = {
    id: number;
    parent_prompt_id?: number | null;
    prompt?: string;
    status: string;
    result_path: string | null;
    error_message?: string | null;
    parameters?: FormattedParameters | null;
    modification_command?: string | null;
    created_at?: string | null;
};

export type MyPromptsResponse = {
    user_id: number;
    username: string;
    prompts: PromptVersionSummary[];
};

type AuthUser = {
    id: number;
    username: string;
    email: string;
};

type AuthResponse = {
    message?: string;
    user: AuthUser;
    error?: string;
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
    comments: FeedbackComment[];
};

export type FeedbackComment = {
    id: number;
    prompt_id: number;
    user_id: number;
    rating: FeedbackRating;
    accuracy_score: number | null;
    quality_score: number | null;
    comment: string;
    prompt: string | null;
    modification_command: string | null;
    modified_at: string | null;
    created_at: string | null;
};

export async function createPrompt(payload: GeneratePayload): Promise<PromptResponse> {
    const res = await apiFetch("/prompts", {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
    });

    const data = await parseJson<{ error?: string; message?: string } & PromptResponse>(res);

    if (!res.ok) {
        throw new Error(data.error || data.message || "Failed to create prompt");
    }

    cachePromptParameters(data.id, payload.parameters);

    return {
        id: data.id,
        prompt: data.prompt,
        status: data.status,
        result_path: data.result_path ?? null,
        error_message: data.error_message ?? null,
        parameters: data.parameters ?? payload.parameters,
        user_id: data.user_id,
        category: data.category,
        modification_command: data.modification_command ?? null,
        created_at: data.created_at ?? null,
    };
}

export async function getPrompt(id: number): Promise<PromptResponse> {
    const res = await apiFetch(`/prompts/${id}`, {
        credentials: "include",
    });

    if (!res.ok) {
        throw new Error("Failed to fetch prompt");
    }

    const data = await parseJson<PromptResponse>(res);

    return withCachedParameters({
        id: data.id,
        prompt: data.prompt,
        status: data.status,
        result_path: data.result_path ?? null,
        error_message: data.error_message ?? null,
        parameters: data.parameters ?? null,
        user_id: data.user_id,
        username: data.username,
        parent_prompt_id: data.parent_prompt_id ?? null,
        modification_command: data.modification_command ?? null,
        root_prompt_id: data.root_prompt_id,
        created_at: data.created_at ?? null,
        version_history: (data.version_history ?? []).map(withCachedParameters),
    });
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
    const completed = await pollPrompt(created.id, onProcessing);
    cachePromptParameters(completed.id, payload.parameters);

    return {
        ...completed,
        parameters: completed.parameters ?? payload.parameters,
    };
}

// Modify button integration
export async function modifyModel(
    id: number,
    payload: ModifyPayload,
    onProcessing: () => void = () => { }
): Promise<PromptResponse> {
    const res = await apiFetch(`/prompts/${id}/modify`, {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
    });

    const data = await parseJson<{ error?: string; message?: string; id: number }>(res);

    if (!res.ok) {
        throw new Error(data.error || data.message || "Failed to modify model");
    }

    cachePromptParameters(data.id, payload.parameters);

    // We are waiting for the completion of the new model generation
    const completed = await pollPrompt(data.id, onProcessing);
    cachePromptParameters(completed.id, payload.parameters);

    return {
        ...completed,
        parameters: completed.parameters ?? payload.parameters,
    };
}

export function getDownloadUrl(id: number) {
    return `${API_BASE_URL}/prompts/${id}/download`;
}

export function getPreviewUrl(id: number) {
    return `${API_BASE_URL}/prompts/${id}/file`;
}

export async function getPreviewBlobUrl(id: number): Promise<string> {
    const res = await apiFetch(`/prompts/${id}/file`, {
        credentials: "include",
    });

    if (!res.ok) {
        throw new Error("Failed to fetch preview file");
    }

    const blob = await res.blob();
    return URL.createObjectURL(blob);
}

export async function signupUser(email: string, password: string): Promise<AuthResponse> {
    const res = await apiFetch("/auth/signup", {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
    });

    const data = await parseJson<AuthResponse>(res);

    if (!res.ok) {
        throw new Error(data.error || "Signup failed");
    }

    return data;
}

export async function loginUser(email: string, password: string): Promise<AuthResponse> {
    const res = await apiFetch("/auth/login", {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
    });

    const data = await parseJson<AuthResponse>(res);

    if (!res.ok) {
        throw new Error(data.error || "Login failed");
    }

    return data;
}

export async function getCurrentUser(): Promise<AuthResponse> {
    const res = await apiFetch("/auth/me", {
        credentials: "include",
    });

    const data = await parseJson<AuthResponse>(res);

    if (!res.ok) {
        throw new Error(data.error || "Failed to fetch current user");
    }

    return data;
}

export async function logoutUser() {
    const res = await apiFetch("/auth/logout", {
        method: "POST",
        credentials: "include",
    });

    const data = await parseJson<{ error?: string }>(res);

    if (!res.ok) {
        throw new Error(data.error || "Logout failed");
    }

    return data;
}

export async function getMyPrompts(): Promise<MyPromptsResponse> {
    const res = await apiFetch("/prompts/me", {
        credentials: "include",
    });

    const data = await parseJson<{ error?: string } & MyPromptsResponse>(res);

    if (!res.ok) {
        throw new Error(data.error || "Failed to fetch user prompts");
    }

    return {
        user_id: data.user_id,
        username: data.username,
        prompts: (data.prompts ?? []).map(withCachedParameters),
    };
}

export async function renamePrompt(
    promptId: number,
    prompt: string
): Promise<PromptResponse> {
    const res = await apiFetch(`/prompts/${promptId}`, {
        method: "PATCH",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ prompt }),
    });

    const data = await parseJson<{ error?: string } & PromptResponse>(res);

    if (!res.ok) {
        throw new Error(data.error || "Failed to rename prompt");
    }

    return {
        id: data.id,
        prompt: data.prompt,
        status: data.status,
        result_path: data.result_path ?? null,
        error_message: data.error_message ?? null,
        parameters: data.parameters ?? null,
        user_id: data.user_id,
        username: data.username,
        parent_prompt_id: data.parent_prompt_id ?? null,
        created_at: data.created_at ?? null,
    };
}

export async function deletePrompt(promptId: number): Promise<{ deleted_ids: number[] }> {
    const res = await apiFetch(`/prompts/${promptId}`, {
        method: "DELETE",
        credentials: "include",
    });

    const data = await parseJson<{ error?: string; deleted_ids?: number[] }>(res);

    if (!res.ok) {
        throw new Error(data.error || "Failed to delete prompt");
    }

    removeCachedPromptParameters(data.deleted_ids ?? [promptId]);

    return {
        deleted_ids: data.deleted_ids ?? [promptId],
    };
}

export async function submitFeedback(
    promptId: number,
    payload: FeedbackPayload
): Promise<FeedbackResponse> {
    const res = await apiFetch(`/prompts/${promptId}/feedback`, {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
    });

    const data = await parseJson<{ error?: string }>(res);

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
    const res = await apiFetch("/prompts/feedback/analytics", {
        credentials: "include",
    });

    const data = await parseJson<{ error?: string }>(res);

    if (!res.ok) {
        throw new Error(data.error || "Failed to fetch feedback analytics");
    }

    return data as FeedbackAnalytics;
}
