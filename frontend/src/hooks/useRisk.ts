import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as riskApi from '../services/riskApi';
import { UserRiskProfileCreate } from '../types/risk';

export const useRiskProfile = () => {
    return useQuery({
        queryKey: ['riskProfile'],
        queryFn: riskApi.getRiskProfile,
        retry: false,
    });
};

export const useSaveRiskProfile = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (profile: UserRiskProfileCreate) => riskApi.createOrUpdateRiskProfile(profile),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['riskProfile'] });
        },
    });
};
