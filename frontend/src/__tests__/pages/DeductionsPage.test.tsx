import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import DeductionsPage from '../../pages/DeductionsPage';
import { PrivacyProvider } from '../../context/PrivacyContext';
import * as taxService from '../../services/taxDeductionService';

jest.mock('../../services/taxDeductionService');

const mockGetTaxDeductions = taxService.getTaxDeductions as jest.Mock;
const mockGetTaxDeductionsSummary = taxService.getTaxDeductionsSummary as jest.Mock;

const renderComponent = () => {
  return render(
    <PrivacyProvider>
      <DeductionsPage />
    </PrivacyProvider>
  );
};

describe('DeductionsPage Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();

    mockGetTaxDeductions.mockResolvedValue([
      {
        id: 'ded1',
        user_id: 'u1',
        financial_year: '2025-2026',
        section: '80C',
        title: 'LIC Policy Premium',
        amount: 150000,
        deduction_date: '2025-06-15',
        proof_notes: 'Policy #123456',
      },
    ]);

    mockGetTaxDeductionsSummary.mockResolvedValue({
      financial_year: '2025-2026',
      total_invested: 150000,
      total_eligible_deduction: 150000,
      sections: [
        {
          section: '80C',
          section_name: 'Section 80C (PPF, ELSS, EPF, LIC, etc.)',
          total_invested: 150000,
          max_limit: 150000,
          eligible_deduction: 150000,
        },
      ],
    });
  });

  test('renders page title, summary cards, statutory progress meter, and table rows', async () => {
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Tax Deductions & Chapter VI-A')).toBeInTheDocument();
    });

    expect(screen.getByText('+ Log Tax Deduction')).toBeInTheDocument();
    expect(screen.getByText('Statutory Section Limits & Progress')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getAllByText('LIC Policy Premium')[0]).toBeInTheDocument();
    });
    expect(screen.getByText('Policy #123456')).toBeInTheDocument();

  });

  test('opens add deduction modal when button is clicked', async () => {
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('+ Log Tax Deduction')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('+ Log Tax Deduction'));

    expect(screen.getByText('Log Tax Deduction')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('e.g. PPF Deposit, Health Insurance Policy')).toBeInTheDocument();
  });
});
