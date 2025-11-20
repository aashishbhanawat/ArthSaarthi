/* eslint-disable testing-library/no-node-access */
import apiClient from './api';
import { User, UserUpdateMe, UserPasswordChange } from '../types/user';
import { Msg } from '../types/msg';

export const updateProfile = async (data: UserUpdateMe): Promise<User> => {
  const response = await apiClient.put<User>('/api/v1/users/me', data);
  return response.data;
};

export const changePassword = async (data: UserPasswordChange): Promise<Msg> => {
  const response = await apiClient.post<Msg>('/api/v1/auth/me/change-password', data);
  return response.data;
};

export const downloadBackup = async (): Promise<void> => {
  const response = await apiClient.get('/api/v1/users/me/backup', {
    responseType: 'blob',
  });

  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;

  const contentDisposition = response.headers['content-disposition'];
  let filename = 'arthsaarthi_backup.json';
  if (contentDisposition) {
    const match = contentDisposition.match(/filename="?([^"]+)"?/);
    if (match && match[1]) {
      filename = match[1];
    }
  }

  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.remove();
};

export const restoreBackup = async (file: File): Promise<void> => {
  const formData = new FormData();
  formData.append('file', file);
  await apiClient.post('/api/v1/users/me/restore', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};
