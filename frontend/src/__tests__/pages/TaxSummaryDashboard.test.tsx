import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { TaxSummaryDashboard } from '../../pages/TaxSummaryDashboard';
import * as taxSummaryService from '../../services/taxSummaryService';

jest.mock('../../services/taxSummaryService');

const mockGetTaxSummary = taxSummaryService.getTaxSummary as jest.Mock;

describe('TaxSummaryDashboard Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();

    mockGetTaxSummary.mockResolvedValue({
      financial_year: '2024-25',
      user_id: 1,
      income_summary: {
        gross_salary: 1200000,
        business_income: 0,
        dividend_income: 0,
        other_income: 0,
        total_gross_income: 1200000,
        total_tds_credits: 50000,
      },
      exemptions_summary_old: {
        standard_deduction: 50000,
        hra_exemption: 0,
        professional_tax: 0,
        children_education_allowance: 0,
        employer_nps: 0,
        total_exemptions: 50000,
      },
      exemptions_summary_new: {
        standard_deduction: 75000,
        hra_exemption: 0,
        professional_tax: 0,
        children_education_allowance: 0,
        employer_nps: 0,
        total_exemptions: 75000,
      },
      deduction_summary: {
        section_80c: 150000,
        section_80d: 25000,
        section_80ccd_1b: 0,
        section_80e: 0,
        section_80g: 0,
        section_80tta_80ttb: 0,
        other_deductions: 0,
        total_chapter_via_deductions: 175000,
      },
      capital_gains_summary: {
        stcg_taxable: 0,
        ltcg_taxable: 0,
        stcg_tax: 0,
        ltcg_tax: 0,
        total_capital_gains_tax: 0,
      },
      old_regime: {
        regime_type: 'OLD',
        gross_income: 1200000,
        exemptions: 50000,
        chapter_via_deductions: 175000,
        taxable_income: 975000,
        tax_on_slabs: 107500,
        capital_gains_tax: 0,
        section_87a_rebate: 0,
        tax_after_rebate: 107500,
        cess: 4300,
        total_tax_liability: 111800,
        tds_credits: 50000,
        net_tax_payable: 61800,
      },
      new_regime: {
        regime_type: 'NEW',
        gross_income: 1200000,
        exemptions: 75000,
        chapter_via_deductions: 0,
        taxable_income: 1125000,
        tax_on_slabs: 88750,
        capital_gains_tax: 0,
        section_87a_rebate: 0,
        tax_after_rebate: 88750,
        cess: 3550,
        total_tax_liability: 92300,
        tds_credits: 50000,
        net_tax_payable: 42300,
      },
      recommended_regime: 'NEW',
      tax_savings: 19500,
      disclaimer: 'This Tax Readiness Summary and Tax Estimation tool is provided strictly for INFORMATIONAL, EDUCATIONAL, AND TAX/INVESTMENT PLANNING PURPOSES ONLY.',
    });
  });

  test('renders title, legal warning disclaimer (FR16.4.1), and regime comparison cards', async () => {
    render(<TaxSummaryDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Tax Readiness Summary (FR16.4)')).toBeInTheDocument();
    });

    // Check Legal Disclaimer Banner
    expect(screen.getByText('IMPORTANT LEGAL NOTICE & TAX DISCLAIMER (FR16.4.1)')).toBeInTheDocument();
    expect(screen.getByText(/INFORMATIONAL, EDUCATIONAL, AND TAX\/INVESTMENT PLANNING PURPOSES ONLY/i)).toBeInTheDocument();

    // Check Regime Cards
    expect(screen.getByText('Old Tax Regime')).toBeInTheDocument();
    expect(screen.getByText('New Tax Regime (Section 115BAC)')).toBeInTheDocument();
  });
});
