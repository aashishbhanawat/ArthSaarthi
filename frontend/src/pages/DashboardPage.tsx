import React from "react";
import { usePortfolios } from '../hooks/usePortfolios';
import { Portfolio } from '../types/portfolio';


// NOTE: This is a simplified calculation for the MVP dashboard.
// A real-world calculation would need to handle cost basis more granularly,
// and use real-time market prices for current value.
const calculatePortfolioMetrics = (portfolios: Portfolio[]) => {
    let totalInvested = 0;
    let totalProceedsFromSales = 0;
    // asset.id -> { quantity: number, totalCost: number }
    const holdings = new Map<number, { quantity: number, totalCost: number }>();

    // Get all transactions from all portfolios and sort them by date to process chronologically
    const allTransactions = portfolios.flatMap(p => p.transactions)
        .sort((a, b) => new Date(a.transaction_date).getTime() - new Date(b.transaction_date).getTime());

    allTransactions.forEach(tx => {
        const quantity = parseFloat(tx.quantity);
        const price = parseFloat(tx.price_per_unit);
        const fees = parseFloat(tx.fees) || 0;
        const transactionValue = quantity * price;

        if (tx.transaction_type === 'BUY') {
            totalInvested += transactionValue + fees;
            const currentHolding = holdings.get(tx.asset.id) || { quantity: 0, totalCost: 0 };
            currentHolding.quantity += quantity;
            currentHolding.totalCost += transactionValue; // Cost basis is just the purchase price, excluding fees for this model
            holdings.set(tx.asset.id, currentHolding);
        } else { // SELL
            totalProceedsFromSales += transactionValue - fees;
            const currentHolding = holdings.get(tx.asset.id);
            if (currentHolding && currentHolding.quantity > 0) {
                // Reduce the cost basis proportionally to the quantity sold
                const proportionSold = quantity / currentHolding.quantity;
                currentHolding.totalCost *= (1 - proportionSold);
                currentHolding.quantity -= quantity;
            }
        }
    });

    // For MVP, current value is the remaining cost basis of current holdings.
    const currentHoldingsValue = Array.from(holdings.values()).reduce((acc, holding) => acc + holding.totalCost, 0);

    const profitLoss = (currentHoldingsValue + totalProceedsFromSales) - totalInvested;
    const profitLossPercentage = totalInvested > 0 ? (profitLoss / totalInvested) * 100 : 0;

    return {
        totalValue: currentHoldingsValue,
        profitLoss,
        profitLossPercentage,
    };
};

const DashboardPage: React.FC = () => {
    const { data: portfolios, isLoading, isError, error } = usePortfolios();

    if (isLoading) {
        return <div className="text-center p-8">Loading dashboard data...</div>;
    }

    if (isError) {
        return <div className="text-center p-8 text-red-500">Error loading dashboard: {error.message}</div>;
    }

    const metrics = portfolios ? calculatePortfolioMetrics(portfolios) : { totalValue: 0, profitLoss: 0, profitLossPercentage: 0 };

    return (
        <div>
            <h1 className="text-3xl font-bold mb-8">Dashboard</h1>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 text-center">
                <div className="card">
                    <h3 className="text-lg font-semibold text-gray-500 mb-2">Total Portfolio Value</h3>
                    <p className="text-4xl font-bold text-gray-800">${metrics.totalValue.toFixed(2)}</p>
                </div>
                <div className="card">
                    <h3 className="text-lg font-semibold text-gray-500 mb-2">Overall Profit / Loss</h3>
                    <p className={`text-4xl font-bold ${metrics.profitLoss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {metrics.profitLoss >= 0 ? '+' : '-'}${Math.abs(metrics.profitLoss).toFixed(2)}
                    </p>
                </div>
                <div className="card">
                    <h3 className="text-lg font-semibold text-gray-500 mb-2">Overall Return %</h3>
                     <p className={`text-4xl font-bold ${metrics.profitLossPercentage >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {metrics.profitLossPercentage.toFixed(2)}%
                    </p>
                </div>
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="card">
                    <h3 className="text-xl font-semibold mb-4">Asset Allocation</h3>
                    <div className="flex items-center justify-center h-64 bg-gray-100 rounded-md text-gray-400">
                        <p>Chart component will be rendered here.</p>
                    </div>
                </div>
                <div className="card">
                    <h3 className="text-xl font-semibold mb-4">Portfolio History</h3>
                    <div className="flex items-center justify-center h-64 bg-gray-100 rounded-md text-gray-400">
                        <p>Chart component will be rendered here.</p>
                    </div>
                </div>
            </div>
        </div>
    );    
};

export default DashboardPage;