/**
 * GitHub URL Parsing Utility
 * Extracts owner, repo, and branch from varied GitHub URL patterns.
 */

export function parseGithubUrl(url) {
    if (!url || typeof url !== 'string') return null;

    // Clean URL
    let cleanUrl = url.trim().replace(/\/$/, '');

    // Pattern: https://github.com/owner/repo/tree/branch or https://github.com/owner/repo
    const regex = /^(?:https?:\/\/)?(?:www\.)?github\.com\/([^\/]+)\/([^\/]+)(?:\/tree\/([^\/]+))?/;
    const match = cleanUrl.match(regex);

    if (match) {
        return {
            owner: match[1],
            repo: match[2].replace(/\.git$/i, ''),
            branch: match[3] || 'main'
        };
    }

    // fallback for short format like owner/repo
    const shortRegex = /^([^\/]+)\/([^\/]+)$/;
    const shortMatch = cleanUrl.match(shortRegex);
    if (shortMatch) {
        return {
            owner: shortMatch[1],
            repo: shortMatch[2].replace(/\.git$/i, ''),
            branch: 'main'
        };
    }

    return null;
}
