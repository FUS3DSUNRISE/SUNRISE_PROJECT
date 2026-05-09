import { useServiceStatusStore } from "@/state/serviceStatusStore";

const DEFAULT_API_BASE_URL = "http://localhost:5000";
const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_BASE_URL?.trim().replace(/\/+$/, "") ||
    DEFAULT_API_BASE_URL;

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

type ImportedAssetModifyPayload = {
    command: string;
};

export type AssetMetadata = {
    original_filename?: string | null;
    extension?: string;
    file_size_bytes?: number;
    interpretable?: boolean;
    objects?: string[];
    structure?: unknown;
    meshes?: string[];
    materials?: string[];
    object_count?: number;
    mesh_count?: number;
    material_count?: number;
    vertex_count?: number;
    face_count?: number;
    error?: string;
    parameters?: unknown;
    properties?: Record<string, unknown>;
    [key: string]: unknown;
};

export type ImportedAssetResponse = {
    id: number;
    filename: string;
    original_filename: string;
    file_type: string;
    file_path: string;
    user_id: number;
    metadata: AssetMetadata;
    message?: string;
};

function getFileExtensionFromName(fileName: string) {
    const cleanName = fileName.split("?")[0] ?? fileName;
    const lastDotIndex = cleanName.lastIndexOf(".");

    return lastDotIndex === -1 ? "" : cleanName.slice(lastDotIndex).toLowerCase();
}

function parseGltfJsonMetadata(data: {
    nodes?: Array<{ name?: string }>;
    meshes?: Array<{ name?: string; primitives?: Array<{ material?: number }> }>;
    materials?: Array<{ name?: string }>;
}) {
    const nodes = data.nodes ?? [];
    const meshes = data.meshes ?? [];
    const materials = data.materials ?? [];

    return {
        objects: nodes.map((node, index) => node.name || `Node_${index}`),
        meshes: meshes.map((mesh, index) => mesh.name || `Mesh_${index}`),
        materials: materials.map((material, index) => material.name || `Material_${index}`),
        object_count: nodes.length,
        mesh_count: meshes.length,
        material_count: materials.length,
    };
}

async function analyzeAssetBlob(blob: Blob, fileName: string): Promise<AssetMetadata> {
    const extension = getFileExtensionFromName(fileName);
    const baseMetadata: AssetMetadata = {
        original_filename: fileName.split(/[\\/]/).pop() || fileName,
        extension,
        file_size_bytes: blob.size,
        interpretable: true,
        objects: [],
        meshes: [],
        materials: [],
        object_count: 0,
        mesh_count: 0,
        material_count: 0,
    };

    try {
        if (extension === ".obj") {
            const text = await blob.text();
            const objects = new Set<string>();
            let vertexCount = 0;
            let faceCount = 0;

            for (const line of text.split(/\r?\n/)) {
                if (line.startsWith("o ") || line.startsWith("g ")) {
                    const objectName = line.trim().split(/\s+(.+)/)[1];
                    if (objectName) objects.add(objectName);
                } else if (line.startsWith("v ")) {
                    vertexCount += 1;
                } else if (line.startsWith("f ")) {
                    faceCount += 1;
                }
            }

            return {
                ...baseMetadata,
                objects: Array.from(objects),
                object_count: objects.size,
                vertex_count: vertexCount,
                face_count: faceCount,
            };
        }

        if (extension === ".gltf") {
            const data = JSON.parse(await blob.text());
            return {
                ...baseMetadata,
                ...parseGltfJsonMetadata(data),
            };
        }

        if (extension === ".glb") {
            const buffer = await blob.arrayBuffer();
            const view = new DataView(buffer);
            const magic = new TextDecoder().decode(new Uint8Array(buffer, 0, 4));

            if (magic !== "glTF") {
                return {
                    ...baseMetadata,
                    interpretable: false,
                    error: "Invalid GLB file",
                };
            }

            const chunkLength = view.getUint32(12, true);
            const chunkType = new TextDecoder().decode(new Uint8Array(buffer, 16, 4));

            if (chunkType !== "JSON") {
                return {
                    ...baseMetadata,
                    interpretable: false,
                    error: "GLB JSON chunk not found",
                };
            }

            const jsonChunk = new TextDecoder()
                .decode(new Uint8Array(buffer, 20, chunkLength))
                .replace(/\0+$/g, "")
                .trim();
            const data = JSON.parse(jsonChunk);

            return {
                ...baseMetadata,
                ...parseGltfJsonMetadata(data),
            };
        }

        return {
            ...baseMetadata,
            interpretable: false,
            error: "Unsupported format for metadata extraction",
        };
    } catch (error) {
        return {
            ...baseMetadata,
            interpretable: false,
            error: error instanceof Error ? error.message : "Metadata extraction failed",
        };
    }
}

