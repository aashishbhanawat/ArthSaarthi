import { UUID } from 'crypto';

export interface HistoricalInterestRate {
  id: UUID;
  scheme_name: string;
  start_date: string;
  end_date: string | null;
  rate: number;
}

export type HistoricalInterestRateCreate = Omit<HistoricalInterestRate, 'id'>;

export type HistoricalInterestRateUpdate = Partial<HistoricalInterestRateCreate>;