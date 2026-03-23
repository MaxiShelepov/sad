import { API_BASE_URL } from './config';

function getCandidateUrls() {
  if (typeof window !== 'undefined' && window.location.hostname === '127.0.0.1') {
    return ['http://127.0.0.1:8001/api', API_BASE_URL].filter(Boolean);
  }
  return [API_BASE_URL].filter(Boolean);
}

async function request(path, options = {}) {
  let lastError = null;

  for (const baseUrl of getCandidateUrls()) {
    try {
      const response = await fetch(`${baseUrl}${path}`, {
        headers: {
          'Content-Type': 'application/json',
          ...(options.headers || {}),
        },
        ...options,
      });

      const text = await response.text();
      const data = text ? JSON.parse(text) : {};

      if (!response.ok) {
        throw new Error(data.detail || data.message || 'Ошибка запроса к серверу');
      }

      return data;
    } catch (error) {
      lastError = error;
    }
  }

  throw lastError || new Error('Ошибка запроса к серверу');
}

export const api = {
  checkLicense: (hwid) => request('/license/check', { method: 'POST', body: JSON.stringify({ hwid }) }),
  getDashboard: (hwid) => request(`/dashboard?hwid=${encodeURIComponent(hwid)}`),
  getProfiles: (hwid) => request(`/profiles?hwid=${encodeURIComponent(hwid)}`),
  getProfile: (profileId, hwid) => request(`/profiles/${profileId}?hwid=${encodeURIComponent(hwid)}`),
  createProfile: (payload) => request('/profiles', { method: 'POST', body: JSON.stringify(payload) }),
  importProfiles: (payload) => request('/profiles/import', { method: 'POST', body: JSON.stringify(payload) }),
  updateProfile: (profileId, hwid, payload) =>
    request(`/profiles/${profileId}?hwid=${encodeURIComponent(hwid)}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteProfile: (profileId, hwid) => request(`/profiles/${profileId}?hwid=${encodeURIComponent(hwid)}`, { method: 'DELETE' }),
  getFingerprint: (profileId, hwid) => request(`/profiles/${profileId}/fingerprint?hwid=${encodeURIComponent(hwid)}`),
  updateFingerprint: (profileId, hwid, payload) =>
    request(`/profiles/${profileId}/fingerprint?hwid=${encodeURIComponent(hwid)}`, { method: 'PUT', body: JSON.stringify(payload) }),
  randomizeFingerprint: (profileId, hwid) =>
    request(`/profiles/${profileId}/fingerprint/randomize?hwid=${encodeURIComponent(hwid)}`, { method: 'POST' }),
  getSession: (profileId, hwid) => request(`/profiles/${profileId}/session?hwid=${encodeURIComponent(hwid)}`),
  updateSession: (profileId, hwid, payload) =>
    request(`/profiles/${profileId}/session?hwid=${encodeURIComponent(hwid)}`, { method: 'PUT', body: JSON.stringify({ data: payload }) }),
  getWarmups: (hwid) => request(`/warmups?hwid=${encodeURIComponent(hwid)}`),
  startWarmup: (payload) => request('/warmups/start', { method: 'POST', body: JSON.stringify(payload) }),
  stopWarmup: (jobId) => request(`/warmups/${jobId}/stop`, { method: 'POST' }),
  startFarm: (payload) => request('/farm/start', { method: 'POST', body: JSON.stringify(payload) }),
  stopFarm: (hwid) => request(`/farm/stop?hwid=${encodeURIComponent(hwid)}`, { method: 'POST' }),
};
