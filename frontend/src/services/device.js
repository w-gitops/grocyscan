/**
 * Generate a stable device fingerprint for X-Device-ID (browser).
 * Device fingerprinting: UA + language + timezone; no PII.
 */
export function getDeviceFingerprint() {
  const ua = typeof navigator !== 'undefined' ? navigator.userAgent : ''
  const lang = typeof navigator !== 'undefined' ? navigator.language : ''
  const tz = typeof Intl !== 'undefined' && Intl.DateTimeFormat
    ? Intl.DateTimeFormat().resolvedOptions().timeZone
    : ''
  const str = [ua, lang, tz].join('|')
  return hashString(str)
}

function hashString(str) {
  let h = 0
  for (let i = 0; i < str.length; i++) {
    const c = str.charCodeAt(i)
    h = ((h << 5) - h) + c
    h |= 0
  }
  return 'fp-' + Math.abs(h).toString(36)
}
