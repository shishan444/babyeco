export interface User {
  id: string;
  email: string;
  name: string;
  familyId: string;
}

export interface Family {
  id: string;
  name: string;
  createdAt: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  confirmPassword: string;
  familyName: string;
}

export interface AuthResponse {
  user: User;
  family: Family;
  token: string;
}

export interface ForgotPasswordData {
  email: string;
}

export interface ResetPasswordData {
  token: string;
  password: string;
  confirmPassword: string;
}
