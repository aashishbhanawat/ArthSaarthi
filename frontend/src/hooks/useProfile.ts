import { useMutation, useQueryClient } from '@tanstack/react-query';
import { updateProfile, changePassword } from '../services/userApi';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { UserUpdateMe, UserPasswordChange } from '../types/user';
import { ApiError, getErrorMessage } from '../types/api';

export const useUpdateProfile = () => {
  const queryClient = useQueryClient();
  const { setUser } = useAuth();
  const { showToast } = useToast();

  return useMutation({
    mutationFn: (data: UserUpdateMe) => updateProfile(data),
    onSuccess: (updatedUser) => {
      setUser(updatedUser);
      queryClient.invalidateQueries({ queryKey: ['user'] });
      showToast('Profile updated successfully!', 'success');
    },
    onError: (error: ApiError) => {
      showToast(`Error: ${getErrorMessage(error)}`, 'error');
    },
  });
};

export const useChangePassword = () => {
  const { showToast } = useToast();
  return useMutation({
    mutationFn: (data: UserPasswordChange) => changePassword(data),
    onSuccess: () => {
      showToast('Password changed successfully!', 'success');
    },
    onError: (error: ApiError) => {
      showToast(`Error: ${getErrorMessage(error)}`, 'error');
    },
  });
};
