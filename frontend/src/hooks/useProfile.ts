import { useMutation, useQueryClient } from '@tanstack/react-query';
import { updateProfile, changePassword } from '../services/userApi';
import { useAuth } from '../context/AuthContext';
import { UserUpdateMe, UserPasswordChange } from '../types/user';

interface ApiError {
  response?: {
    data?: {
      detail?: string;
    };
  };
  message: string;
}

export const useUpdateProfile = () => {
  const queryClient = useQueryClient();
  const { setUser } = useAuth();

  return useMutation({
    mutationFn: (data: UserUpdateMe) => updateProfile(data),
    onSuccess: (updatedUser) => {
      // Update the user in the auth context
      setUser(updatedUser);
      // Invalidate user-related queries if any
      queryClient.invalidateQueries({ queryKey: ['user'] });
      alert('Profile updated successfully!');
    },
    onError: (error: ApiError) => {
      alert(`Error updating profile: ${error.response?.data?.detail || error.message}`);
    },
  });
};

export const useChangePassword = () => {
  return useMutation({
    mutationFn: (data: UserPasswordChange) => changePassword(data),
    onSuccess: () => {
      alert('Password changed successfully!');
    },
    onError: (error: ApiError) => {
      alert(`Error changing password: ${error.response?.data?.detail || error.message}`);
    },
  });
};
