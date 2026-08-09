/**
 * CodeGalaxy — API Client
 * Axios wrapper for communicating with the FastAPI backend.
 */
import axios from 'axios';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
const API_BASE = `${BACKEND_URL}/api`;

const api = axios.create({
    baseURL: API_BASE,
    timeout: 30000,
    headers: { 'Content-Type': 'application/json' },
});

/**
 * Start ingestion of a GitHub repository.
 */
export async function ingestRepo(owner, repo, branch = 'main') {
    const res = await api.post('/ingest', { owner, repo, branch });
    return res.data;
}

/**
 * Poll ingestion status.
 */
export async function getIngestStatus(repoId) {
    const res = await api.get(`/ingest/${repoId}/status`);
    return res.data;
}

/**
 * List all processed repositories.
 */
export async function listRepos() {
    const res = await api.get('/repos');
    return res.data;
}

/**
 * Get the full graph data for a repository.
 */
export async function getGraph(repoId) {
    const res = await api.get(`/repos/${repoId}/graph`);
    return res.data;
}

/**
 * Get detailed file information.
 */
export async function getFileDetail(fileId) {
    const res = await api.get(`/files/${fileId}`);
    return res.data;
}

/**
 * Generate AI Summary for a file.
 */
export async function getFileSummary(fileId) {
    const res = await api.post(`/files/${fileId}/summary`);
    return res.data;
}

export async function pingBackend() {
    try {
        const res = await axios.get(`${BACKEND_URL}/ping`, { timeout: 15000 });
        return res.status === 200;
    } catch {
        return false;
    }
}

export default api;
