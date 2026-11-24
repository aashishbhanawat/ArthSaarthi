import { render, screen } from '@testing-library/react';
import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { AIIntelligenceTab } from './AIIntelligenceTab';
import * as mlApi from '../../services/mlApi';
import * as AuthContext from '../../context/AuthContext';

jest.mock('../../services/mlApi');
const mockedMlApi = mlApi as jest.Mocked<typeof mlApi>;

describe('AIIntelligenceTab (User Profile)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedMlApi.getEdgeModels.mockResolvedValue([
      {
        id: 'finbert_int8',
        name: 'FinBERT INT8 Quantized',
        description: 'State-of-the-art financial sentiment transformer.',
        size_mb: 105.2,
        download_url: 'https://example.com/finbert',
        filename: 'finbert_int8.onnx',
        engine_type: 'finbert_onnx',
        status: 'ACTIVE',
        progress_percentage: 100,
        downloaded_bytes: 105200000,
        total_bytes: 105200000,
      },
    ]);
  });

  const renderTab = (isAdmin: boolean) => {
    jest.spyOn(AuthContext, 'useAuth').mockReturnValue({
      user: {
        id: 'user-1',
        email: 'test@example.com',
        is_active: true,
        is_admin: isAdmin,
        full_name: 'Test User',
      },
      token: 'fake-token',
      login: jest.fn(),
      logout: jest.fn(),
      loading: false,
      deploymentMode: 'server',
      isOffline: false,
      hasMasterKey: true,
      setHasMasterKey: jest.fn(),
    });

    return render(
      <BrowserRouter>
        <AIIntelligenceTab />
      </BrowserRouter>
    );
  };

  test('renders read-only active model status and sentiment testing without destructive download buttons', async () => {
    renderTab(false);

    expect(await screen.findByText('FinBERT INT8 Quantized')).toBeInTheDocument();
    expect(screen.getByText('Active (ONNX Inference)')).toBeInTheDocument();

    // Verify destructive admin buttons are NOT present in user profile
    expect(screen.queryByRole('button', { name: /Download Model/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Delete Model/i })).not.toBeInTheDocument();

    // Normal user does not see admin maintenance link
    expect(screen.queryByText('Manage Models in Administration')).not.toBeInTheDocument();

    // Interactive tester is present
    expect(screen.getByText('🧪 Test Active Sentiment Engine')).toBeInTheDocument();
  });

  test('renders admin link to System Maintenance when user is admin', async () => {
    renderTab(true);

    expect(await screen.findByText('FinBERT INT8 Quantized')).toBeInTheDocument();
    const adminLink = screen.getByRole('link', { name: /Manage Models in Administration/i });
    expect(adminLink).toBeInTheDocument();
    expect(adminLink).toHaveAttribute('href', '/admin/maintenance');
  });
});
