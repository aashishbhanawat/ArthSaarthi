import React from 'react';
import UpdateProfileForm from '../components/Profile/UpdateProfileForm';
import ChangePasswordForm from '../components/Profile/ChangePasswordForm';

const ProfilePage = () => {
  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold">User Profile</h1>
      <div className="max-w-2xl mx-auto">
        <UpdateProfileForm />
        <ChangePasswordForm />
      </div>
    </div>
  );
};

export default ProfilePage;
