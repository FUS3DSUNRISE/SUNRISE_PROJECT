import PromptInput from "@/components/PromptInput";
import GenerateButton from "@/components/GenerateButton";
import ResultSection from "@/components/ResultSection";

export default function Home() {
    return (
        <main className="h-screen flex flex-col">
            <h1 className="text-2xl font-bold p-4">SUNRISE</h1>

            <div className="flex flex-1">
                {/* LEFT */}
                <div className="w-1/3 border-r p-4">
                    <PromptInput />
                    <GenerateButton />
                </div>

                {/* RIGHT */}
                <div className="flex-1 p-4">
                    <ResultSection />
                </div>
            </div>
        </main>
    );
}