/**
 * Centralized API Error type for consistent error handling across the frontend.
 * This extends Error to be compatible with React Query's error handling.
 */
export interface ApiErrorResponse {
    detail?: string | { msg: string }[];
}

export interface ApiError extends Error {
    response?: {
        data?: ApiErrorResponse;
        status?: number;
    };
}

/**
 * Helper function to extract error message from API error
 */
export const getErrorMessage = (error: ApiError | Error): string => {
    if ('response' in error && error.response?.data?.detail) {
        const detail = error.response.data.detail;
        if (typeof detail === 'string') {
            return detail;
        }
        if (Array.isArray(detail)) {
            return detail.map(d => d.msg).join(', ');
        }
    }
    return error.message || 'An unexpected error occurred';
};
