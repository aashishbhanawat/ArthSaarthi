import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useUsers, useDeleteUser } from '../../hooks/useUsers';
import UsersTable from '../../components/Admin/UsersTable'; // Corrected path
import UserFormModal from '../../components/Admin/UserFormModal'; // Corrected path
import DeleteConfirmationModal from '../../components/Admin/DeleteConfirmationModal';
import { User } from '../../types/user';

const UserManagementPage: React.FC = () => {
  const { data: users, isLoading, error } = useUsers();
  const deleteUserMutation = useDeleteUser();

  const [isFormModalOpen, setFormModalOpen] = useState(false);
  const [isDeleteModalOpen, setDeleteModalOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);

  const handleCreateUser = () => {
    setSelectedUser(null);
    setFormModalOpen(true);
  };

  const handleEditUser = (user: User) => {
    setSelectedUser(user);
    setFormModalOpen(true);
  };

  const handleDeleteUser = (user: User) => {
    setSelectedUser(user);
    setDeleteModalOpen(true);
  };

  const confirmDelete = () => {
    if (selectedUser) {
      deleteUserMutation.mutate(selectedUser.id);
      setDeleteModalOpen(false);
      setSelectedUser(null);
    }
  };

  if (isLoading) return <div>Loading users...</div>;
  if (error) return <div>An error occurred: {error.message}</div>;

  return (
    <div className="page-container" id="UserManagementPage">
      <h1>User Management</h1>
      <button onClick={handleCreateUser}>Create New User</button>

      <UsersTable
        users={users || []}
        onEdit={handleEditUser}
        onDelete={handleDeleteUser}
      />

      <UserFormModal
        isOpen={isFormModalOpen}
        onClose={() => setFormModalOpen(false)}
        userToEdit={selectedUser}
      />

      <DeleteConfirmationModal
        isOpen={isDeleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        onConfirm={confirmDelete}
        user={selectedUser}
      />
    </div>
  );
};

export default UserManagementPage;