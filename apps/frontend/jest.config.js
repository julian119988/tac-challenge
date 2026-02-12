/**
 * Jest configuration for TAC Challenge frontend tests.
 *
 * This configuration sets up Jest for testing browser-based JavaScript
 * with ES modules, jsdom environment, and mocked browser APIs.
 */

export default {
  // Use jsdom for browser environment simulation
  testEnvironment: 'jsdom',

  // Test file patterns
  testMatch: [
    '**/test/**/*.test.js'
  ],

  // ES modules support (no transpilation needed for modern JS)
  transform: {},

  // Module name mapping for ES modules
  moduleNameMapper: {
    '^(\\.{1,2}/.*)\\.js$': '$1'
  },

  // Setup files to run after environment setup
  setupFilesAfterEnv: ['<rootDir>/test/setup.js'],

  // Coverage collection
  collectCoverageFrom: [
    '*.js',
    '!index.html',
    '!jest.config.js',
    '!test/**'
  ],

  // Coverage thresholds (optional)
  coverageThresholds: {
    global: {
      statements: 50,
      branches: 40,
      functions: 40,
      lines: 50
    }
  },

  // Verbose output
  verbose: true,

  // Clear mocks between tests
  clearMocks: true,

  // Restore mocks between tests
  restoreMocks: true
};
