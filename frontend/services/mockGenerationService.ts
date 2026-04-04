export async function simulateGenerationFlow(
    onSubmitted: () => void,
    onProcessing: () => void,
    onSuccess: () => void,
    onError: (message: string) => void,
    shouldFail = false
) {
    onSubmitted();

    await new Promise((resolve) => setTimeout(resolve, 800));

    onProcessing();

    await new Promise((resolve) => setTimeout(resolve, 2000));

    if (shouldFail) {
        onError("Oops! Something went wrong while generating the model.");
        return;
    }

    onSuccess();
}