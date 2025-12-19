import { QuestionMarkCircleIcon } from '@heroicons/react/24/solid';

interface HelpLinkProps {
  sectionId: string;
  className?: string;
}

const HelpLink = ({ sectionId, className = 'h-5 w-5 text-gray-400 hover:text-gray-600' }: HelpLinkProps) => {
  const handleClick = (e: React.MouseEvent) => {
    // Check if running in Electron
    if (window.electronAPI?.openUserGuide) {
      e.preventDefault();
      window.electronAPI.openUserGuide(sectionId);
    }
    // In web mode, the href will work normally
  };

  return (
    <a
      href={`/user_guide/index.html#${sectionId}`}
      target="_blank"
      rel="noopener noreferrer"
      aria-label={`Help for this section`}
      className="ml-2"
      onClick={handleClick}
    >
      <QuestionMarkCircleIcon className={className} />
    </a>
  );
};

export default HelpLink;