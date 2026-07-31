import UpdateProfileForm from '../components/Profile/UpdateProfileForm';
import ChangePasswordForm from '../components/Profile/ChangePasswordForm';
import BackupRestoreCard from '../components/Profile/BackupRestoreCard';
import AndroidSettingsCard from '../components/Profile/AndroidSettingsCard';

const ProfilePage = () => {
  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold">Profile & Settings</h1>
      <div className="max-w-2xl mx-auto space-y-8">
        <UpdateProfileForm />
        <ChangePasswordForm />
        <BackupRestoreCard />
        <AndroidSettingsCard />
      </div>
    </div>
  );
};

export default ProfilePage;
