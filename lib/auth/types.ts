export type UserRole = 'admin' | 'hr' | 'employee';

export interface User {
  id: string;
  email: string;
  password_hash: string;
  role: UserRole;
  full_name: string;
  employee_code: string | null;
  created_at: string;
  updated_at: string;
}

export interface SessionPayload {
  userId: string;
  email: string;
  role: UserRole;
  fullName: string;
  employeeCode: string | null;
  iat: number;
  exp: number;
}

export interface AuthResult {
  success: boolean;
  user?: {
    id: string;
    email: string;
    role: UserRole;
    full_name: string;
    employee_code: string | null;
  };
  error?: string;
}

export interface RegisterInput {
  email: string;
  password: string;
  name: string;
}

export interface LoginInput {
  email: string;
  password: string;
}