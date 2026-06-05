const searchForm = document.getElementById('searchForm');
const bookTitlesInput = document.getElementById('bookTitles');
const searchBtn = document.getElementById('searchBtn');
const searchBtnText = document.getElementById('searchBtnText');
const searchSpinner = document.getElementById('searchSpinner');
const clearBtn = document.getElementById('clearBtn');
const resultsSection = document.getElementById('resultsSection');
const resultsContainer = document.getElementById('resultsContainer');
const statsText = document.getElementById('statsText');
const serverInfo = document.getElementById('serverInfo');

// Handle form submission
searchForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const text = bookTitlesInput.value.trim();

    if (!text) {
        alert('Bitte gib mindestens einen Buchtitel ein.');
        return;
    }

    // Show loading state
    setLoadingState(true);
    resultsSection.classList.add('d-none');

    try {
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: text })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Fehler bei der Suche');
        }

        const data = await response.json();
        displayResults(data);

    } catch (error) {
        console.error('Search error:', error);
        alert(`Fehler bei der Suche: ${error.message}`);
    } finally {
        setLoadingState(false);
    }
});

// Handle clear button
clearBtn.addEventListener('click', () => {
    bookTitlesInput.value = '';
    resultsSection.classList.add('d-none');
    resultsContainer.innerHTML = '';
    bookTitlesInput.focus();
});

// Set loading state
function setLoadingState(isLoading) {
    if (isLoading) {
        searchBtn.disabled = true;
        searchBtnText.textContent = 'Suche läuft...';
        searchSpinner.classList.remove('d-none');
    } else {
        searchBtn.disabled = false;
        searchBtnText.textContent = 'Suchen';
        searchSpinner.classList.add('d-none');
    }
}

// Display search results
function displayResults(data) {
    resultsContainer.innerHTML = '';

    // Update statistics
    statsText.textContent = `${data.total_queries} Bücher gesucht: ${data.found_count} gefunden, ${data.not_found_count} nicht gefunden`;

    // Show which Calibre server was queried (helps diagnose deployment issues)
    if (serverInfo) {
        serverInfo.textContent = `Calibre-Server: ${data.calibre_server || '–'}`;
    }

    // Display each result
    data.results.forEach(result => {
        const resultItem = createResultItem(result);
        resultsContainer.appendChild(resultItem);
    });

    // Show results section with animation
    resultsSection.classList.remove('d-none');
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Create a result item element
function createResultItem(result) {
    const div = document.createElement('div');
    div.className = `result-item ${result.found ? 'found' : 'not-found'}`;

    const badge = result.found
        ? '<span class="badge bg-success">Gefunden</span>'
        : '<span class="badge bg-danger">Nicht gefunden</span>';

    let contentHTML = `
        <div class="d-flex justify-content-between align-items-start mb-2">
            <div class="result-query">${escapeHtml(result.query)}</div>
            ${badge}
        </div>
    `;

    if (result.found && result.book_url) {
        contentHTML += `
            <div class="mb-2">
                <a href="${escapeHtml(result.book_url)}" target="_blank" class="result-link me-3">
                    📚 In Calibre-Web öffnen →
                </a>
            </div>
        `;

        if (result.total_num > 1) {
            contentHTML += `
                <div class="result-info mb-2">
                    ${result.total_num} Treffer gefunden
                </div>
            `;
        }
    } else if (result.error) {
        contentHTML += `
            <div class="result-info text-danger mb-2">
                Fehler: ${escapeHtml(result.error)}
            </div>
        `;
    }

    // Always add SceneNZBs link
    if (result.scenenzbs_url) {
        contentHTML += `
            <div class="mb-1">
                <a href="${escapeHtml(result.scenenzbs_url)}" target="_blank" class="result-link-secondary">
                    🔍 Auf SceneNZBs suchen →
                </a>
            </div>
        `;
    }

    // Search protocol: collapsible per-strategy log
    if (result.log && result.log.length > 0) {
        contentHTML += createSearchLog(result.log);
    }

    div.innerHTML = contentHTML;
    return div;
}

// Build a collapsible search protocol table for a single result
function createSearchLog(log) {
    const rows = log.map(attempt => {
        const status = attempt.error
            ? `<span class="text-danger">${escapeHtml(attempt.error)}</span>`
            : `<span class="text-success">${attempt.status ?? '–'}</span>`;
        const hits = attempt.error
            ? '–'
            : `${attempt.book_count}/${attempt.total_num}`;
        return `
            <tr>
                <td class="text-break"><code>${escapeHtml(attempt.strategy)}</code></td>
                <td>${status}</td>
                <td class="text-end">${hits}</td>
                <td class="text-end text-muted">${attempt.elapsed_ms} ms</td>
            </tr>
        `;
    }).join('');

    return `
        <details class="search-log mt-2">
            <summary class="text-muted small">🔎 Suchprotokoll (${log.length} ${log.length === 1 ? 'Strategie' : 'Strategien'})</summary>
            <div class="table-responsive mt-2">
                <table class="table table-sm table-bordered small mb-0">
                    <thead>
                        <tr>
                            <th>Strategie</th>
                            <th>Status</th>
                            <th class="text-end">Treffer</th>
                            <th class="text-end">Dauer</th>
                        </tr>
                    </thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
        </details>
    `;
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Focus on textarea on page load
window.addEventListener('DOMContentLoaded', () => {
    bookTitlesInput.focus();
});
