# Offline account-age observations

Source: https://github.com/lastochkin-group/telegram-account-age-estimator/blob/main/ages.json
Retrieved 2026-10-25. Only numeric ID/year observations are used; no source implementation is copied. These are third-party empirical observations, not authenticated Telegram registration records. Runtime sends no ID to this source or any external service.

The original 44 timestamp samples are reduced to UTC calendar years. Non-monotonic observations are retained. Adjacent ID observations produce an explicitly approximate year/range; the endpoints are not confidence limits. No dates are extrapolated below the smallest ID or above 5520018289. Real Telegram-provided month/year takes priority. Bots/deleted users are excluded.
