import React from 'react';
import { useNavigate } from 'react-router-dom';
import { XMarkIcon } from '@heroicons/react/24/outline';

const UserGuidePage: React.FC = () => {
    const navigate = useNavigate();

    return (
        <div className="flex flex-col h-full bg-white dark:bg-gray-900">
            <header className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center gap-4 sticky top-0 bg-white dark:bg-gray-900 z-10">
                <button
                    onClick={() => navigate(-1)}
                    className="p-2 -ml-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                    aria-label="Back"
                >
                    <XMarkIcon className="h-6 w-6 text-gray-800 dark:text-gray-200" />
                </button>
                <h1 className="text-xl font-bold text-gray-900 dark:text-white">User Guide</h1>
            </header>

            <div className="flex-1 overflow-hidden relative">
                <iframe
                    src="/user_guide/index.html"
                    title="User Guide"
                    className="w-full h-full border-none"
                    onLoad={(e) => {
                        // Optional: Inject some CSS into the iframe to make it look better in the app
                        try {
                            const iframe = e.target as HTMLIFrameElement;
                            if (iframe.contentDocument) {
                                const style = iframe.contentDocument.createElement('style');
                                style.textContent = `
                                    body { padding-bottom: 80px; }
                                    .navbar { display: none !important; }
                                `;
                                iframe.contentDocument.head.appendChild(style);
                            }
                        } catch (err) {
                            console.warn("Could not inject styles into user guide iframe", err);
                        }
                    }}
                />
            </div>
        </div>
    );
};

export default UserGuidePage;
