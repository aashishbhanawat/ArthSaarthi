import React from 'react';
import UpdateProfileForm from '../components/Profile/UpdateProfileForm';
import ChangePasswordForm from '../components/Profile/ChangePasswordForm';

const ProfilePage: React.FC = () => {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold">User Profile</h1>
      </div>
      <UpdateProfileForm />
      <ChangePasswordForm />
    </div>
  );
};

export default ProfilePage;
