import axios from "axios"
import applyCaseMiddleware from "axios-case-converter"
import { jwtDecode } from "jwt-decode"

const API_URL = "http://localhost:8000/api"

interface AuthResponse {
  access_token: string
  token_type: string
}

interface DecodedToken {
  sub: string
  name: string
  email: string
  exp: number
}

// Store token in localStorage
const setToken = (token: string) => {
  localStorage.setItem("auth_token", token)
}

// Get token from localStorage
export const getToken = (): string | null => {
  if (typeof window !== "undefined") {
    return localStorage.getItem("auth_token")
  }
  return null
}

// Remove token from localStorage
export const removeToken = () => {
  localStorage.removeItem("auth_token")
}

// Check if token is valid
const isTokenValid = (token: string): boolean => {
  try {
    const decoded = jwtDecode<DecodedToken>(token)
    const currentTime = Date.now() / 1000
    return decoded.exp > currentTime
  } catch {
    return false
  }
}

// Register a new user
export const register = async (name: string, email: string, password: string) => {
  const role = "operator"
  const response = await fetch(`${API_URL}/auth/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ name, email, password, role }),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.message || "Registration failed")
  }

  return await response.json()
}

// Login user
export const login = async (username: string, password: string) => {
  const formData = new FormData()
  const API_URL = "http://localhost:8000/api"
  const client = applyCaseMiddleware(axios.create())
  formData.append("username", username)
  formData.append("password", password)
  const response = await fetch(`${API_URL}/auth/jwt/login`, {
    method: "POST",
    body: formData,
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.message || "Login failed")
  }

  const data: AuthResponse = await response.json()
  const {data: user} = await client.get(`${API_URL}/users/me`,
    {
      headers: {
        "Authorization": `Bearer ${data.access_token}`,
      },
    })
  localStorage.setItem("user", JSON.stringify(user))
  
  console.log(data)
  setToken(data.access_token)
  return data
}

// Logout user
export const logout = async () => {
  removeToken()
}

// Get authenticated user profile
export const getUserProfile = async () => {
  const token = getToken()

  if (!token || !isTokenValid(token)) {
    throw new Error("Not authenticated")
  }

  const response = await fetch(`${API_URL}/users/profile`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    if (response.status === 401) {
      removeToken()
      throw new Error("Session expired")
    }
    throw new Error("Failed to fetch user profile")
  }

  return await response.json()
}

// Check if user is authenticated
export const isAuthenticated = (): boolean => {
  const token = getToken()
  return !!token && isTokenValid(token)
}
