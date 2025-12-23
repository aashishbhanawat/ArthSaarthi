import React from 'react';
import { User } from '../../types/user';

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
              <td className="text-right py-3 px-4 space-x-2">
                <button onClick={() => onEdit(user)} className="btn btn-secondary text-sm py-1 px-3">Edit</button>
                <button onClick={() => onDelete(user)} className="btn btn-danger text-sm py-1 px-3">Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default UsersTable;