export async function generateModel(prompt: string) {
    // MOCK for now (replace later with real backend)
    console.log("Generating model for:", prompt);
    return new Promise((resolve) => {
        setTimeout(() => {
            resolve({
                modelUrl: "/sample.glb",
            });
        }, 2000);
    });
}