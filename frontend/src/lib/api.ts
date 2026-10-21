import type { components } from '../api-schema';

export type BrowserSession = components['schemas']['BrowserSession'];
export class APIError extends Error {
  readonly code: string;
  readonly status: number;
  constructor(code: string, status: number) {
    super(code);
    this.code = code;
    this.status = status;
  }
}

export function csrfToken(): string {
  const entry = document.cookie
    .split(';')
    .find((part) => part.trim().startsWith('aircooker_pwa_csrf='));
  return entry ? decodeURIComponent(entry.trim().slice('aircooker_pwa_csrf='.length)) : '';
}

/** Same-origin only. Credentials remain in Secure/HttpOnly cookies, never in app storage. */
export class APIClient {
  private refreshing: Promise<void> | null = null;

  private async perform(path: string, init: RequestInit): Promise<Response> {
    if (!path.startsWith('/api/v1/') || path.includes('://'))
      throw new APIError('invalid_api_path', 0);
    const headers = new Headers(init.headers);
    headers.set('X-Aircooker-Client', 'pwa');
    if (!['GET', 'HEAD'].includes(init.method ?? 'GET')) headers.set('X-CSRF-Token', csrfToken());
    if (typeof init.body === 'string') headers.set('Content-Type', 'application/json');
    try {
      return await fetch(path, {
        ...init,
        headers,
        credentials: 'same-origin',
        cache: 'no-store',
        redirect: 'error',
        signal: init.signal ?? AbortSignal.timeout(30_000),
      });
    } catch {
      throw new APIError('connection_unavailable', 0);
    }
  }

  private async decode<T>(response: Response): Promise<T> {
    if (response.status === 204) return undefined as T;
    const text = await response.text();
    if (text.length > 5 * 1024 * 1024) throw new APIError('response_too_large', response.status);
    let value: unknown;
    try {
      value = JSON.parse(text);
    } catch {
      throw new APIError('invalid_server_response', response.status);
    }
    if (!response.ok) {
      const code =
        typeof value === 'object' &&
        value !== null &&
        'error' in value &&
        typeof value.error === 'object' &&
        value.error !== null &&
        'code' in value.error &&
        typeof value.error.code === 'string'
          ? value.error.code
          : 'request_failed';
      throw new APIError(code, response.status);
    }
    return value as T;
  }

  private refresh(): Promise<void> {
    if (this.refreshing) return this.refreshing;
    const renew = async () => {
      // Another page may already have rotated the shared cookies while we waited.
      const session = await this.perform('/api/v1/pwa/auth/session', {});
      if (session.ok) return;
      await this.decode(await this.perform('/api/v1/pwa/auth/refresh', { method: 'POST' }));
    };
    const pending = (async () => {
      if (navigator.locks) await navigator.locks.request('aircooker-auth-refresh', renew);
      else await renew();
    })();
    this.refreshing = pending.finally(() => {
      this.refreshing = null;
    });
    return this.refreshing;
  }

  async request<T>(path: string, init: RequestInit = {}, renew = true): Promise<T> {
    let response = await this.perform(path, init);
    if (response.status === 401 && renew) {
      await this.refresh();
      response = await this.perform(path, init);
    }
    try {
      return await this.decode<T>(response);
    } catch (error) {
      // A parallel page may rotate the CSRF cookie after this request was prepared.
      // The server rejects CSRF before performing a mutation, so one fresh retry is safe.
      if (
        renew &&
        error instanceof APIError &&
        error.status === 403 &&
        error.code === 'csrf_failed'
      ) {
        return this.decode<T>(await this.perform(path, init));
      }
      throw error;
    }
  }

  async media(id: string): Promise<Blob> {
    if (!/^[a-f\d-]{36}$/i.test(id)) throw new APIError('invalid_image_id', 0);
    const path = '/api/v1/media/' + id;
    let response = await this.perform(path, {});
    if (response.status === 401) {
      await this.refresh();
      response = await this.perform(path, {});
    }
    if (!response.ok) return this.decode<never>(response);
    const blob = await response.blob();
    if (!['image/jpeg', 'image/png'].includes(blob.type) || blob.size > 8 * 1024 * 1024) {
      throw new APIError('invalid_photo', response.status);
    }
    return blob;
  }

  async upload(id: string, blob: Blob): Promise<void> {
    const body = new FormData();
    body.append('file', blob, 'recipe.jpg');
    const result = await this.request<components['schemas']['MediaInfo']>('/api/v1/media/' + id, {
      method: 'PUT',
      body,
    });
    if (
      result.id !== id ||
      !['image/jpeg', 'image/png'].includes(result.content_type) ||
      !Number.isSafeInteger(result.byte_count) ||
      result.byte_count <= 0 ||
      !/^[a-f\d]{64}$/.test(result.sha256)
    )
      throw new APIError('invalid_server_response', 0);
  }
}
