import React, { useRef } from 'react';
import { CalendarIcon } from '@heroicons/react/24/outline';
import { UseFormRegisterReturn } from 'react-hook-form';

interface DateInputProps {
    id: string;
    label?: string;
    register?: UseFormRegisterReturn;
    error?: string;
    className?: string;
    disabled?: boolean;
    placeholder?: string;
    value?: string;
    onChange?: (value: string) => void;
    required?: boolean;
}

const DateInput: React.FC<DateInputProps> = ({
    id,
    label,
    register,
    error,
    className = "",
    disabled = false,
    placeholder = "YYYY-MM-DD",
    value,
    onChange,
    required = false
}) => {
    const datePickerRef = useRef<HTMLInputElement>(null);
    const textInputRef = useRef<HTMLInputElement>(null);

    const handleCalendarClick = () => {
        if (datePickerRef.current && textInputRef.current) {
            // SYNC: Set the picker's value to the text input's current value (if valid)
            const currentVal = textInputRef.current.value;
            // Simple regex check for YYYY-MM-DD
            if (/^\d{4}-\d{2}-\d{2}$/.test(currentVal)) {
                datePickerRef.current.value = currentVal;
            } else {
                // Fallback to today if current value is invalid
                datePickerRef.current.value = new Date().toISOString().split('T')[0];
            }

            // Use showPicker if available (modern browsers), otherwise fallback to click()
            if ('showPicker' in HTMLInputElement.prototype) {
                try {
                    datePickerRef.current.showPicker();
                } catch (e) {
                    // eslint-disable-next-line testing-library/no-node-access
                    datePickerRef.current.click();
                }
            } else {
                // eslint-disable-next-line testing-library/no-node-access
                datePickerRef.current.click();
            }
        }
    };

    const onPickerChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const newValue = e.target.value; // YYYY-MM-DD
        if (newValue && textInputRef.current) {
            // Set the value directly in the visible text input
            textInputRef.current.value = newValue;

            // Trigger both 'change' and 'input' events to ensure react-hook-form sees it
            // Some versions of react-hook-form listen for 'change'
            const changeEvent = new Event('change', { bubbles: true });
            textInputRef.current.dispatchEvent(changeEvent);

            const inputEvent = new Event('input', { bubbles: true });
            textInputRef.current.dispatchEvent(inputEvent);

            // Also trigger standard onChange if provided (for GoalFormModal)
            if (onChange) {
                onChange(newValue);
            }

            // If react-hook-form register's onChange is available, call it directly too
            if (register && register.onChange) {
                register.onChange({
                    target: textInputRef.current,
                    type: 'change'
                } as unknown as React.ChangeEvent<HTMLInputElement>);
            }
        }
    };

    // Correctly handle register's ref and other props
    const { ref: registerRef, ...registerProps } = register || {};

    const handleRef = (node: HTMLInputElement | null) => {
        // Update our local ref for manual DOM manipulation
        if (textInputRef) {
            (textInputRef as React.MutableRefObject<HTMLInputElement | null>).current = node;
        }

        // Forward to register ref if it exists
        if (registerRef) {
            if (typeof registerRef === 'function') {
                registerRef(node);
            } else if (typeof registerRef === 'object' && registerRef !== null) {
                (registerRef as React.MutableRefObject<HTMLInputElement | null>).current = node;
            }
        }
    };

    return (
        <div className={`flex flex-col ${className}`}>
            {label && (
                <label htmlFor={id} className="form-label">
                    {label}
                </label>
            )}
            <div className="relative group">
                <input
                    {...registerProps}
                    ref={handleRef}
                    id={id}
                    type="text"
                    placeholder={placeholder}
                    disabled={disabled}
                    required={required}
                    {...(!register ? {
                        value,
                        onChange: (e: React.ChangeEvent<HTMLInputElement>) => onChange?.(e.target.value)
                    } : {})}
                    className={`form-input pr-10 text-xs sm:text-sm md:text-base ${error ? 'border-red-500 focus:ring-red-500' : ''}`}
                />

                {/* Hidden Date Picker */}
                <input
                    ref={datePickerRef}
                    type="date"
                    className="absolute inset-0 opacity-0 pointer-events-none w-0 h-0"
                    onChange={onPickerChange}
                    tabIndex={-1}
                    aria-hidden="true"
                    disabled={disabled}
                />

                <button
                    type="button"
                    onClick={handleCalendarClick}
                    disabled={disabled}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 text-gray-400 hover:text-blue-500 dark:hover:text-blue-400 transition-colors bg-white dark:bg-gray-700 rounded-md"
                    title="Open calendar"
                >
                    <CalendarIcon className="w-5 h-5" />
                </button>
            </div>
            {error && <p className="text-red-500 text-xs italic">{error}</p>}
        </div>
    );
};

export default DateInput;
