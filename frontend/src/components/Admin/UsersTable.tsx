import React from 'react';
import { User } from '../../types/user';

interface UsersTableProps {
  users: User[];
  onEdit: (user: User) => void;
  onDelete: (user: User) => void;
}

const UsersTable: React.FC<UsersTableProps> = ({ users, onEdit, onDelete }) => {
  return (
    <table>
      <thead>
        <tr>
          <th>Full Name</th>
          <th>Email</th>
          <th>Active</th>
          <th>Admin</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {users.map((user) => (
          <tr key={user.id}>
            <td>{user.full_name || 'N/A'}</td>
            <td>{user.email}</td>
            <td>{user.is_active ? 'Yes' : 'No'}</td>
            <td>{user.is_admin ? 'Yes' : 'No'}</td>
            <td>
              <button onClick={() => onEdit(user)}>Edit</button>
              <button onClick={() => onDelete(user)} className="button-danger">
                Delete
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};

export default UsersTable;