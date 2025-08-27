import React from 'react';
import UpdateProfileForm from '../components/Profile/UpdateProfileForm';
import ChangePasswordForm from '../components/Profile/ChangePasswordForm';

const ProfilePage: React.FC = () => {
  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold">Profile Settings</h1>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
        <UpdateProfileForm />
        <ChangePasswordForm />
      </div>
    </div>
  );
};

export default ProfilePage;
