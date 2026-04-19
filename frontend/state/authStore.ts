import { create } from "zustand";


export interface AuthUser {
    id: number;
    username: string;
    email: string;
}


interface AuthStore {
    user: AuthUser | null;
    setUser: (user: AuthUser | null) => void;
    logout: () => void;
}


export const useAuthStore = create<AuthStore>((set) => ({
    user: null,


    setUser: (user) => set({ user }),


    logout: () => set({ user: null }),
}));
