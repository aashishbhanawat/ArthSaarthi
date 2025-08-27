import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as adminApi from '../services/adminApi';
import * as userApi from '../services/userApi';
import { UserCreate, UserUpdate, UserPasswordChange } from '../types/user';
import { useAuth } from '../context/AuthContext';

const USERS_QUERY_KEY = 'users';

export const useUsers = () => {
  return useQuery({
    queryKey: [USERS_QUERY_KEY],
    queryFn: adminApi.getUsers,
  });
};

export const useCreateUser = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (userData: UserCreate) => adminApi.createUser(userData),
    onSuccess: () => {
      // Invalidate and refetch the users query to show the new user
      queryClient.invalidateQueries({ queryKey: [USERS_QUERY_KEY] });
    },
    onError: (error: { response?: { data?: { detail?: string } } }) => {
      // It's good practice to handle errors, maybe show a toast notification
      console.error('Error creating user:', error);
      // You can throw the error to be caught by the component's onSubmit
      throw error;
    },
  });
};

export const useUpdatePassword = () => {
  return useMutation<void, Error, UserPasswordChange>({
    mutationFn: (passwordData: UserPasswordChange) => userApi.updatePassword(passwordData),
    onError: (error: { response?: { data?: { detail?: string } } }) => {
      console.error('Error updating password:', error);
      throw error;
    },
  });
};

export const useUpdateMe = () => {
  const { setUser } = useAuth();
  return useMutation({
    mutationFn: (userData: { full_name: string }) => userApi.updateMe(userData),
    onSuccess: (data) => {
      if (setUser) {
        setUser(data);
      }
    },
    onError: (error: { response?: { data?: { detail?: string } } }) => {
      console.error('Error updating user:', error);
      throw error;
    },
  });
};

export const useUpdateUser = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      userId,
      userData,
    }: {
      userId: string;
      userData: UserUpdate;
    }) => adminApi.updateUser(userId, userData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [USERS_QUERY_KEY] });
    },
    onError: (error: { response?: { data?: { detail?: string } } }) => {
      console.error('Error updating user:', error);
      throw error;
    },
  });
};

export const useDeleteUser = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (userId: string) => adminApi.deleteUser(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [USERS_QUERY_KEY] });
    },
    onError: (error: { response?: { data?: { detail?: string } } }) => {
      console.error('Error deleting user:', error);
      throw error;
    },
  });
};