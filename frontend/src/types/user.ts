export interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_admin: boolean;
}

export type UserCreate = {
  full_name: string;
  email: string;
  password: string;
  is_admin?: boolean;
};

export type UserUpdate = Partial<{
  full_name: string;
  email: string;
  is_active: boolean;
  is_admin: boolean;
  password?: string;
}>;

export interface UserUpdateMe {
  full_name?: string;
}

export interface UserPasswordChange {
  old_password: string;
  new_password: string;
}