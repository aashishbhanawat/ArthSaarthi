import '@testing-library/jest-dom';

// Mock the entire react-router-dom module
// This is a general mock. Specific tests can override parts of it if needed.
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'), // import and retain the original functionalities
  useNavigate: () => jest.fn(), // mock useNavigate by default
  useParams: () => ({}), // mock useParams to return an empty object by default
}));


// Mock the entire react-chartjs-2 module to prevent canvas errors in JSDOM
jest.mock('react-chartjs-2', () => {
    const React = require('react');
    return {
        Line: () => React.createElement('div', { 'data-testid': 'line-chart-mock' }),
        Pie: () => React.createElement('div', { 'data-testid': 'pie-chart-mock' }),
    };
});