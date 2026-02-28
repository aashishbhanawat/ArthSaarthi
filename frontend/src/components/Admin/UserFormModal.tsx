import React, { useState, useEffect } from 'react';
import { User, UserUpdate } from '../../types/user';
import { useCreateUser, useUpdateUser } from '../../hooks/useUsers';

interface UserFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  userToEdit: User | null;
}

const UserFormModal: React.FC<UserFormModalProps> = ({
  isOpen,
  onClose,
  userToEdit,
}) => {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isActive, setIsActive] = useState(true);
  const [isAdmin, setIsAdmin] = useState(false);
  const [error, setError] = useState('');

  const createUserMutation = useCreateUser();
  const updateUserMutation = useUpdateUser();

  const isEditing = !!userToEdit;
  const { isPending } = isEditing ? updateUserMutation : createUserMutation;

  useEffect(() => {
    if (isEditing) {
      setFullName(userToEdit.full_name || '');
      setEmail(userToEdit.email);
      setIsActive(userToEdit.is_active);
      setIsAdmin(userToEdit.is_admin);
      setPassword(''); // Don't show existing password
    } else {
      // Reset form for creation
      setFullName('');
      setEmail('');
      setPassword('');
      setIsActive(true);
      setIsAdmin(false);
    }
    setError('');
  }, [isOpen, userToEdit, isEditing]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      if (isEditing) {
        const updateData: UserUpdate = {
          full_name: fullName,
          email,
          is_active: isActive,
          is_admin: isAdmin,
        };
        if (password) {
          updateData.password = password;
        }
        await updateUserMutation.mutateAsync({
          userId: userToEdit.id,
          userData: updateData,
        });
      } else {
        await createUserMutation.mutateAsync({
          full_name: fullName,
          email,
          password,
          is_admin: isAdmin, // Assuming new users can be created as admins
        });
      }
      onClose();
    } catch (e: unknown) {
      const error = e as { response?: { data?: { detail?: string | { msg: string }[] } } };
      const errorDetail = error.response?.data?.detail;
      let displayMessage = "An unexpected error occurred.";

      if (typeof errorDetail === 'string') {
        displayMessage = errorDetail;
      } else if (Array.isArray(errorDetail)) {
        displayMessage = errorDetail.map(e => e.msg).join(', ');
      }
      setError(displayMessage);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div role="dialog" aria-modal="true" aria-labelledby="user-form-modal-title" className="modal-content max-w-md">
        <div className="modal-header">
          <h2 id="user-form-modal-title" className="text-2xl font-bold">{isEditing ? 'Edit User' : 'Create New User'}</h2>
          <button onClick={onClose} aria-label="Close" className="text-gray-400 hover:text-gray-600">&times;</button>
        </div>
        <div className="p-6">
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="fullName" className="form-label">Full Name</label>
              <input id="fullName" type="text" value={fullName} onChange={(e) => setFullName(e.target.value)} className="form-input" disabled={isPending} />
            </div>
            <div className="form-group">
              <label htmlFor="email" className="form-label">Email</label>
              <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="form-input" required disabled={isPending} />
            </div>
            <div className="form-group">
              <label htmlFor="password" className="form-label">
                Password {isEditing && <span className="text-xs text-gray-500">(leave blank to keep current)</span>}
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="form-input"
                required={!isEditing}
                disabled={isPending}
              />
            </div>
            <div className="form-group grid grid-cols-2 gap-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={isActive}
                  onChange={(e) => setIsActive(e.target.checked)}
                  className="mr-2"
                  disabled={isPending || !isEditing}
                />
                <span className="form-label mb-0">Active</span>
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={isAdmin}
                  onChange={(e) => setIsAdmin(e.target.checked)}
                  className="mr-2"
                  disabled={isPending}
                />
                <span className="form-label mb-0">Administrator</span>
              </label>
            </div>

            {error && (
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
                <span className="block sm:inline">{error}</span>
              </div>
            )}

            <div className="flex items-center justify-end pt-4">
              <button type="button" onClick={onClose} className="btn btn-secondary mr-2" disabled={isPending}>
                Cancel
              </button>
              <button type="submit" className="btn btn-primary" disabled={isPending}>
                {isPending ? 'Saving...' : (isEditing ? 'Save Changes' : 'Create User')}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default UserFormModal;