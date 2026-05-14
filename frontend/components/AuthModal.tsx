"use client";


import { useState } from "react";
import { getUserFriendlyErrorMessage, loginUser, signupUser } from "@/services/api";
import { useAuthStore } from "@/state/authStore";


type Props = {
    type: "login" | "signup";
    onCloseAction: () => void;
};


export default function AuthModal({ type, onCloseAction }: Props) {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [errorMessage, setErrorMessage] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const setUser = useAuthStore((s) => s.setUser);


    const handleSubmit = async () => {
        if (!email.trim() || !password.trim()) {
            setErrorMessage("Email and password are required.");
            return;
        }


        try {
            setLoading(true);
            setErrorMessage(null);


            const data =
            type === "login"
                ? await loginUser(email, password)
                : await signupUser(email, password);


            setUser(data.user);


            console.log(`${type} success:`, data);


            onCloseAction();
           
        } catch (e: unknown) {
            const message = getUserFriendlyErrorMessage(e, "Something went wrong.");
            setErrorMessage(message);
        } finally {
            setLoading(false);
        }
    };


    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div className="w-full max-w-md rounded-2xl border border-white/10 bg-[#0f111a] p-8 shadow-xl">
                <div className="mb-6 flex items-center justify-between">
                    <h2 className="text-2xl font-semibold">
                        {type === "login" ? "Login" : "Create Account"}
                    </h2>
                    <button onClick={onCloseAction} className="cursor-pointer text-white/60 hover:text-white">
                        ✕
                    </button>
                </div>


                <div className="flex flex-col gap-4">
                    <input
                        type="email"
                        placeholder="Email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="rounded-lg bg-[#1a1d2b] px-4 py-3 outline-none"
                    />


                    <input
                        type="password"
                        placeholder="Password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="rounded-lg bg-[#1a1d2b] px-4 py-3 outline-none"
                    />


                    {errorMessage && (
                        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
                            {errorMessage}
                        </div>
                    )}


                    <button
                        onClick={handleSubmit}
                        disabled={loading}
                        className="mt-4 cursor-pointer rounded-lg bg-[#4f5dff] py-3 font-medium hover:bg-[#5d69ff] disabled:cursor-wait disabled:opacity-70"
                    >
                        {loading
                            ? type === "login"
                                ? "Logging in..."
                                : "Signing up..."
                            : type === "login"
                                ? "Login"
                                : "Sign Up"}
                    </button>
                </div>
            </div>
        </div>
    );
}
