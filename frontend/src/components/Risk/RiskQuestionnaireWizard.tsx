import React, { useState } from 'react';
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
        text: 'What is your age?',
        options: [
            { value: 'A', text: 'I am less than 40 yrs old', points: 6 },
            { value: 'B', text: 'I am between 40-55 yrs old', points: 4 },
            { value: 'C', text: 'I am between 55-70 yrs old', points: 2 },
            { value: 'D', text: 'I am > 70 yrs old', points: 1 },
        ],
    },
    {
        id: 'q2',
        text: 'What best describes your income levels?',
        options: [
            { value: 'A', text: 'I expect my income to increase at a high rate', points: 6 },
            { value: 'B', text: 'I expect my income to remain steady', points: 4 },
            { value: 'C', text: 'I do not have a fixed monthly income', points: 2 },
            { value: 'D', text: 'I am retired and/or do not have a source of income', points: 1 },
        ],
    },
    {
        id: 'q3',
        text: 'What is your investment horizon and when do you plan to start withdrawing money from the portfolio?',
        options: [
            { value: 'A', text: 'Less than 1 year', points: 1 },
            { value: 'B', text: 'From 1-3 years', points: 2 },
            { value: 'C', text: 'Between 3-5 years', points: 3 },
            { value: 'D', text: 'More than 5 years', points: 4 },
        ],
    },
    {
        id: 'q4',
        text: 'If a few months after investing, the value of your investments declines by 20%, what would you do?',
        options: [
            { value: 'A', text: 'Cut losses immediately and liquidate all investments (Capital preservation is paramount)', points: 1 },
            { value: 'B', text: 'I would be worried, but would give my investments a little more time', points: 2 },
            { value: 'C', text: 'I will be ok with volatility and accept decline in portfolio value as a part of investing. I would keep my investments as they are', points: 3 },
            { value: 'D', text: 'I would add to my investments. I am confident about my investments and will not be worried by notional losses', points: 4 },
        ],
    },
    {
        id: 'q5',
        text: 'Your investment knowledge is best described as:',
        options: [
            { value: 'A', text: 'Limited: I have little/no investment knowledge beyond traditional bank savings accounts and fixed deposits', points: 1 },
            { value: 'B', text: 'Moderate: I have knowledge and understanding of financial products beyond traditional investments and am aware of related risks', points: 2 },
            { value: 'C', text: 'Advanced: I have sufficient understanding of various financial products and am a regular investor', points: 3 },
            { value: 'D', text: 'Extensive: I have extensive knowledge and understanding of investment products, and am comfortable making my own decisions', points: 4 },
        ],
    },
    {
        id: 'q6',
        text: 'If you receive a lump sum amount of money, how would you invest it?',
        options: [
            { value: 'A', text: 'I would invest in something that offered moderate current income and is conservative', points: 1 },
            { value: 'B', text: 'I would invest in something that offered high current income with a moderate amount of risk', points: 2 },
            { value: 'C', text: 'I would invest in something that offered high total return (current income + capital appreciation) with moderately high risk', points: 3 },
            { value: 'D', text: 'I would invest in something that offered substantial capital appreciation even though it has high risk', points: 4 },
        ],
    },
];

const RiskQuestionnaireWizard: React.FC<RiskQuestionnaireWizardProps> = ({ onSubmit, isSubmitting }) => {
    const [currentStep, setCurrentStep] = useState(0);
    const [answers, setAnswers] = useState<Record<string, string>>({});

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
    const progressPercent = ((currentStep + 1) / QUESTIONS.length) * 100;
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
