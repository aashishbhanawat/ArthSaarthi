import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider, UseMutationResult } from '@tanstack/react-query';
import InterestRateFormModal from '../../../components/Admin/InterestRateFormModal';
import * as useInterestRatesHook from '../../../hooks/useInterestRates';
import { HistoricalInterestRate, HistoricalInterestRateCreate, HistoricalInterestRateUpdate } from '../../../types/interestRate';

const queryClient = new QueryClient();

const renderWithClient = (ui: React.ReactElement) => {
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  );
};

const mockCreateMutation = jest.fn();
const mockUpdateMutation = jest.fn();

jest.spyOn(useInterestRatesHook, 'useCreateInterestRate').mockReturnValue({
  mutate: mockCreateMutation,
  isPending: false,
} as unknown as UseMutationResult<HistoricalInterestRate, Error, HistoricalInterestRateCreate, unknown>);

jest.spyOn(useInterestRatesHook, 'useUpdateInterestRate').mockReturnValue({
  mutate: mockUpdateMutation,
  isPending: false,
} as unknown as UseMutationResult<HistoricalInterestRate, Error, { rateId: string; rateData: HistoricalInterestRateUpdate; }, unknown>);

describe('InterestRateFormModal', () => {
  const onCloseMock = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  const mockRate: HistoricalInterestRate = {
    id: '1',
    scheme_name: 'PPF',
    start_date: '2023-04-01',
    end_date: '2024-03-31',
    rate: 7.1,
  };

  describe('Create Mode', () => {
    it('renders correctly and submits new rate data', async () => {
      renderWithClient(<InterestRateFormModal isOpen={true} onClose={onCloseMock} rateToEdit={null} />);

      expect(screen.getByRole('heading', { name: 'Add New Interest Rate' })).toBeInTheDocument();

      fireEvent.change(screen.getByLabelText('Scheme Name'), { target: { value: 'NSC' } });
      fireEvent.change(screen.getByLabelText('Start Date'), { target: { value: '2024-01-01' } });
      fireEvent.change(screen.getByLabelText(/End Date/i), { target: { value: '2024-03-31' } });
      fireEvent.change(screen.getByLabelText('Interest Rate (%)'), { target: { value: '7.7' } });

      fireEvent.click(screen.getByRole('button', { name: 'Create Rate' }));

      await waitFor(() => {
        expect(mockCreateMutation).toHaveBeenCalledWith(
          expect.objectContaining({
            scheme_name: 'NSC',
            start_date: '2024-01-01',
            end_date: '2024-03-31',
            rate: 7.7,
          }),
          expect.any(Object)
        );
      });
    });
  });

  describe('Edit Mode', () => {
    it('renders with pre-filled data and submits updated data', async () => {
      renderWithClient(<InterestRateFormModal isOpen={true} onClose={onCloseMock} rateToEdit={mockRate} />);

      expect(screen.getByRole('heading', { name: 'Edit Interest Rate' })).toBeInTheDocument();
      expect(screen.getByLabelText('Scheme Name')).toHaveValue(mockRate.scheme_name);
      expect(screen.getByLabelText('Interest Rate (%)')).toHaveValue(mockRate.rate);

      fireEvent.change(screen.getByLabelText('Interest Rate (%)'), { target: { value: '7.2' } });

      fireEvent.click(screen.getByRole('button', { name: 'Save Changes' }));

      await waitFor(() => {
        expect(mockUpdateMutation).toHaveBeenCalledWith(
          expect.objectContaining({
            rateId: mockRate.id,
            rateData: expect.objectContaining({ rate: 7.2 }),
          }),
          expect.any(Object)
        );
      });
    });

    it('displays an API error message on failure', async () => {
      mockUpdateMutation.mockImplementation((_data, options) => {
        options.onError({ response: { data: { detail: 'Invalid date range' } } });
      });

      renderWithClient(<InterestRateFormModal isOpen={true} onClose={onCloseMock} rateToEdit={mockRate} />);

      fireEvent.click(screen.getByRole('button', { name: 'Save Changes' }));

      await waitFor(() => {
        expect(screen.getByText('Invalid date range')).toBeInTheDocument();
      });
    });
  });
});