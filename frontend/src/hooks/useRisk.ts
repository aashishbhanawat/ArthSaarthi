import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as riskApi from '../services/riskApi';
import { UserRiskProfileCreate } from '../types/risk';

export const useRiskProfile = (enabled: boolean = true) => {
    return useQuery({
        queryKey: ['riskProfile'],
        queryFn: riskApi.getRiskProfile,
        enabled,
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
