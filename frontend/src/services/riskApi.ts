import apiClient from './api';
import { UserRiskProfile, UserRiskProfileCreate } from '../types/risk';

export const getRiskProfile = async (): Promise<UserRiskProfile> => {
    const response = await apiClient.get<UserRiskProfile>('/api/v1/risk/');
    return response.data;
};

export const createOrUpdateRiskProfile = async (profile: UserRiskProfileCreate): Promise<UserRiskProfile> => {
    const response = await apiClient.post<UserRiskProfile>('/api/v1/risk/', profile);
    return response.data;
};
