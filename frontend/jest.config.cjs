const { pathsToModuleNameMapper } = require('ts-jest');
const { compilerOptions } = require('./tsconfig.json');

module.exports = {
  testEnvironment: 'jest-environment-jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],
  moduleNameMapper: {
    ...pathsToModuleNameMapper(compilerOptions.paths, { prefix: '<rootDir>/' }),
    // Handle CSS imports (e.g., for CSS modules)
    "\\.(css|less|scss|sass)$": "identity-obj-proxy",
    // Mock heroicons to prevent SVG rendering issues in Jest
    '^@heroicons/react/24/(outline|solid)$': '<rootDir>/src/__mocks__/heroicons.cjs',
  },
  transform: {
    '^.+\\.tsx?$': 'ts-jest',
  },
};
