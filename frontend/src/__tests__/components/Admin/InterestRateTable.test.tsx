import { render, screen, fireEvent } from '@testing-library/react';
import InterestRateTable from '../../../components/Admin/InterestRateTable';
import { HistoricalInterestRate } from '../../../types/interestRate';

const mockRates: HistoricalInterestRate[] = [
  {
    id: '1',
    scheme_name: 'PPF',
    start_date: '2023-04-01',
    end_date: '2024-03-31',
    rate: 7.1,
  },
  {
    id: '2',
    scheme_name: 'NSC',
    start_date: '2023-07-01',
    end_date: '2023-09-30',
    rate: 7.7,
  },
];

describe('InterestRateTable', () => {
  const onEditMock = jest.fn();
  const onDeleteMock = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders a table with the correct data', () => {
    render(<InterestRateTable rates={mockRates} onEdit={onEditMock} onDelete={onDeleteMock} />);

    expect(screen.getByText('PPF')).toBeInTheDocument();
    expect(screen.getByText('NSC')).toBeInTheDocument();
    expect(screen.getByText('7.10%')).toBeInTheDocument();
    expect(screen.getByText('7.70%')).toBeInTheDocument();
  });

  it('calls onEdit with the correct rate when the edit button is clicked', () => {
    render(<InterestRateTable rates={mockRates} onEdit={onEditMock} onDelete={onDeleteMock} />);
    const editButtons = screen.getAllByRole('button', { name: /edit/i });

    fireEvent.click(editButtons[0]); // This will be the 'PPF' row
    expect(onEditMock).toHaveBeenCalledWith(mockRates[0]);
  });

  it('calls onDelete with the correct rate when the delete button is clicked', () => {
    render(<InterestRateTable rates={mockRates} onEdit={onEditMock} onDelete={onDeleteMock} />);
    const deleteButtons = screen.getAllByRole('button', { name: /delete/i });

    fireEvent.click(deleteButtons[1]); // This will be the 'NSC' row
    expect(onDeleteMock).toHaveBeenCalledWith(mockRates[1]);
  });
});