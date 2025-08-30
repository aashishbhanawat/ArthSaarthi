import { useMutation, useQueryClient } from '@tanstack/react-query';
import { updateProfile, changePassword } from '../services/userApi';
import { UserUpdateMe, UserPasswordChange, User } from '../types/user';
import { useAuth } from '../context/AuthContext';

export const useUpdateProfile = () => {
  const { setUser } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (userData: UserUpdateMe) => updateProfile(userData),
    onSuccess: (updatedUser: User) => {
      // Update the user in the auth context
      setUser(updatedUser);
      // Optionally, invalidate queries that depend on user data
      // For example, if there's a 'user' query key
      queryClient.invalidateQueries({ queryKey: ['user'] });
    },
    onError: (error) => {
      console.error('Error updating profile:', error);
      // Here you could show a toast notification
    },
  });
};

export const useChangePassword = () => {
  return useMutation({
    mutationFn: (passwordData: UserPasswordChange) => changePassword(passwordData),
    onSuccess: () => {
      // Password changed successfully, maybe show a notification
      console.log('Password changed successfully');
    },
    onError: (error) => {
      console.error('Error changing password:', error);
      // Here you could show a toast notification
    },
  });
};
