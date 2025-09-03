import { renderHook } from '@testing-library/react';
import { usePrivacySensitiveCurrency, formatCurrency as originalFormatCurrency } from '../../utils/formatting';
import * as PrivacyContext from '../../context/PrivacyContext';

describe('usePrivacySensitiveCurrency', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('should return the real currency string when privacy mode is off', () => {
    jest.spyOn(PrivacyContext, 'usePrivacy').mockReturnValue({
      isPrivacyMode: false,
      togglePrivacyMode: () => {},
    });

    const { result } = renderHook(() => usePrivacySensitiveCurrency());
    const formatCurrency = result.current;
    expect(formatCurrency(123456.78)).toBe(originalFormatCurrency(123456.78));
  });

  it('should return the obscured placeholder string when privacy mode is on', () => {
    jest.spyOn(PrivacyContext, 'usePrivacy').mockReturnValue({
      isPrivacyMode: true,
      togglePrivacyMode: () => {},
    });

    const { result } = renderHook(() => usePrivacySensitiveCurrency());
    const formatCurrency = result.current;
    expect(formatCurrency(123456.78)).toBe('₹**,***.**');
  });
});
