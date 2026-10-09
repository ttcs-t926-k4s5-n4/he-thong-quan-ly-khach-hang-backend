'use strict';
/** Giới hạn tần suất theo cửa sổ trượt, lưu trong bộ nhớ tiến trình. */
class SlidingWindowLimiter {
  constructor() { this.hits = new Map(); }

  hit(key, limit, windowSeconds) {
    const now = Date.now();
    const windowMs = windowSeconds * 1000;
    const list = (this.hits.get(key) || []).filter((t) => now - t < windowMs);
    if (list.length >= limit) {
      this.hits.set(key, list);
      return { allowed: false, retryAfter: Math.max(1, Math.ceil((windowMs - (now - list[0])) / 1000)) };
    }
    list.push(now);
    this.hits.set(key, list);
    return { allowed: true, retryAfter: 0 };
  }

  reset() { this.hits.clear(); }
}

/** '5/600' -> { limit: 5, windowSeconds: 600 } */
function parseRate(spec) {
  const [limit, seconds] = String(spec).split('/');
  return { limit: Number(limit), windowSeconds: Number(seconds) };
}

module.exports = { SlidingWindowLimiter, parseRate };
