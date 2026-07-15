import React, { useState, useEffect } from 'react';
import { UserRiskProfileCreate } from '../../types/risk';

interface RiskQuestionnaireWizardProps {
    onSubmit: (profile: UserRiskProfileCreate) => void;
    isSubmitting: boolean;
}

interface Question {
    id: string;
    text: string;
    options: {
        value: string;
        text: string;
        points: number;
    }[];
}

const QUESTIONS: Question[] = [
    {
        id: 'q1',
        text: 'In general, how would your best friend describe you as a risk taker?',
        options: [
            { value: 'A', text: 'A real gambler', points: 4 },
            { value: 'B', text: 'Willing to take risks after completing adequate research', points: 3 },
            { value: 'C', text: 'Cautious', points: 2 },
            { value: 'D', text: 'A real risk avoider', points: 1 },
        ],
    },
    {
        id: 'q2',
        text: 'You are on a TV game show and can choose one of the following. Which would you take?',
        options: [
            { value: 'A', text: '₹1,00,000 in cash', points: 1 },
            { value: 'B', text: 'A 50% chance at winning ₹5,00,000', points: 2 },
            { value: 'C', text: 'A 25% chance at winning ₹10,00,000', points: 3 },
            { value: 'D', text: 'A 5% chance at winning ₹1,00,00,000', points: 4 },
        ],
    },
    {
        id: 'q3',
        text: 'You have just finished saving for a "once-in-a-lifetime" vacation. Three weeks before you plan to leave, you lose your job. You would:',
        options: [
            { value: 'A', text: 'Cancel the vacation', points: 1 },
            { value: 'B', text: 'Take a much more modest vacation', points: 2 },
            { value: 'C', text: 'Go as scheduled, reasoning that you need the time to prepare for a job search', points: 3 },
            { value: 'D', text: 'Extend your vacation, because this might be your last chance to go first-class', points: 4 },
        ],
    },
    {
        id: 'q4',
        text: 'If you unexpectedly received ₹10,00,000 to invest, what would you do?',
        options: [
            { value: 'A', text: 'Deposit it in a bank account, money market account, or an insured CD', points: 1 },
            { value: 'B', text: 'Invest it in safe high quality bonds or bond mutual funds', points: 2 },
            { value: 'C', text: 'Invest it in stocks or stock mutual funds', points: 3 },
        ],
    },
    {
        id: 'q5',
        text: 'In terms of experience, how comfortable are you investing in stocks or stock mutual funds?',
        options: [
            { value: 'A', text: 'Not at all comfortable', points: 1 },
            { value: 'B', text: 'Somewhat comfortable', points: 2 },
            { value: 'C', text: 'Very comfortable', points: 3 },
        ],
    },
    {
        id: 'q6',
        text: 'When you think of the word "risk" which of the following words comes to mind first?',
        options: [
            { value: 'A', text: 'Loss', points: 1 },
            { value: 'B', text: 'Uncertainty', points: 2 },
            { value: 'C', text: 'Opportunity', points: 3 },
            { value: 'D', text: 'Thrill', points: 4 },
        ],
    },
    {
        id: 'q7',
        text: 'Some experts are predicting prices of assets such as gold, jewels, collectibles, and real estate (hard assets) to increase in value; bond prices may fall, however, experts tend to agree that government bonds are relatively safe. Most of your investment assets are now in high-interest government bonds. What would you do?',
        options: [
            { value: 'A', text: 'Hold the bonds', points: 1 },
            { value: 'B', text: 'Sell the bonds, put half the proceeds into money market accounts, and the other half into hard assets', points: 2 },
            { value: 'C', text: 'Sell the bonds and put the total proceeds into hard assets', points: 3 },
            { value: 'D', text: 'Sell the bonds, put all the money into hard assets, and borrow additional money to buy more', points: 4 },
        ],
    },
    {
        id: 'q8',
        text: 'Given the best- and worst-case returns of the four investment choices below, which would you prefer?',
        options: [
            { value: 'A', text: '₹10,000 gain best case; ₹0 gain/loss worst case', points: 1 },
            { value: 'B', text: '₹40,000 gain best case; ₹10,000 loss worst case', points: 2 },
            { value: 'C', text: '₹1,30,000 gain best case; ₹40,000 loss worst case', points: 3 },
            { value: 'D', text: '₹2,40,000 gain best case; ₹1,20,000 loss worst case', points: 4 },
        ],
    },
    {
        id: 'q9',
        text: 'In addition to whatever you own, you have been given ₹50,000. You are now asked to choose between:',
        options: [
            { value: 'A', text: 'A sure gain of ₹25,000', points: 1 },
            { value: 'B', text: 'A 50% chance to gain ₹50,000 and a 50% chance to gain nothing', points: 3 },
        ],
    },
    {
        id: 'q10',
        text: 'In addition to whatever you own, you have been given ₹1,00,000. You are now asked to choose between:',
        options: [
            { value: 'A', text: 'A sure loss of ₹25,000', points: 1 },
            { value: 'B', text: 'A 50% chance to lose ₹50,000 and a 50% chance to lose nothing', points: 3 },
        ],
    },
    {
        id: 'q11',
        text: 'Suppose a relative left you an inheritance of ₹50,00,000, stipulating in the will that you invest ALL the money in ONE of the following choices. Which one would you select?',
        options: [
            { value: 'A', text: 'A savings account or money market mutual fund', points: 1 },
            { value: 'B', text: 'A mutual fund that owns stocks and bonds', points: 2 },
            { value: 'C', text: 'A portfolio of 15 common stocks', points: 3 },
            { value: 'D', text: 'Commodities like gold, silver, and oil', points: 4 },
        ],
    },
    {
        id: 'q12',
        text: 'If you had to invest ₹10,00,000, which of the following investment choices would you find most appealing?',
        options: [
            { value: 'A', text: '60% in low-risk investments, 30% in medium-risk investments, 10% in high-risk investments', points: 1 },
            { value: 'B', text: '30% in low-risk investments, 40% in medium-risk investments, 30% in high-risk investments', points: 2 },
            { value: 'C', text: '10% in low-risk investments, 40% in medium-risk investments, 50% in high-risk investments', points: 3 },
        ],
    },
    {
        id: 'q13',
        text: 'Your trusted friend and neighbor, an experienced geologist, is putting together a group of investors to fund an exploratory gold mining venture. The venture could pay back 50 to 100 times the investment if successful. If the mine is a bust, the entire investment is worthless. Your friend estimates the chance of success is only 20%. If you had the money, how much would you invest?',
        options: [
            { value: 'A', text: 'Nothing', points: 1 },
            { value: 'B', text: 'One month\'s salary', points: 2 },
            { value: 'C', text: 'Three month\'s salary', points: 3 },
            { value: 'D', text: 'Six month\'s salary', points: 4 },
        ],
    },
];

