const BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8001').replace(/\/+$/, '');

async function readResponse(response) {
  if (response.status === 204) return null;

  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json') || contentType.includes('+json')) {
    try {
      return await response.json();
    } catch {
      return null;
    }
  }

  const text = await response.text();
  return text || null;
}

function describeError(payload, status) {
  const detail = payload && typeof payload === 'object' ? payload.detail : payload;
  if (typeof detail === 'string' && detail.trim()) return detail;
  if (Array.isArray(detail) && detail.length) {
    return detail
      .map((item) => {
        const location = Array.isArray(item.loc)
          ? item.loc.filter((part) => part !== 'body').join('.')
          : '';
        const message = item.msg || item.message || 'Invalid value';
        return location ? `${location}: ${message}` : message;
      })
      .join('; ');
  }
  if (detail && typeof detail === 'object') {
    return detail.message || JSON.stringify(detail);
  }
  return `Request failed with status ${status}.`;
}

export async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  let body = options.body;
  const isFormData = typeof FormData !== 'undefined' && body instanceof FormData;

  if (isFormData) {
    // The browser must add the multipart boundary itself.
    headers.delete('Content-Type');
  } else if (body !== undefined && body !== null && !headers.has('Content-Type')) {
    if (typeof body === 'string') {
      headers.set('Content-Type', 'application/json');
    } else if (typeof body === 'object' && !(body instanceof Blob)) {
      body = JSON.stringify(body);
      headers.set('Content-Type', 'application/json');
    }
  }

  const url = `${BASE}${path.startsWith('/') ? path : `/${path}`}`;
  let response;
  try {
    response = await fetch(url, { ...options, headers, body });
  } catch (error) {
    if (error?.name === 'AbortError') throw error;
    throw new Error(`Could not reach the MeetMate backend at ${BASE}. Check that the server is running.`);
  }

  const payload = await readResponse(response);
  if (!response.ok) throw new Error(describeError(payload, response.status));
  return payload;
}

export async function uploadTranscript(file) {
  const form = new FormData();
  form.append('file', file);
  return api('/api/transcripts/upload', { method: 'POST', body: form });
}

export async function downloadReport(meetingId) {
  const response = await fetch(`${BASE}/api/meetings/${meetingId}/export`);
  if (!response.ok) {
    const payload = await readResponse(response);
    throw new Error(describeError(payload, response.status));
  }

  const blob = await response.blob();
  const disposition = response.headers.get('content-disposition') || '';
  const encodedName = disposition.match(/filename\*=UTF-8''([^;]+)/i)?.[1];
  const regularName = disposition.match(/filename="?([^";]+)"?/i)?.[1];
  let filename = encodedName ? decodeURIComponent(encodedName) : regularName;
  if (!filename) filename = `meeting-${meetingId}.md`;

  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = objectUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
}
