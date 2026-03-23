import React from 'react';
import { User } from '../../types/user';
import { PencilSquareIcon, TrashIcon } from '@heroicons/react/24/outline';

interface UsersTableProps {
  users: User[];
  onEdit: (user: User) => void;
  onDelete: (user: User) => void;
}

const UsersTable: React.FC<UsersTableProps> = ({ users, onEdit, onDelete }) => {
  return (
    <div className="card overflow-x-auto">
      <table className="min-w-full bg-white dark:bg-gray-800">
        <thead className="bg-gray-200 dark:bg-gray-700">
          <tr>
            <th className="text-left py-3 px-4 uppercase font-semibold text-sm dark:text-gray-300">Email</th>
            <th className="text-left py-3 px-4 uppercase font-semibold text-sm dark:text-gray-300">Role</th>
            <th className="text-right py-3 px-4 uppercase font-semibold text-sm dark:text-gray-300">Actions</th>
          </tr>
        </thead>
        <tbody className="text-gray-700 dark:text-gray-300">
          {users.map((user) => (
            <tr key={user.id} className="border-b dark:border-gray-700 odd:bg-gray-50 dark:odd:bg-gray-700/50">
              <td className="text-left py-3 px-4">{user.email}</td>
              <td className="text-left py-3 px-4">
                <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${user.is_admin ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300' : 'bg-gray-100 text-gray-800 dark:bg-gray-600 dark:text-gray-300'}`}>
                  {user.is_admin ? 'Admin' : 'User'}
                </span>
              </td>
              <td className="text-right py-3 px-4">
                <div className="flex justify-end items-center space-x-4">
                  <button onClick={() => onEdit(user)} className="text-gray-500 hover:text-blue-600 dark:hover:text-blue-400 transition-colors" aria-label={`Edit user ${user.email}`} title="Edit User">
                    <PencilSquareIcon className="h-5 w-5" />
                  </button>
                  <button onClick={() => onDelete(user)} className="text-gray-500 hover:text-red-600 dark:hover:text-red-400 transition-colors" aria-label={`Delete user ${user.email}`} title="Delete User">
                    <TrashIcon className="h-5 w-5" />
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default UsersTable;