const API_BASE = '';

export async function fetchImages(page = 1, limit = 50) {
  const res = await fetch(`${API_BASE}/api/images?page=${page}&limit=${limit}`);
  if (!res.ok) throw new Error('Failed to fetch images');
  return res.json();
}

export async function fetchImageDetails(imageId) {
  const res = await fetch(`${API_BASE}/api/images/${imageId}`);
  if (!res.ok) throw new Error('Failed to fetch image details');
  return res.json();
}

export async function deleteImage(imageId) {
  const res = await fetch(`${API_BASE}/api/images/${imageId}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to delete image');
  return true;
}

export async function fetchPeople(skip = 0, limit = 100) {
  const res = await fetch(`${API_BASE}/api/people?skip=${skip}&limit=${limit}`);
  if (!res.ok) throw new Error('Failed to fetch people');
  return res.json();
}

export async function fetchImagesByPerson(personId, page = 1, limit = 50) {
  const res = await fetch(`${API_BASE}/api/images/person/${personId}?page=${page}&limit=${limit}`);
  if (!res.ok) throw new Error('Failed to fetch images for person');
  return res.json();
}

export async function updatePersonName(personId, name) {
  const res = await fetch(`${API_BASE}/api/people/${personId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  });
  if (!res.ok) throw new Error('Failed to update person name');
  return res.json();
}

export async function fetchImageFaces(imageId) {
  const res = await fetch(`${API_BASE}/api/images/${imageId}/faces`);
  if (!res.ok) return [];
  return res.json();
}

export async function triggerScan(folderPath, forceRescan = false) {
  const res = await fetch(`${API_BASE}/api/scan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ folder_path: folderPath, force_rescan: forceRescan }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to start scan');
  }
  return res.json();
}

export async function getScanStatus() {
  const res = await fetch(`${API_BASE}/api/scan/status`);
  if (!res.ok) throw new Error('Failed to fetch scan status');
  return res.json();
}

export async function cancelScan() {
  const res = await fetch(`${API_BASE}/api/scan/cancel`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to cancel scan');
  return res.json();
}

export async function triggerFaceProcessing(batchSize = 100) {
  const res = await fetch(`${API_BASE}/api/faces/process`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ batch_size: batchSize }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to trigger face processing');
  }
  return res.json();
}

export async function getFaceStatus() {
  const res = await fetch(`${API_BASE}/api/faces/status`);
  if (!res.ok) throw new Error('Failed to fetch face status');
  return res.json();
}

export async function cancelFaceProcessing() {
  const res = await fetch(`${API_BASE}/api/faces/cancel`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to cancel face processing');
  return res.json();
}
