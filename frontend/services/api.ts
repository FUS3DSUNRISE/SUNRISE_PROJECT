const BASE_URL = "http://127.0.0.1:5000";


export async function createPrompt(prompt: string) {
    const res = await fetch(`${BASE_URL}/prompts`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ prompt }),
    });

    if (!res.ok) {
        throw new Error("Failed to create prompt");
    }

    return res.json(); // { id, status }
}

export async function getPrompt(id: number) {
    const res = await fetch(`${BASE_URL}/prompts/${id}`);

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
  onProcessing: () => void = () => {}
) {
  const created = await createPrompt(prompt);
  return await pollPrompt(created.id, onProcessing);
}