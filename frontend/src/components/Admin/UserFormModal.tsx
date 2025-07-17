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

  const isEditing = userToEdit !== null;

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
        // Note: Password update is not part of this form for security/simplicity.
        // It would typically be a separate "reset password" flow.
        await updateUserMutation.mutateAsync({
          userId: userToEdit.id,
          userData: updateData,
        });
      } else {
        await createUserMutation.mutateAsync({
          full_name: fullName,
          email,
          password,
        });
      }
      onClose();
    } catch (error: any) {
      const errorDetail = error.response?.data?.detail;
      let displayMessage = "An unexpected error occurred.";

      if (typeof errorDetail === 'string') {
        displayMessage = errorDetail;
      } else if (Array.isArray(errorDetail) && errorDetail.length > 0 && typeof errorDetail[0].msg === 'string') {
        displayMessage = errorDetail.map(e => e.msg).join(', ');
      } else {
        // Handle other potential object structures or fall back
        displayMessage = errorDetail?.msg || displayMessage;
      }
      setError(displayMessage);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-backdrop">
      <div className="modal-content">
        <h2>{isEditing ? 'Edit User' : 'Create New User'}</h2>
        {error && <p style={{ color: 'red' }}>{error}</p>}
        <form onSubmit={handleSubmit}>
          <div>
            <label htmlFor="fullName">Full Name</label>
            <input
              id="fullName"
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          {!isEditing && (
            <div>
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required={!isEditing}
              />
            </div>
          )}
           {isEditing && (
            <>
              <div>
                <label htmlFor="isActive">
                  <input id="isActive" type="checkbox" checked={isActive} onChange={(e) => setIsActive(e.target.checked)} />
                  Active
                </label>
              </div>
              <div>
                <label htmlFor="isAdmin">
                  <input id="isAdmin" type="checkbox" checked={isAdmin} onChange={(e) => setIsAdmin(e.target.checked)} />
                  Administrator
                </label>
              </div>
            </>
          )}
          <div className="modal-actions">
            <button type="button" onClick={onClose} className="button-secondary">
              Cancel
            </button>
            <button type="submit" disabled={createUserMutation.isPending || updateUserMutation.isPending}>
              {isEditing ? 'Save Changes' : 'Create User'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default UserFormModal;