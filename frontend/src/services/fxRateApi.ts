
import api from '~/services/api';

export const getFxRate = async (source: string, to: string, date: string): Promise<{ rate: number }> => {
    const response = await api.get(`/api/v1/fx-rate?source=${source}&to=${to}&date=${date}`);
    return response.data;
};
