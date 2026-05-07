import { createPrompt, pollPrompt, FormattedParameters, PromptResponse } from "./api";

export async function runGenerationFlow(
    prompt: string,
    parameters: FormattedParameters, 
    onSubmitted: () => void,
    onProcessing: () => void,
    onSuccess: (result: PromptResponse) => void,
    onError: (message: string) => void
) {
    try {
        onSubmitted();

        const { id } = await createPrompt({ 
            prompt: prompt, 
            parameters: parameters 
        });

        const result = await pollPrompt(id, onProcessing);

        onSuccess(result);
    } catch (e: unknown) {
        onError(e instanceof Error ? e.message : "Generation failed.");
    }
}
