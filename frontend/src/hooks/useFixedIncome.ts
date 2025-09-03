import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createBond, createFixedDeposit, createPpf } from '../services/fixedIncomeApi';
import { BondCreate, FixedDepositCreate, PublicProvidentFundCreate } from '../types/fixed_income';

export const useCreateFixedDeposit = () => {
  const queryClient = useQueryClient();

  return useMutation(
    ({ portfolioId, data }: { portfolioId: string; data: FixedDepositCreate }) => createFixedDeposit(portfolioId, data),
    {
      onSuccess: () => {
        // Invalidate and refetch holdings and portfolio summary
        queryClient.invalidateQueries('holdings');
        queryClient.invalidateQueries('portfolioSummary');
      },
    }
  );
};

export const useCreateBond = () => {
    const queryClient = useQueryClient();

    return useMutation(
        ({ portfolioId, data }: { portfolioId: string; data: BondCreate }) => createBond(portfolioId, data),
        {
            onSuccess: () => {
                queryClient.invalidateQueries('holdings');
                queryClient.invalidateQueries('portfolioSummary');
            },
        }
    );
};

export const useCreatePpf = () => {
    const queryClient = useQueryClient();

    return useMutation(
        ({ portfolioId, data }: { portfolioId: string; data: PublicProvidentFundCreate }) => createPpf(portfolioId, data),
        {
            onSuccess: () => {
                queryClient.invalidateQueries('holdings');
                queryClient.invalidateQueries('portfolioSummary');
            },
        }
    );
};
