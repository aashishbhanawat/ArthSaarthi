import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { SchedulerDashboard } from './SchedulerDashboard';
import * as schedulerApi from '../../services/schedulerApi';
import { SchedulerSummary } from '../../types/scheduler';

jest.mock('../../services/schedulerApi');
const mockedApi = schedulerApi as jest.Mocked<typeof schedulerApi>;

const mockSummary: SchedulerSummary = {
  is_running: true,
  total_jobs: 1,
  active_jobs: 1,
  paused_jobs: 0,
  failed_last_24h: 0,
  jobs: [
    {
      id: 'daily_portfolio_snapshot',
      name: 'Daily Portfolio Valuation Snapshot',
      trigger: "cron[hour='0', minute='5']",
      next_run_time: '2026-11-03T00:05:00Z',
      status: 'ACTIVE',
      description: 'Calculates portfolio snapshots daily.',
    },
  ],
};

describe('SchedulerDashboard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedApi.getSchedulerSummary.mockResolvedValue(mockSummary);
    mockedApi.getScheduledJobLogs.mockResolvedValue({
      total: 1,
      items: [
        {
          id: 'log-1',
          job_id: 'daily_portfolio_snapshot',
          job_name: 'Daily Portfolio Valuation Snapshot',
          status: 'SUCCESS',
          started_at: '2026-11-02T00:05:00Z',
          finished_at: '2026-11-02T00:05:02Z',
          execution_time_seconds: 2.15,
          error_message: null,
          created_at: '2026-11-02T00:05:02Z',
        },
      ],
    });
    mockedApi.triggerJobNow.mockResolvedValue({
      message: "Job 'daily_portfolio_snapshot' triggered successfully.",
      job_id: 'daily_portfolio_snapshot',
      status: 'TRIGGERED',
    });
    mockedApi.pauseScheduledJob.mockResolvedValue({
      message: "Job 'daily_portfolio_snapshot' has been paused.",
      job_id: 'daily_portfolio_snapshot',
      status: 'PAUSED',
    });
  });

  it('renders scheduler dashboard with job list and status', async () => {
    render(<SchedulerDashboard />);

    expect(await screen.findByText('Automated Tasks')).toBeInTheDocument();
    expect(screen.getAllByText('Active').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Daily Portfolio Valuation Snapshot').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Daily at 00:05').length).toBeGreaterThan(0);
  });

  it('triggers manual job run on button click', async () => {
    render(<SchedulerDashboard />);

    const runButtons = await screen.findAllByText('Run Now');
    fireEvent.click(runButtons[0]);

    expect(
      await screen.findByText('Started task: "Daily Portfolio Valuation Snapshot"')
    ).toBeInTheDocument();
    expect(mockedApi.triggerJobNow).toHaveBeenCalledWith('daily_portfolio_snapshot');
  });

  it('pauses job on pause button click', async () => {
    render(<SchedulerDashboard />);

    const pauseButtons = await screen.findAllByText('Pause');
    fireEvent.click(pauseButtons[0]);

    expect(
      await screen.findByText('Paused task: "Daily Portfolio Valuation Snapshot"')
    ).toBeInTheDocument();
    expect(mockedApi.pauseScheduledJob).toHaveBeenCalledWith('daily_portfolio_snapshot');
  });

  it('opens activity history modal on click', async () => {
    render(<SchedulerDashboard />);

    const logsButton = await screen.findByText('Activity History');
    fireEvent.click(logsButton);

    expect(await screen.findByText('Task Activity History')).toBeInTheDocument();
    expect(mockedApi.getScheduledJobLogs).toHaveBeenCalled();
    expect(screen.getByText('Duration: 2.15s')).toBeInTheDocument();
  });
});
