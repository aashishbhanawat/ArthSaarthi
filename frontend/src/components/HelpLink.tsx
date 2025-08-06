import { QuestionMarkCircleIcon } from '@heroicons/react/24/solid';

interface HelpLinkProps {
  sectionId: string;
  className?: string;
}

const HelpLink = ({ sectionId, className = 'h-5 w-5 text-gray-400 hover:text-gray-600' }: HelpLinkProps) => {
  return (
    <a
      href={`/user_guide.md#${sectionId}`}
      target="_blank"
      rel="noopener noreferrer"
      aria-label={`Help for this section`}
      className="ml-2"
    >
      <QuestionMarkCircleIcon className={className} />
    </a>
  );
};

export default HelpLink;