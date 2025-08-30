import React from 'react';
import UpdateProfileForm from '../components/Profile/UpdateProfileForm';
import ChangePasswordForm from '../components/Profile/ChangePasswordForm';
import HelpLink from '../components/HelpLink';

const ProfilePage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center">
        <h1 className="text-3xl font-bold">Profile &amp; Settings</h1>
        <HelpLink sectionId="profile-settings" />
      </div>
      <div className="p-4 sm:p-8 bg-base-200 rounded-box">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
            <UpdateProfileForm />
            <ChangePasswordForm />
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
