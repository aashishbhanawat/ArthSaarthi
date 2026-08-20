import re

with open('frontend/src/components/Watchlists/WatchlistEmptyState.tsx', 'r') as f:
    content = f.read()

new_content = content.replace("export const WatchlistEmptyState: React.FC = () => {", "import { PlusIcon } from '@heroicons/react/24/outline';\n\ninterface WatchlistEmptyStateProps {\n  onCreateClick?: () => void;\n}\n\nexport const WatchlistEmptyState: React.FC<WatchlistEmptyStateProps> = ({ onCreateClick }) => {")
new_content = new_content.replace("<EyeIcon className=\"mx-auto h-12 w-12 text-gray-400\" />", "<EyeIcon className=\"mx-auto h-12 w-12 text-gray-400\" aria-hidden=\"true\" />")
new_content = new_content.replace("</p>\n    </div>", "</p>\n      {onCreateClick && (\n        <div className=\"mt-6 flex justify-center\">\n          <button\n            type=\"button\"\n            onClick={onCreateClick}\n            className=\"btn btn-primary inline-flex items-center gap-2\"\n          >\n            <PlusIcon className=\"h-5 w-5\" aria-hidden=\"true\" />\n            Create Watchlist\n          </button>\n        </div>\n      )}\n    </div>")

with open('frontend/src/components/Watchlists/WatchlistEmptyState.tsx', 'w') as f:
    f.write(new_content)
