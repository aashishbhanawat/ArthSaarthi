import apiClient from './api';

export interface BrokerCredentialResponse {
  id: string;
  provider_name: string;
  api_key: string;
  is_active: boolean;
  is_authenticated: boolean;
  token_issued_at?: string;
  token_expires_at?: string;
  created_at: string;
  updated_at: string;
}

export interface SaveBrokerCredentialPayload {
  provider_name: string;
  api_key: string;
  api_secret: string;
}

export const getBrokerCredentials = async (): Promise<BrokerCredentialResponse[]> => {
  const response = await apiClient.get<BrokerCredentialResponse[]>('/api/v1/broker/credentials');
  return response.data;
};

export const saveBrokerCredentials = async (
  payload: SaveBrokerCredentialPayload
): Promise<BrokerCredentialResponse> => {
  const response = await apiClient.post<BrokerCredentialResponse>('/api/v1/broker/credentials', payload);
  return response.data;
};

export const getIciciLoginUrl = async (): Promise<{ provider_name: string; login_url: string }> => {

  const response = await apiClient.get<{ provider_name: string; login_url: string }>('/api/v1/broker/icici/login-url');
  return response.data;
};

export const authenticateIciciSession = async (
  session_token: string
): Promise<BrokerCredentialResponse> => {
  const response = await apiClient.post<BrokerCredentialResponse>('/api/v1/broker/icici/authenticate', {
    provider_name: 'icici_breeze',
    session_token,
  });
  return response.data;
};

export const deleteBrokerCredentials = async (provider_name: string): Promise<{ message: string }> => {
  const response = await apiClient.delete<{ message: string }>(`/api/v1/broker/credentials/${provider_name}`);
  return response.data;
};
