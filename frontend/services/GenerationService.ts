import { parameter } from "three/tsl";
import { createPrompt, pollPrompt, FormattedParameters } from "./api";

export async function runGenerationFlow(
    prompt: string,
    parameters: FormattedParameters, 
    onSubmitted: () => void,
    onProcessing: () => void,
    onSuccess: (result: any) => void,
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
    } catch (e: any) {
        onError(e.message);
    }
}