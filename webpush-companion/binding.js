// @ts-nocheck

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const BASE64URL_RE = /^[A-Za-z0-9_-]+$/;
const encoder = new TextEncoder();

function hasExactKeys(value, expected) {
  if(!value || typeof value !== 'object' || Array.isArray(value)) return false;
  const keys = Object.keys(value).sort();
  const wanted = [...expected].sort();
  return keys.length === wanted.length && keys.every((key, index) => key === wanted[index]);
}

function utf8Length(value) {
  return encoder.encode(value).length;
}

function validBase64Url(value, maxLength) {
  return typeof value === 'string' && value.length >= 1 && value.length <= maxLength && BASE64URL_RE.test(value);
}

export function normalizeJerkgramPushSubscription(value) {
  if(!hasExactKeys(value, ['endpoint', 'keys', 'vapid'])) return null;
  if(value.vapid !== true) return null;
  if(typeof value.endpoint !== 'string') return null;

  const endpointLength = utf8Length(value.endpoint);
  if(endpointLength < 1 || endpointLength > 4096) return null;

  let parsed;
  try {
    parsed = new URL(value.endpoint);
  } catch(_) {
    return null;
  }
  if(parsed.protocol !== 'https:' || !parsed.hostname) return null;

  if(!hasExactKeys(value.keys, ['p256dh', 'auth'])) return null;
  if(!validBase64Url(value.keys.p256dh, 256)) return null;
  if(!validBase64Url(value.keys.auth, 128)) return null;

  return {
    endpoint: value.endpoint,
    keys: {
      p256dh: value.keys.p256dh,
      auth: value.keys.auth
    },
    vapid: true
  };
}

export function buildJerkgramBindingEnvelope(installationId, subscription) {
  if(typeof installationId !== 'string' || !UUID_RE.test(installationId)) return null;
  const normalized = normalizeJerkgramPushSubscription(subscription);
  if(!normalized) return null;

  return {
    v: 1,
    installationId,
    subscription: normalized
  };
}

function normalizeEnvelope(value) {
  if(!hasExactKeys(value, ['v', 'installationId', 'subscription'])) return null;
  if(value.v !== 1) return null;
  return buildJerkgramBindingEnvelope(value.installationId, value.subscription);
}

export function encodeJerkgramBinding(envelope) {
  const normalized = normalizeEnvelope(envelope);
  if(!normalized) return null;

  const json = JSON.stringify(normalized);
  const bytes = encoder.encode(json);
  if(bytes.length > 5376) return null;

  let binary = '';
  for(const byte of bytes) binary += String.fromCharCode(byte);
  const encoded = btoa(binary)
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/g, '');
  if(encoded.length > 7168) return null;
  return encoded;
}

export function buildJerkgramBindingUrl(action, installationId, subscription) {
  if(action !== 'register' && action !== 'unregister') return null;

  const envelope = buildJerkgramBindingEnvelope(installationId, subscription);
  if(!envelope) return null;
  const binding = encodeJerkgramBinding(envelope);
  if(!binding) return null;

  const url = `jerkgram://push/${action}?binding=${binding}`;
  if(utf8Length(url) > 8192) return null;
  return url;
}
