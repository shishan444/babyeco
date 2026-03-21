import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User, Family, LoginCredentials, RegisterData } from "@/types/auth";
import { authClient } from "@/lib/api/authClient";

interface AuthState {
  user: User | null;
  family: Family | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  clearError: () => void;
  checkSession: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      family: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (credentials: LoginCredentials) => {
        set({ isLoading: true, error: null });
        try {
          const response = await authClient.login(credentials);
          set({
            user: response.user,
            family: response.family,
            token: response.token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : "Login failed",
            isLoading: false,
          });
        }
      },

      register: async (data: RegisterData) => {
        set({ isLoading: true, error: null });
        try {
          const response = await authClient.register(data);
          set({
            user: response.user,
            family: response.family,
            token: response.token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : "Registration failed",
            isLoading: false,
          });
        }
      },

      logout: () => {
        set({
          user: null,
          family: null,
          token: null,
          isAuthenticated: false,
        });
      },

      clearError: () => set({ error: null }),

      checkSession: async () => {
        const { token } = get();
        if (!token) {
          set({ isAuthenticated: false, user: null, family: null });
          return;
        }

        try {
          const response = await authClient.validateToken(token);
          set({
            user: response.user,
            family: response.family,
            isAuthenticated: true,
          });
        } catch (error) {
          // Token is invalid, clear session
          set({
            user: null,
            family: null,
            token: null,
            isAuthenticated: false,
          });
        }
      },
    }),
    {
      name: "auth-storage",
    }
  )
);
