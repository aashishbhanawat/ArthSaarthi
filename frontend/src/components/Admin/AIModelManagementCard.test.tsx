import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { AIModelManagementCard } from './AIModelManagementCard';
import * as mlApi from '../../services/mlApi';
import { ToastProvider } from '../../context/ToastContext';

jest.mock('../../services/mlApi');
const mockedMlApi = mlApi as jest.Mocked<typeof mlApi>;

const mockModels: mlApi.EdgeModelInfo[] = [
  {
    id: 'finbert_int8',
    name: 'FinBERT INT8 Quantized',
    description: 'State-of-the-art financial sentiment transformer.',
    size_mb: 105.2,
    download_url: 'https://example.com/finbert',
    filename: 'finbert_int8.onnx',
    engine_type: 'finbert_onnx',
    status: 'NOT_DOWNLOADED',
    progress_percentage: 0,
    downloaded_bytes: 0,
    total_bytes: 105200000,
  },
];

describe('AIModelManagementCard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const renderComponent = () =>
    render(
      <ToastProvider>
        <AIModelManagementCard />
      </ToastProvider>
    );

  test('renders models list with status and download action', async () => {
    mockedMlApi.getEdgeModels.mockResolvedValue(mockModels);

    renderComponent();

    expect(await screen.findByText('Shared Edge ML Models')).toBeInTheDocument();
    expect(screen.getByText('FinBERT INT8 Quantized')).toBeInTheDocument();
    expect(screen.getByText(/Not Downloaded/i)).toBeInTheDocument();

    const downloadBtn = screen.getByRole('button', { name: /Download to Server/i });
    expect(downloadBtn).toBeInTheDocument();
  });

  test('handles downloading model triggers downloadEdgeModel', async () => {
    mockedMlApi.getEdgeModels.mockResolvedValue(mockModels);
    mockedMlApi.downloadEdgeModel.mockResolvedValue({
      ...mockModels[0],
      status: 'DOWNLOADING',
      progress_percentage: 25,
    });

    renderComponent();

    const downloadBtn = await screen.findByRole('button', { name: /Download to Server/i });
    fireEvent.click(downloadBtn);

    await waitFor(() => {
      expect(mockedMlApi.downloadEdgeModel).toHaveBeenCalledWith('finbert_int8');
    });
  });

  test('renders active status with delete action', async () => {
    const activeModels: mlApi.EdgeModelInfo[] = [
      {
        ...mockModels[0],
        status: 'ACTIVE',
        progress_percentage: 100,
      },
    ];
    mockedMlApi.getEdgeModels.mockResolvedValue(activeModels);
    mockedMlApi.deleteEdgeModel.mockResolvedValue(true);

    // Mock confirm dialog
    jest.spyOn(window, 'confirm').mockImplementation(() => true);

    renderComponent();

    expect(await screen.findByText('Active (ONNX Inference)')).toBeInTheDocument();
    const deleteBtn = screen.getByRole('button', { name: /Delete Model/i });
    expect(deleteBtn).toBeInTheDocument();

    fireEvent.click(deleteBtn);

    await waitFor(() => {
      expect(mockedMlApi.deleteEdgeModel).toHaveBeenCalledWith('finbert_int8');
    });
  });
});