const RiskQuestionnaireWizard: React.FC<RiskQuestionnaireWizardProps> = ({ onSubmit, isSubmitting }) => {
    const [currentStep, setCurrentStep] = useState<number>(() => {
        const saved = localStorage.getItem('risk_wizard_step');
        return saved ? parseInt(saved, 10) : 0;
    });
    const [answers, setAnswers] = useState<Record<string, string>>(() => {
        const saved = localStorage.getItem('risk_wizard_answers');
        return saved ? JSON.parse(saved) : {};
    });

    useEffect(() => {
        localStorage.setItem('risk_wizard_step', currentStep.toString());
    }, [currentStep]);

    useEffect(() => {
        localStorage.setItem('risk_wizard_answers', JSON.stringify(answers));
    }, [answers]);

    const handleSelectOption = (value: string) => {
        const questionId = QUESTIONS[currentStep].id;
        setAnswers((prev) => ({ ...prev, [questionId]: value }));
    };

    const handleNext = () => {
        if (currentStep < QUESTIONS.length - 1) {
            setCurrentStep((prev) => prev + 1);
        } else {
            onSubmit({ answers });
        }
    };

    const handleBack = () => {
        if (currentStep > 0) {
            setCurrentStep((prev) => prev - 1);
        }
    };

    const activeQuestion = QUESTIONS[currentStep];
    const progressPercent = (currentStep / QUESTIONS.length) * 100;
    const currentAnswer = answers[activeQuestion.id];

    return (
        <div className="max-w-2xl mx-auto mt-8">
            <div className="card shadow-md">
                {/* Header */}
                <div className="flex justify-between items-center mb-4">
                    <span className="text-sm font-semibold text-gray-500 dark:text-gray-400">
                        Step {currentStep + 1} of {QUESTIONS.length}
                    </span>
                    <span className="text-sm font-semibold text-blue-600 dark:text-blue-400">
                        {Math.round(progressPercent)}% Complete
                    </span>
                </div>

                {/* Progress Bar */}
                <div className="w-full bg-gray-200 dark:bg-gray-700 h-2.5 rounded-full mb-8">
                    <div
                        className="bg-blue-600 dark:bg-blue-500 h-2.5 rounded-full transition-all duration-300"
                        style={{ width: `${progressPercent}%` }}
                    ></div>
                </div>

                {/* Question */}
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">
                    {activeQuestion.text}
                </h2>

                {/* Options List */}
                <div className="space-y-4 mb-8">
                    {activeQuestion.options.map((option) => {
                        const isSelected = currentAnswer === option.value;
                        return (
                            <button
                                key={option.value}
                                onClick={() => handleSelectOption(option.value)}
                                className={`w-full text-left p-4 rounded-lg border transition-all duration-200 ${
                                    isSelected
                                        ? 'border-blue-600 bg-blue-50/50 dark:border-blue-400 dark:bg-blue-900/20 ring-2 ring-blue-500/20'
                                        : 'border-gray-200 hover:border-gray-300 bg-white dark:border-gray-700 dark:bg-gray-800 dark:hover:border-gray-600'
                                }`}
                                style={{ minHeight: '48px' }}
                            >
                                <div className="flex items-center gap-3">
                                    <span
                                        className={`w-6 h-6 rounded-full flex items-center justify-center text-sm font-semibold border ${
                                            isSelected
                                                ? 'bg-blue-600 border-blue-600 text-white dark:bg-blue-500 dark:border-blue-500'
                                                : 'border-gray-300 text-gray-500 dark:border-gray-600 dark:text-gray-400'
                                        }`}
                                    >
                                        {option.value}
                                    </span>
                                    <span className="text-gray-800 dark:text-gray-200 font-medium">
                                        {option.text}
                                    </span>
                                </div>
                            </button>
                        );
                    })}
                </div>

                {/* Footer Actions */}
                <div className="flex justify-between items-center pt-4 border-t dark:border-gray-700">
                    <button
                        onClick={handleBack}
                        disabled={currentStep === 0}
                        className="btn btn-secondary px-6"
                    >
                        Back
                    </button>
                    <button
                        onClick={handleNext}
                        disabled={!currentAnswer || isSubmitting}
                        className="btn btn-primary px-6"
                    >
                        {currentStep === QUESTIONS.length - 1 ? (isSubmitting ? 'Saving...' : 'Submit') : 'Next'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default RiskQuestionnaireWizard;
