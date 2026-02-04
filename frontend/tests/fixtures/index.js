/**
 * Central export for all test fixtures
 * 
 * Usage:
 *   import { test, expect, TEST_CREDENTIALS } from './fixtures'
 */

export { 
  test, 
  expect, 
  TEST_CREDENTIALS,
  isBackendAvailable,
  skipIfNoBackend
} from './auth.fixture.js'
