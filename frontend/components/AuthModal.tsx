"use client";

type Props = {
    type: "login" | "signup";
    onCloseAction: () => void;
};

export default function AuthModal({ type, onCloseAction }: Props) {
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div className="w-full max-w-md rounded-2xl bg-[#0f111a] border border-white/10 p-8 shadow-xl">

                {/* Header */}
                <div className="flex justify-between items-center mb-6">
                    <h2 className="text-2xl font-semibold">
                        {type === "login" ? "Login" : "Create Account"}
                    </h2>
                    <button onClick={onCloseAction} className="text-white/60 hover:text-white">
                        ✕
                    </button>
                </div>

                {/* Form */}
                <div className="flex flex-col gap-4">
                    <input
                        type="email"
                        placeholder="Email"
                        className="rounded-lg bg-[#1a1d2b] px-4 py-3 outline-none"
                    />
                    <input
                        type="password"
                        placeholder="Password"
                        className="rounded-lg bg-[#1a1d2b] px-4 py-3 outline-none"
                    />

                    <button className="mt-4 rounded-lg bg-[#4f5dff] py-3 font-medium hover:bg-[#5d69ff]">
                        {type === "login" ? "Login" : "Sign Up"}
                    </button>
                </div>
            </div>
        </div>
    );
}