import { createPrompt, pollPrompt } from "./api";

export async function runGenerationFlow(
    prompt: string,
    onSubmitted: () => void,
    onProcessing: () => void,
    onSuccess: (result: any) => void,
    onError: (message: string) => void
) {
    try {
        onSubmitted();

        const { id } = await createPrompt(prompt);

        const result = await pollPrompt(id, onProcessing);

        onSuccess(result);
    } catch (e: any) {
        onError(e.message);
    }
}