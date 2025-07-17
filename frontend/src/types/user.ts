export interface User {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_admin: boolean;
}

export type UserCreate = {
  full_name: string;
  email: string;
  password: string;
};

export type UserUpdate = Partial<{
  full_name: string;
  email: string;
  is_active: boolean;
  is_admin: boolean;
}>;