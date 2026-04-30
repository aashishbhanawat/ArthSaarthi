import React from 'react';
import { User } from '../../types/user';
import { PencilSquareIcon, TrashIcon } from '@heroicons/react/24/outline';

interface UserCardProps {
    user: User;
    onEdit: (user: User) => void;
    onDelete: (user: User) => void;
}

const UserCard: React.FC<UserCardProps> = ({ user, onEdit, onDelete }) => {
    return (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4 mb-3 transition-all hover:shadow-md">
            <div className="flex justify-between items-start">
                <div className="flex flex-col max-w-[65%]">
                    <span className="text-sm font-bold text-gray-900 dark:text-gray-100 truncate">{user.email}</span>
                    <div className="mt-1">
                        <span className={`px-2 inline-flex text-[10px] leading-5 font-semibold rounded-full ${user.is_admin ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300' : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'}`}>
                            {user.is_admin ? 'Admin' : 'User'}
                        </span>
                    </div>
                </div>
                <div className="flex items-center gap-4">
                    <button 
                        type="button" 
                        onClick={() => onEdit(user)} 
                        className="text-gray-500 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                        aria-label={`Edit user ${user.email}`}
                        title="Edit User"
                    >
                        <PencilSquareIcon className="h-5 w-5" />
                    </button>
                    <button 
                        type="button" 
                        onClick={() => onDelete(user)} 
                        className="text-gray-500 hover:text-red-600 dark:hover:text-red-400 transition-colors"
                        aria-label={`Delete user ${user.email}`}
                        title="Delete User"
                    >
                        <TrashIcon className="h-5 w-5" />
                    </button>
                </div>
            </div>
        </div>
    );
};

export default UserCard;
