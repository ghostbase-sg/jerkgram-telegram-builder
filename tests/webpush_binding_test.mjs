import assert from 'node:assert/strict';
import {
  normalizeJerkgramPushSubscription,
  buildJerkgramBindingEnvelope,
  encodeJerkgramBinding,
  buildJerkgramBindingUrl
} from '../webpush-companion/binding.js';

const INSTALLATION_ID = '123e4567-e89b-42d3-a456-426614174000';
const VALID_SUBSCRIPTION = {
  endpoint: 'https://push.example.test/sub/abc',
  keys: {
    p256dh: 'Abc_123-xyz',
    auth: 'Def_456-xyz'
  },
  vapid: true
};

const EXPECTED = {
  v: 1,
  installationId: INSTALLATION_ID,
  subscription: VALID_SUBSCRIPTION
};

const decodeBinding = (binding) => {
  assert.equal(binding.includes('='), false, 'binding must be base64url without padding');
  const base64 = binding.replace(/-/g, '+').replace(/_/g, '/');
  const padded = base64 + '='.repeat((4 - (base64.length % 4)) % 4);
  return JSON.parse(Buffer.from(padded, 'base64').toString('utf8'));
};

assert.deepEqual(normalizeJerkgramPushSubscription(VALID_SUBSCRIPTION), VALID_SUBSCRIPTION);
assert.deepEqual(buildJerkgramBindingEnvelope(INSTALLATION_ID, VALID_SUBSCRIPTION), EXPECTED);

const encoded = encodeJerkgramBinding(EXPECTED);
assert.ok(encoded);
assert.deepEqual(decodeBinding(encoded), EXPECTED);
assert.equal(
  JSON.stringify(decodeBinding(encoded)),
  '{"v":1,"installationId":"123e4567-e89b-42d3-a456-426614174000","subscription":{"endpoint":"https://push.example.test/sub/abc","keys":{"p256dh":"Abc_123-xyz","auth":"Def_456-xyz"},"vapid":true}}'
);

for(const action of ['register', 'unregister']) {
  const url = buildJerkgramBindingUrl(action, INSTALLATION_ID, VALID_SUBSCRIPTION);
  assert.ok(url);
  const parsed = new URL(url);
  assert.equal(parsed.protocol, 'jerkgram:');
  assert.equal(parsed.hostname, 'push');
  assert.equal(parsed.pathname, `/${action}`);
  assert.deepEqual([...parsed.searchParams.keys()], ['binding']);
  assert.deepEqual(decodeBinding(parsed.searchParams.get('binding')), EXPECTED);
}

assert.equal(buildJerkgramBindingUrl('authorize', INSTALLATION_ID, VALID_SUBSCRIPTION), null);
assert.equal(buildJerkgramBindingEnvelope('not-a-uuid', VALID_SUBSCRIPTION), null);
assert.equal(
  normalizeJerkgramPushSubscription({...VALID_SUBSCRIPTION, endpoint: 'http://push.example.test/sub/abc'}),
  null
);
assert.equal(
  normalizeJerkgramPushSubscription({...VALID_SUBSCRIPTION, endpoint: 'https:///missing-host'}),
  null
);
assert.equal(
  normalizeJerkgramPushSubscription({...VALID_SUBSCRIPTION, keys: {...VALID_SUBSCRIPTION.keys, p256dh: 'bad+key'}}),
  null
);
assert.equal(
  normalizeJerkgramPushSubscription({...VALID_SUBSCRIPTION, keys: {...VALID_SUBSCRIPTION.keys, auth: 'bad/key'}}),
  null
);
assert.equal(normalizeJerkgramPushSubscription({...VALID_SUBSCRIPTION, vapid: false}), null);
assert.equal(normalizeJerkgramPushSubscription({...VALID_SUBSCRIPTION, extra: true}), null);
assert.equal(
  normalizeJerkgramPushSubscription({
    ...VALID_SUBSCRIPTION,
    keys: {...VALID_SUBSCRIPTION.keys, extra: 'nope'}
  }),
  null
);
assert.equal(
  normalizeJerkgramPushSubscription({
    ...VALID_SUBSCRIPTION,
    keys: {...VALID_SUBSCRIPTION.keys, p256dh: 'A'.repeat(257)}
  }),
  null
);
assert.equal(
  normalizeJerkgramPushSubscription({
    ...VALID_SUBSCRIPTION,
    keys: {...VALID_SUBSCRIPTION.keys, auth: 'A'.repeat(129)}
  }),
  null
);
assert.ok(normalizeJerkgramPushSubscription({...VALID_SUBSCRIPTION, endpoint: `https://e.test/${'a'.repeat(4000)}`}));
assert.equal(normalizeJerkgramPushSubscription({...VALID_SUBSCRIPTION, endpoint: `https://e.test/${'a'.repeat(4096)}`}), null);

assert.equal(
  buildJerkgramBindingEnvelope(INSTALLATION_ID, {...VALID_SUBSCRIPTION, accountId: '42'}),
  null
);
assert.equal(
  buildJerkgramBindingEnvelope(INSTALLATION_ID, {...VALID_SUBSCRIPTION, authKey: 'secret'}),
  null
);
assert.equal(
  encodeJerkgramBinding({...EXPECTED, extra: true}),
  null
);

const huge = {
  v: 1,
  installationId: INSTALLATION_ID,
  subscription: {
    endpoint: `https://e.test/${'a'.repeat(5300)}`,
    keys: {p256dh: 'A', auth: 'B'},
    vapid: true
  }
};
assert.equal(encodeJerkgramBinding(huge), null);

const almostMax = buildJerkgramBindingUrl('register', INSTALLATION_ID, {
  endpoint: `https://e.test/${'a'.repeat(3900)}`,
  keys: {p256dh: 'A'.repeat(256), auth: 'B'.repeat(128)},
  vapid: true
});
assert.ok(almostMax);
assert.ok(new TextEncoder().encode(almostMax).length <= 8192);

const decoded = decodeBinding(encoded);
assert.equal('user_id' in decoded, false);
assert.equal('accountId' in decoded, false);
assert.equal('authKey' in decoded, false);
assert.equal('phone' in decoded, false);
assert.equal('token' in decoded, false);

console.log('webpush passwordless binding tests: PASS');
