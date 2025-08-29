import React from 'react';
import UpdateProfileForm from '../components/Profile/UpdateProfileForm';
import ChangePasswordForm from '../components/Profile/ChangePasswordForm';
import HelpLink from '../components/HelpLink';

const ProfilePage: React.FC = () => {
  return (
    <div className="space-y-8">
      <div className="flex items-center">
        <h1 className="text-3xl font-bold">Profile Settings</h1>
        <HelpLink sectionId="profile-settings" />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
        <UpdateProfileForm />
        <ChangePasswordForm />
      </div>
    </div>
  );
};

export default ProfilePage;
