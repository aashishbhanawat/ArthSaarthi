module.exports = {
  testEnvironment: 'jest-environment-jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],
  moduleNameMapper: {
    // Handle CSS imports (e.g., for CSS modules)
    "\\.(css|less|scss|sass)$": "identity-obj-proxy",
    // Mock heroicons to prevent SVG rendering issues in Jest
    '^@heroicons/react/24/(outline|solid)$': '<rootDir>/src/__mocks__/heroicons.cjs',
  },
  transform: {
    '^.+\\.tsx?$': [
      'ts-jest',
      {
        tsconfig: 'tsconfig.json',
        babelConfig: {
          presets: [
            ['@babel/preset-env', { targets: { node: 'current' } }],
            '@babel/preset-typescript',
            ['@babel/preset-react', { runtime: 'automatic' }]
          ],
          plugins: [
            'babel-plugin-transform-vite-meta-env'
          ]
        }
      },
    ],
  },
};

