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

type BackendErrorPayload = {
    error?: string;
    message?: string;
    detail?: string;
    error_message?: string | null;
    code?: string;
    error_code?: string;
    status?: string;
};

export type BackendErrorCode =
    | "AUTH_REQUIRED"
    | "AUTH_INVALID"
    | "EMAIL_IN_USE"
    | "FORBIDDEN"
    | "NOT_FOUND"
    | "VALIDATION_FAILED"
    | "PROMPT_BLOCKED"
    | "CLARIFICATION_REQUIRED"
    | "LLM_OUTPUT_INVALID"
    | "ASSET_UNINTERPRETABLE"
    | "ASSET_UNSUPPORTED"
    | "DUPLICATE_FEEDBACK"
    | "BACKEND_UNAVAILABLE"
    | "UNKNOWN";

export class BackendError extends Error {
    status: number;
    code: BackendErrorCode;
    rawMessage: string;

    constructor({
        status,
        code,
        message,
        rawMessage,
    }: {
        status: number;
        code: BackendErrorCode;
        message: string;
        rawMessage: string;
    }) {
        super(message);
        this.name = "BackendError";
        this.status = status;
        this.code = code;
        this.rawMessage = rawMessage;
    }
}

const BACKEND_ERROR_MESSAGES: Record<BackendErrorCode, string> = {
    AUTH_REQUIRED: "Please log in before continuing.",
    AUTH_INVALID: "The email or password is incorrect.",
    EMAIL_IN_USE: "An account already exists for that email.",
    FORBIDDEN: "You do not have permission to use this item.",
    NOT_FOUND: "We could not find that item. It may have been deleted or moved.",
    VALIDATION_FAILED: "Some submitted parameters are invalid. Please check the settings and try again.",
    PROMPT_BLOCKED: "This prompt cannot be generated. Please revise the request and try again.",
    CLARIFICATION_REQUIRED: "The prompt needs more detail before it can be generated.",
    LLM_OUTPUT_INVALID: "The AI returned output that could not be converted into a 3D model. Try a simpler or more specific prompt.",
    ASSET_UNINTERPRETABLE: "The asset could not be interpreted. Try another file or simplify the model.",
    ASSET_UNSUPPORTED: "That file type is not supported. Please use a GLB, GLTF, or OBJ file.",
    DUPLICATE_FEEDBACK: "Feedback has already been submitted for this result.",
    BACKEND_UNAVAILABLE: "The backend is unavailable right now. Check that the API is running and try again.",
    UNKNOWN: "Something went wrong. Please try again.",
};

function getPayloadMessage(payload: BackendErrorPayload) {
    return payload.error || payload.message || payload.detail || payload.error_message || "";
}

function normalizeErrorCode(value: string | undefined): BackendErrorCode | null {
    if (!value) return null;

    const normalized = value.trim().toUpperCase().replace(/[^A-Z0-9]+/g, "_");
    const supportedCodes = new Set<BackendErrorCode>(Object.keys(BACKEND_ERROR_MESSAGES) as BackendErrorCode[]);

    return supportedCodes.has(normalized as BackendErrorCode)
        ? normalized as BackendErrorCode
        : null;
}

function inferBackendErrorCode(status: number, payload: BackendErrorPayload, rawMessage: string): BackendErrorCode {
    const explicitCode = normalizeErrorCode(payload.error_code || payload.code);
    if (explicitCode) return explicitCode;

    const lowerMessage = rawMessage.toLowerCase();

    if (lowerMessage.includes("invalid credentials")) return "AUTH_INVALID";
    if (lowerMessage.includes("email already in use")) return "EMAIL_IN_USE";
    if (lowerMessage.includes("already submitted")) return "DUPLICATE_FEEDBACK";
    if (isUnavailableStatus(status)) return "BACKEND_UNAVAILABLE";
    if (status === 401 || lowerMessage.includes("not authenticated")) return "AUTH_REQUIRED";
    if (status === 403 || lowerMessage.includes("unauthorized")) return "FORBIDDEN";
    if (status === 404 || lowerMessage.includes("not found")) return "NOT_FOUND";
    if (lowerMessage.includes("unsupported file format")) return "ASSET_UNSUPPORTED";
    if (
        lowerMessage.includes("validation") ||
        lowerMessage.includes("field required") ||
        lowerMessage.includes("value is not") ||
        lowerMessage.includes("missing command") ||
        lowerMessage.includes("missing prompt") ||
        lowerMessage.includes("missing json")
    ) {
        return "VALIDATION_FAILED";
    }
    if (payload.status === "clarify") return "CLARIFICATION_REQUIRED";
    if (payload.status === "error" && status === 400) return "PROMPT_BLOCKED";
    if (
        lowerMessage.includes("generated code") ||
        lowerMessage.includes("llm") ||
        lowerMessage.includes("malformed")
    ) {
        return "LLM_OUTPUT_INVALID";
    }
    if (
        lowerMessage.includes("blender") ||
        lowerMessage.includes("could not interpret") ||
        lowerMessage.includes("uninterpretable") ||
        lowerMessage.includes("asset")
    ) {
        return "ASSET_UNINTERPRETABLE";
    }

    return "UNKNOWN";
}