export type PromptResponse = {
    id: number;
    prompt: string;
    status: string;
    result_path: string | null;
    error_message: string | null;
    user_id?: number;
    category?: string;
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
    const res = await apiFetch(`/prompts/${id}`, {
        credentials: "include",
    });

    if (!res.ok) {
        throw new Error("Failed to fetch prompt");
    }

    const data = await parseJson<PromptResponse>(res);

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

    // We are waiting for the completion of the new model generation
    return await pollPrompt(data.id, onProcessing);
}

export async function importAsset(file: File): Promise<ImportedAssetResponse> {
    const formData = new FormData();
    formData.append("file", file);

    const res = await apiFetch("/assets/import", {
        method: "POST",
        credentials: "include",
        body: formData,
    });

    const data = await parseJson<{ error?: string } & Partial<ImportedAssetResponse>>(res);

    if (!res.ok || typeof data.id !== "number") {
        const error = new Error(data.error || "Failed to import asset") as Error & {
            status?: number;
        };
        error.status = res.status;
        throw error;
    }

    const metadataRes = await apiFetch(`/assets/${data.id}/metadata`, {
        credentials: "include",
    });
    const metadataData = await parseJson<{
        error?: string;
        id: number;
        original_filename: string;
        file_type: string;
        metadata: AssetMetadata;
    }>(metadataRes);

    if (!metadataRes.ok) {
        const error = new Error(metadataData.error || "Failed to fetch asset metadata") as Error & {
            status?: number;
        };
        error.status = metadataRes.status;
        throw error;
    }

    const metadata = metadataData.metadata ?? {};

    if (metadata.interpretable === false) {
        const error = new Error(
            "Cannot interpret asset. Please check the file format or integrity."
        ) as Error & { status?: number; metadata?: AssetMetadata };
        error.status = 422;
        error.metadata = metadata;
        throw error;
    }

    return {
        id: data.id,
        filename: data.filename ?? "",
        original_filename: data.original_filename ?? metadataData.original_filename,
        file_type: data.file_type ?? metadataData.file_type,
        file_path: data.file_path ?? "",
        user_id: data.user_id ?? 0,
        metadata,
        message: data.message,
    };
}

export async function modifyImportedAsset(
    id: number,
    payload: ImportedAssetModifyPayload,
    onProcessing: () => void = () => { }
): Promise<PromptResponse> {
    const res = await apiFetch(`/assets/${id}/modify`, {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
    });

    const data = await parseJson<{ error?: string; message?: string; id: number }>(res);

    if (!res.ok) {
        throw new Error(data.error || data.message || "Failed to modify imported asset");
    }

    return await pollPrompt(data.id, onProcessing);
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

export async function getPromptFileAssetMetadata(
    id: number,
    fileName: string
): Promise<AssetMetadata> {
    const res = await apiFetch(`/prompts/${id}/file`, {
        credentials: "include",
    });

    const data = await parseJson<{ error?: string }>(res.clone());

    if (!res.ok) {
        throw new Error(data.error || "Failed to fetch generated asset metadata");
    }

    return await analyzeAssetBlob(await res.blob(), fileName);
}

export async function getPublicAssetMetadata(path: string, fileName: string): Promise<AssetMetadata> {
    const res = await fetch(path, {
        cache: "no-store",
    });

    if (!res.ok) {
        throw new Error("Failed to fetch asset metadata");
    }

    return await analyzeAssetBlob(await res.blob(), fileName);
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

export async function getMyPrompts() {
    const res = await apiFetch("/prompts/me", {
        credentials: "include",
    });

    const data = await parseJson<{ error?: string }>(res);

    if (!res.ok) {
        throw new Error(data.error || "Failed to fetch user prompts");
    }

    return data;
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
