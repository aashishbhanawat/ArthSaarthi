import React, { useState } from 'react';
import { useUsers, useDeleteUser } from '../../hooks/useUsers';
import UsersTable from '../../components/Admin/UsersTable'; // Corrected path
import UserFormModal from '../../components/Admin/UserFormModal'; // Corrected path
import { DeleteConfirmationModal } from '../../components/common/DeleteConfirmationModal';
import { User } from '../../types/user';

const UserManagementPage: React.FC = () => {
  const { data: users, isLoading, isError, error } = useUsers();
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
      deleteUserMutation.mutate(selectedUser.id, {
        onSuccess: () => {
          setDeleteModalOpen(false);
          setSelectedUser(null);
        },
      });
    }
  };

  if (isLoading) return <div className="text-center p-8">Loading users...</div>;
  if (isError) return <div className="text-center p-8 text-red-500">Error: {error.message}</div>;

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">User Management</h1>
        <button onClick={handleCreateUser} className="btn btn-primary">Create New User</button>
      </div>

      <UsersTable
        users={users || []}
        onEdit={handleEditUser}
        onDelete={handleDeleteUser}
      />

      {isFormModalOpen && (
        <UserFormModal
          isOpen={isFormModalOpen}
          onClose={() => setFormModalOpen(false)}
          userToEdit={selectedUser}
        />
      )}

      {isDeleteModalOpen && selectedUser && (
        <DeleteConfirmationModal
          isOpen={isDeleteModalOpen}
          onClose={() => setDeleteModalOpen(false)}
          onConfirm={confirmDelete}
          title="Delete User"
          message={
            <p>
              Are you sure you want to delete the user <strong>{selectedUser.email}</strong>?
            </p>
          }
          isDeleting={deleteUserMutation.isPending}
        />
      )}
    </div>
  );
};

export default UserManagementPage;