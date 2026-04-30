import { useNavigate } from 'react-router-dom';
import { QuestionMarkCircleIcon } from '@heroicons/react/24/solid';

interface HelpLinkProps {
  sectionId: string;
  className?: string;
}

const HelpLink = ({ sectionId, className = 'h-5 w-5 text-gray-400 hover:text-gray-600' }: HelpLinkProps) => {
  const navigate = useNavigate();

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    // Navigate to local help page instead of opening new window
    navigate(`/help#${sectionId}`);
  };

  return (
    <button
      onClick={handleClick}
      aria-label={`Help for this section`}
      className="ml-2 focus:outline-none"
    >
      <QuestionMarkCircleIcon className={className} />
    </button>
  );
};

export default HelpLink;