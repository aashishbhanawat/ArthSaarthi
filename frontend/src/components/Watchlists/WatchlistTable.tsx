import React from 'react';
import { Table, Button } from 'flowbite-react';
import { Watchlist } from '../../types/watchlist';
import { XMarkIcon } from '@heroicons/react/24/solid';
import { formatCurrency, formatPercentage } from '../../utils/formatting';

interface WatchlistTableProps {
  watchlist: Watchlist | undefined;
  onRemoveItem: (itemId: string) => void;
}

const WatchlistTable: React.FC<WatchlistTableProps> = ({ watchlist, onRemoveItem }) => {
  if (!watchlist) {
    return <div className="text-center p-4">Select a watchlist to view its assets.</div>;
  }

  if (watchlist.items.length === 0) {
    return <div className="text-center p-4">This watchlist is empty.</div>;
  }

  return (
    <div className="overflow-x-auto">
      <Table hoverable>
        <Table.Head>
          <Table.HeadCell>Symbol</Table.HeadCell>
          <Table.HeadCell>Name</Table.HeadCell>
          <Table.HeadCell>Price</Table.HeadCell>
          <Table.HeadCell>Change</Table.HeadCell>
          <Table.HeadCell>% Change</Table.HeadCell>
          <Table.HeadCell>Market Cap</Table.HeadCell>
          <Table.HeadCell></Table.HeadCell>
        </Table.Head>
        <Table.Body className="divide-y">
          {watchlist.items.map((item) => (
            <Table.Row key={item.id} className="bg-white dark:border-gray-700 dark:bg-gray-800">
              <Table.Cell className="font-medium text-gray-900 dark:text-white">
                {item.asset.symbol}
              </Table.Cell>
              <Table.Cell>{item.asset.name}</Table.Cell>
              <Table.Cell>{formatCurrency(item.asset.current_price)}</Table.Cell>
              <Table.Cell
                className={
                  item.asset.price_change_24h && item.asset.price_change_24h < 0
                    ? 'text-red-600'
                    : 'text-green-600'
                }
              >
                {formatCurrency(item.asset.price_change_24h)}
              </Table.Cell>
              <Table.Cell
                className={
                  item.asset.price_change_percentage_24h && item.asset.price_change_percentage_24h < 0
                    ? 'text-red-600'
                    : 'text-green-600'
                }
              >
                {formatPercentage(item.asset.price_change_percentage_24h / 100)}
              </Table.Cell>
              <Table.Cell>{formatCurrency(item.asset.market_cap)}</Table.Cell>
              <Table.Cell>
                <Button size="xs" color="failure" onClick={() => onRemoveItem(item.id)}>
                  <XMarkIcon className="h-4 w-4" />
                </Button>
              </Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table>
    </div>
  );
};

export default WatchlistTable;