function createBackendError(res: Response, payload: BackendErrorPayload, fallback: string) {
    const rawMessage = getPayloadMessage(payload) || fallback;
    const code = inferBackendErrorCode(res.status, payload, rawMessage);

    return new BackendError({
        status: res.status,
        code,
        message: BACKEND_ERROR_MESSAGES[code] || rawMessage || fallback,
        rawMessage,
    });
}

function createPromptStatusError(prompt: PromptResponse) {
    const rawMessage = prompt.error_message || "Generation failed";
    const code = inferBackendErrorCode(500, { error_message: rawMessage }, rawMessage);

    return new BackendError({
        status: 500,
        code,
        message: BACKEND_ERROR_MESSAGES[code] || rawMessage,
        rawMessage,
    });
}

export function getUserFriendlyErrorMessage(error: unknown, fallback = "Something went wrong. Please try again.") {
    if (error instanceof BackendError) return error.message;
    if (error instanceof Error) return error.message || fallback;
    return fallback;
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

    const data = await parseJson<BackendErrorPayload & PromptResponse>(res);

    if (!res.ok) {
        throw createBackendError(res, data, "Failed to create prompt");
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

    const data = await parseJson<BackendErrorPayload & PromptResponse>(res);

    if (!res.ok) {
        throw createBackendError(res, data, "Failed to fetch prompt");
    }

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
            throw createPromptStatusError(data);
        }

        await new Promise((resolve) => setTimeout(resolve, 2000));
    }

    throw new BackendError({
        status: 500,
        code: "UNKNOWN",
        message: "The generation ended in an unexpected state. Please try again.",
        rawMessage: "Unexpected prompt status.",
    });
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

    const data = await parseJson<BackendErrorPayload & { id: number }>(res);

    if (!res.ok) {
        throw createBackendError(res, data, "Failed to modify model");
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
        const data = await parseJson<BackendErrorPayload>(res);
        throw createBackendError(res, data, "Failed to fetch preview file");
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
        throw createBackendError(res, data, "Signup failed");
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
        throw createBackendError(res, data, "Login failed");
    }

    return data;
}

export async function getCurrentUser(): Promise<AuthResponse> {
    const res = await apiFetch("/auth/me", {
        credentials: "include",
    });

    const data = await parseJson<AuthResponse>(res);

    if (!res.ok) {
        throw createBackendError(res, data, "Failed to fetch current user");
    }

    return data;
}

export async function logoutUser() {
    const res = await apiFetch("/auth/logout", {
        method: "POST",
        credentials: "include",
    });

    const data = await parseJson<BackendErrorPayload>(res);

    if (!res.ok) {
        throw createBackendError(res, data, "Logout failed");
    }

    return data;
}

export async function getMyPrompts(): Promise<MyPromptsResponse> {
    const res = await apiFetch("/prompts/me", {
        credentials: "include",
    });

    const data = await parseJson<BackendErrorPayload & MyPromptsResponse>(res);

    if (!res.ok) {
        throw createBackendError(res, data, "Failed to fetch user prompts");
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

    const data = await parseJson<BackendErrorPayload & PromptResponse>(res);

    if (!res.ok) {
        throw createBackendError(res, data, "Failed to rename prompt");
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

    const data = await parseJson<BackendErrorPayload & { deleted_ids?: number[] }>(res);

    if (!res.ok) {
        throw createBackendError(res, data, "Failed to delete prompt");
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

    const data = await parseJson<BackendErrorPayload>(res);

    if (!res.ok) {
        throw createBackendError(res, data, "Failed to submit feedback");
    }

    return data as FeedbackResponse;
}

export async function getFeedbackAnalytics(): Promise<FeedbackAnalytics> {
    const res = await apiFetch("/prompts/feedback/analytics", {
        credentials: "include",
    });

    const data = await parseJson<BackendErrorPayload>(res);

    if (!res.ok) {
        throw createBackendError(res, data, "Failed to fetch feedback analytics");
    }

    return data as FeedbackAnalytics;
}
