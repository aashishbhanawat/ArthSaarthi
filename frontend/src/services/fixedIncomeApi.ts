import api from './api';
import { Asset } from '../types/asset';
import { FixedDepositCreate, BondCreate, PublicProvidentFundCreate } from '../types/fixed_income';

export const createFixedDeposit = async (portfolioId: string, data: FixedDepositCreate): Promise<Asset> => {
  const response = await api.post<Asset>(`/api/v1/portfolios/${portfolioId}/fixed-deposits`, data);
  return response.data;
};

export const createBond = async (portfolioId: string, data: BondCreate): Promise<Asset> => {
    const response = await api.post<Asset>(`/api/v1/portfolios/${portfolioId}/bonds`, data);
    return response.data;
};

export const createPpf = async (portfolioId: string, data: PublicProvidentFundCreate): Promise<Asset> => {
    const response = await api.post<Asset>(`/api/v1/portfolios/${portfolioId}/ppf`, data);
    return response.data;
};
