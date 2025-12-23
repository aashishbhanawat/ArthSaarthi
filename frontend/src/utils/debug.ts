/**
 * Debug logging utility for ArthSaarthi frontend.
 * 
 * Enable debug logging by running in browser console:
 *   localStorage.setItem('debug', 'true')
 *   location.reload()
 * 
 * Disable debug logging:
 *   localStorage.removeItem('debug')
 *   location.reload()
 * 
 * Or enable for specific namespaces only:
 *   localStorage.setItem('debug', 'transaction,portfolio')
 */

const getDebugSetting = (): string | null => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('debug');
};

const isDebugEnabled = (namespace?: string): boolean => {
    const debugSetting = getDebugSetting();
    if (!debugSetting) return false;
    if (debugSetting === 'true' || debugSetting === '*') return true;
    if (!namespace) return false;

    const enabledNamespaces = debugSetting.split(',').map(n => n.trim().toLowerCase());
    return enabledNamespaces.includes(namespace.toLowerCase());
};

/**
 * Debug logger that only logs when debug mode is enabled.
 * 
 * @param namespace - Category of the log (e.g., 'transaction', 'portfolio')
 * @param message - Log message
 * @param data - Optional data to log
 */
export const debugLog = (namespace: string, message: string, data?: unknown): void => {
    if (!isDebugEnabled(namespace)) return;

    const timestamp = new Date().toISOString().split('T')[1].split('.')[0];
    const prefix = `[${timestamp}] [${namespace.toUpperCase()}]`;

    if (data !== undefined) {
        console.log(`${prefix} ${message}`, data);
    } else {
        console.log(`${prefix} ${message}`);
    }
};

/**
 * Debug warning that only logs when debug mode is enabled.
 */
export const debugWarn = (namespace: string, message: string, data?: unknown): void => {
    if (!isDebugEnabled(namespace)) return;

    const timestamp = new Date().toISOString().split('T')[1].split('.')[0];
    const prefix = `[${timestamp}] [${namespace.toUpperCase()}]`;

    if (data !== undefined) {
        console.warn(`${prefix} ${message}`, data);
    } else {
        console.warn(`${prefix} ${message}`);
    }
};

/**
 * Check if debug mode is enabled (for conditional logic).
 */
export const isDebugMode = (): boolean => isDebugEnabled();
