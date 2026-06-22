import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  id: string
  name: string
  email: string
  role: string
  branch_id: string | null
}

interface AuthState {
  user: User | null
  access_token: string | null
  setAuth: (user: User, token: string) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      access_token: null,
      setAuth: (user, access_token) => set({ user, access_token }),
      logout: () => set({ user: null, access_token: null }),
    }),
    { name: 'kasirpro-auth' }
  )
)
