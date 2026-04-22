const BASE_URL = "http://localhost:5000";

export async function createPrompt(prompt: string, category: string, parameters: any) {
    const res = await fetch(`${BASE_URL}/prompts`, {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ prompt: prompt, category: category, parameters: parameters }),
    });

    const data = await res.json();

    if (!res.ok) {
        throw new Error(data.error || data.message || "Failed to create prompt");
    }

    return data;
}

export async function getPrompt(id: number) {
    const res = await fetch(`${BASE_URL}/prompts/${id}`, {
        credentials: "include",
    });

    if (!res.ok) {
        throw new Error("Failed to fetch prompt");
    }

    return res.json();
}

export async function pollPrompt(
    id: number,
    onProcessing: () => void
): Promise<any> {
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
}

export async function generateModel(
    prompt: string,
    category: string,
    parameters: any, 
    onProcessing: () => void = () => { }
) {
    const created = await createPrompt(prompt, category, parameters);
    return await pollPrompt(created.id, onProcessing);
}

export function getDownloadUrl(id: number) {
    return `${BASE_URL}/prompts/${id}/download`;
}

export function getPreviewUrl(id: number) {
    return `${BASE_URL}/prompts/${id}/file`;
}

export async function getPreviewBlobUrl(id: number) {
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

    const data = await res.json();

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

    const data = await res.json();

    if (!res.ok) {
        throw new Error(data.error || "Login failed");
    }

    return data;
}

export async function getCurrentUser() {
    const res = await fetch(`${BASE_URL}/auth/me`, {
        credentials: "include",
    });

    const data = await res.json();

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

    const data = await res.json();

    if (!res.ok) {
        throw new Error(data.error || "Logout failed");
    }

    return data;
}

export async function getMyPrompts() {
    const res = await fetch(`${BASE_URL}/prompts/me`, {
        credentials: "include",
    });

    const data = await res.json();

    if (!res.ok) {
        throw new Error(data.error || "Failed to fetch user prompts");
    }

    return data;
}