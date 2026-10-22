import assert from 'node:assert/strict';
import { test } from 'node:test';
import { ideaError } from './idea-errors.ts';
import { de, en } from '../i18n.ts';

test('idea errors offer localized recovery without echoing untrusted diagnostics', () => {
  for (const [code, message] of [
    ['ai_authentication_failed', 'ideasAuthError'],
    ['ai_model_or_endpoint_not_found', 'ideasModelError'],
    ['ai_request_rejected', 'ideasRequestError'],
    ['ai_content_blocked', 'ideasBlockedError'],
    ['ai_timeout', 'ideasTimeoutError'],
    ['ai_rate_limited', 'ideasRateError'],
    ['ai_request_limit', 'ideasLocalLimitError'],
    ['ai_output_incomplete', 'ideasIncompleteError'],
    ['ai_schema_validation_failed', 'ideasInvalidError'],
    ['ai_generation_interrupted', 'ideasInterruptedError'],
    ['ai_configuration_changed_review_consent', 'ideasConfigurationChanged'],
    ['connection_unavailable', 'ideasConnectionError'],
    ['local_storage_unavailable', 'ideasStorageError'],
  ]) {
    const result = ideaError(code);
    assert.equal(result.message, message);
    assert.equal(result.code, code);
    assert.ok(en[result.message] && de[result.message]);
  }
  for (const code of [
    'private_api_key_value',
    '<script>alert(1)</script>',
    '__proto__',
    'constructor',
    undefined,
  ]) {
    assert.deepEqual(ideaError(code), { message: 'ideasError', code: undefined });
  }
  assert.deepEqual(ideaError('ai_timeout', true), {
    message: 'ideasExpiredError',
    code: undefined,
  });
});
