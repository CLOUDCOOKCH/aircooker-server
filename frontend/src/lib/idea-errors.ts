import type { en } from '../i18n';

const messages: Record<string, keyof typeof en> = {
  ai_authentication_failed: 'ideasAuthError',
  ai_model_or_endpoint_not_found: 'ideasModelError',
  ai_request_rejected: 'ideasRequestError',
  ai_content_blocked: 'ideasBlockedError',
  ai_timeout: 'ideasTimeoutError',
  ai_connection_failed: 'ideasProviderConnectionError',
  ai_rate_limited: 'ideasRateError',
  ai_request_limit: 'ideasLocalLimitError',
  ai_output_incomplete: 'ideasIncompleteError',
  ai_schema_validation_failed: 'ideasInvalidError',
  ai_invalid_response: 'ideasInvalidError',
  ai_response_too_large: 'ideasInvalidError',
  ai_provider_failed: 'ideasProviderError',
  ai_generation_interrupted: 'ideasInterruptedError',
  ai_configuration_changed_review_consent: 'ideasConfigurationChanged',
  ai_not_configured: 'ideasConfigure',
  ai_input_format_unsupported: 'ideasConfigure',
  connection_unavailable: 'ideasConnectionError',
  invalid_server_response: 'ideasGatewayError',
  local_storage_unavailable: 'ideasStorageError',
};

/** Provider/server text is untrusted. Only these fixed codes may reach the UI. */
export function ideaError(code?: string | null, expired = false) {
  if (expired) return { message: 'ideasExpiredError' as const, code: undefined };
  if (code && Object.hasOwn(messages, code)) return { message: messages[code], code };
  return { message: 'ideasError' as const, code: undefined };
}
