const API_BASE = 'http://localhost:5000/api';
let allCompetitors = [];
let allUpdates = [];

// Navigation
function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
    });

    // Remove active class from all buttons
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected section and activate button
    document.getElementById(sectionName).classList.add('active');
    event.target.classList.add('active');

    // Load section-specific data
    switch(sectionName) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'competitors':
            loadCompetitors();
            break;
        case 'updates':
            loadAllUpdates();
            break;
        case 'alerts':
            loadAlerts();
            break;
    }
}

// Load dashboard data
async function loadDashboard() {
    try {
        showLoading('dashboard');

        const response = await fetch(`${API_BASE}/dashboard/stats`);
        const data = await response.json();

        // Update stats
        document.getElementById('total-competitors').textContent = data.total_competitors;
        document.getElementById('total-updates').textContent = data.total_updates;

        const highImpact = data.recent_updates.filter(update => update.impact_score > 0.7).length;
        document.getElementById('high-impact').textContent = highImpact;
        document.getElementById('last-updated').textContent = new Date().toLocaleTimeString();

        // Update category chart
        updateCategoryChart(data.category_distribution);

        // Update recent updates
        updateRecentUpdates(data.recent_updates);

    } catch (error) {
        console.error('Error loading dashboard:', error);
        showError('dashboard', 'Failed to load dashboard data');
    }
}

// Update category distribution chart
function updateCategoryChart(categoryData) {
    const ctx = document.getElementById('categoryChart').getContext('2d');

    // Destroy existing chart if it exists
    if (window.categoryChart) {
        window.categoryChart.destroy();
    }

    const colors = {
        'pricing': '#e74c3c',
        'campaign': '#3498db',
        'product_release': '#2ecc71',
        'partnership': '#f39c12',
        'other': '#9b59b6'
    };

    window.categoryChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(categoryData).map(key => key.charAt(0).toUpperCase() + key.slice(1)),
            datasets: [{
                data: Object.values(categoryData),
                backgroundColor: Object.keys(categoryData).map(key => colors[key] || '#95a5a6'),
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// Update recent updates list
function updateRecentUpdates(updates) {
    const container = document.getElementById('recent-updates');
    container.innerHTML = '';

    if (updates.length === 0) {
        container.innerHTML = '<div class="update-item">No updates found. Run scraping to collect data.</div>';
        return;
    }

    updates.forEach(update => {
        const updateElement = document.createElement('div');
        updateElement.className = `update-item ${update.impact_score > 0.7 ? 'high-impact' : ''}`;

        updateElement.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div style="flex: 1;">
                    <span class="update-category" style="background: ${getCategoryColor(update.category)}">
                        ${update.category.toUpperCase()}
                    </span>
                    <strong>${update.title || 'Competitor Update'}</strong>
                    <p style="margin: 8px 0; color: #666; font-size: 0.9em;">
                        ${update.content?.substring(0, 120)}...
                    </p>
                    <small style="color: #999;">
                        📅 ${new Date(update.detected_at).toLocaleDateString()}
                        • 🌐 ${update.source}
                        • 🏢 ${getCompetitorName(update.competitor_id)}
                    </small>
                </div>
                <div style="text-align: right; min-width: 80px;">
                    <div style="font-size: 0.8em; color: #666;">Impact Score</div>
                    <div style="font-weight: bold; font-size: 1.2em; color: ${update.impact_score > 0.7 ? '#e74c3c' : '#3498db'}">
                        ${(update.impact_score * 100).toFixed(0)}%
                    </div>
                </div>
            </div>
        `;

        container.appendChild(updateElement);
    });
}

// Load all competitors
async function loadCompetitors() {
    try {
        showLoading('competitors');

        const response = await fetch(`${API_BASE}/competitors`);
        allCompetitors = await response.json();

        const container = document.getElementById('competitors-list');
        container.innerHTML = '';

        if (allCompetitors.length === 0) {
            container.innerHTML = '<div class="update-item">No competitors found. Add some competitors to start monitoring.</div>';
            return;
        }

        allCompetitors.forEach(competitor => {
            const competitorElement = document.createElement('div');
            competitorElement.className = 'competitor-card';
            competitorElement.innerHTML = `
                <h3>${competitor.name}</h3>
                <p>🌐 ${competitor.website}</p>
                <p>📊 Last checked: ${competitor.last_checked || 'Never'}</p>
                <button onclick="scrapeCompetitor(${competitor.id})" class="btn-primary" style="margin-top: 10px;">
                    Scrape Now
                </button>
            `;
            container.appendChild(competitorElement);
        });

    } catch (error) {
        console.error('Error loading competitors:', error);
        showError('competitors', 'Failed to load competitors');
    }
}

// Load all updates with filtering
async function loadAllUpdates() {
    try {
        showLoading('updates');

        const response = await fetch(`${API_BASE}/updates?limit=100`);
        allUpdates = await response.json();

        // Load competitors for filter
        const compResponse = await fetch(`${API_BASE}/competitors`);
        allCompetitors = await compResponse.json();

        // Update competitor filter
        updateCompetitorFilter();

        filterUpdates();

    } catch (error) {
        console.error('Error loading updates:', error);
        showError('updates', 'Failed to load updates');
    }
}

function updateCompetitorFilter() {
    const filter = document.getElementById('competitor-filter');
    filter.innerHTML = '<option value="">All Competitors</option>';

    allCompetitors.forEach(comp => {
        const option = document.createElement('option');
        option.value = comp.id;
        option.textContent = comp.name;
        filter.appendChild(option);
    });
}

function filterUpdates() {
    const categoryFilter = document.getElementById('category-filter').value;
    const competitorFilter = document.getElementById('competitor-filter').value;

    let filteredUpdates = allUpdates;

    if (categoryFilter) {
        filteredUpdates = filteredUpdates.filter(update => update.category === categoryFilter);
    }

    if (competitorFilter) {
        filteredUpdates = filteredUpdates.filter(update => update.competitor_id == competitorFilter);
    }

    displayAllUpdates(filteredUpdates);
}

function displayAllUpdates(updates) {
    const container = document.getElementById('all-updates');
    container.innerHTML = '';

    if (updates.length === 0) {
        container.innerHTML = '<div class="update-item">No updates match your filters.</div>';
        return;
    }

    updates.forEach(update => {
        const updateElement = document.createElement('div');
        updateElement.className = `update-item ${update.impact_score > 0.7 ? 'high-impact' : ''}`;

        updateElement.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div style="flex: 1;">
                    <span class="update-category" style="background: ${getCategoryColor(update.category)}">
                        ${update.category.toUpperCase()}
                    </span>
                    <strong>${update.title || 'Competitor Update'}</strong>
                    <p style="margin: 8px 0; color: #666; font-size: 0.9em;">
                        ${update.content}
                    </p>
                    <small style="color: #999;">
                        📅 ${new Date(update.detected_at).toLocaleDateString()}
                        • 🌐 ${update.source}
                        • 🏢 ${getCompetitorName(update.competitor_id)}
                        • 🔗 <a href="${update.url}" target="_blank">View Source</a>
                    </small>
                </div>
                <div style="text-align: right; min-width: 80px;">
                    <div style="font-size: 0.8em; color: #666;">Impact</div>
                    <div style="font-weight: bold; font-size: 1.2em; color: ${update.impact_score > 0.7 ? '#e74c3c' : '#3498db'}">
                        ${(update.impact_score * 100).toFixed(0)}%
                    </div>
                </div>
            </div>
        `;

        container.appendChild(updateElement);
    });
}

// Load high impact alerts
async function loadAlerts() {
    try {
        showLoading('alerts');

        const response = await fetch(`${API_BASE}/updates?limit=50`);
        const updates = await response.json();

        const highImpactUpdates = updates.filter(update => update.impact_score > 0.7);

        const container = document.getElementById('alerts-list');
        container.innerHTML = '';

        if (highImpactUpdates.length === 0) {
            container.innerHTML = '<div class="update-item">🎉 No high-impact alerts! Everything looks good.</div>';
            return;
        }

        highImpactUpdates.forEach(update => {
            const updateElement = document.createElement('div');
            updateElement.className = 'update-item high-impact';

            updateElement.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div style="flex: 1;">
                        <span class="update-category" style="background: #e74c3c">
                            🚨 ${update.category.toUpperCase()}
                        </span>
                        <strong>${update.title || 'High Impact Update'}</strong>
                        <p style="margin: 8px 0; color: #666; font-size: 0.9em;">
                            ${update.content}
                        </p>
                        <small style="color: #999;">
                            📅 ${new Date(update.detected_at).toLocaleDateString()}
                            • 🌐 ${update.source}
                            • 🏢 ${getCompetitorName(update.competitor_id)}
                        </small>
                    </div>
                    <div style="text-align: right; min-width: 80px;">
                        <div style="font-size: 0.8em; color: #666;">Impact</div>
                        <div style="font-weight: bold; font-size: 1.2em; color: #e74c3c">
                            ${(update.impact_score * 100).toFixed(0)}%
                        </div>
                    </div>
                </div>
            `;

            container.appendChild(updateElement);
        });

    } catch (error) {
        console.error('Error loading alerts:', error);
        showError('alerts', 'Failed to load alerts');
    }
}

// Add new competitor
async function addNewCompetitor(event) {
    event.preventDefault();

    const formData = {
        name: document.getElementById('comp-name').value,
        website: document.getElementById('comp-website').value,
        social_handles: JSON.stringify({
            twitter: document.getElementById('comp-twitter').value
        })
    };

    try {
        const response = await fetch(`${API_BASE}/competitors`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            alert('Competitor added successfully!');
            document.getElementById('comp-name').value = '';
            document.getElementById('comp-website').value = '';
            document.getElementById('comp-twitter').value = '';
            loadCompetitors();
        } else {
            alert('Error adding competitor');
        }
    } catch (error) {
        console.error('Error adding competitor:', error);
        alert('Error adding competitor');
    }
}

// Trigger manual scraping
async function triggerScraping() {
    try {
        const button = event.target;
        const originalText = button.textContent;
        button.textContent = '🔄 Scraping...';
        button.disabled = true;

        await fetch(`${API_BASE}/scrape`, { method: 'POST' });

        // Wait a bit and refresh
        setTimeout(() => {
            loadDashboard();
            button.textContent = originalText;
            button.disabled = false;
            alert('✅ Scraping completed! Data has been updated.');
        }, 3000);

    } catch (error) {
        console.error('Error triggering scraping:', error);
        alert('❌ Error starting scraping');
        event.target.textContent = '🔄 Run Scraping Now';
        event.target.disabled = false;
    }
}

// Helper functions
function getCategoryColor(category) {
    const colors = {
        'pricing': '#e74c3c',
        'campaign': '#3498db',
        'product_release': '#2ecc71',
        'partnership': '#f39c12',
        'other': '#9b59b6'
    };
    return colors[category] || '#95a5a6';
}

function getCompetitorName(competitorId) {
    const competitor = allCompetitors.find(c => c.id == competitorId);
    return competitor ? competitor.name : 'Unknown';
}

function showLoading(section) {
    const container = document.getElementById(section === 'updates' ? 'all-updates' :
                                           section === 'competitors' ? 'competitors-list' :
                                           section === 'alerts' ? 'alerts-list' : 'recent-updates');
    if (container) {
        container.innerHTML = '<div class="update-item">Loading...</div>';
    }
}

function showError(section, message) {
    const container = document.getElementById(section === 'updates' ? 'all-updates' :
                                           section === 'competitors' ? 'competitors-list' :
                                           section === 'alerts' ? 'alerts-list' : 'recent-updates');
    if (container) {
        container.innerHTML = `<div class="update-item" style="border-left-color: #e74c3c;">❌ ${message}</div>`;
    }
}

function addCompetitor() {
    showSection('competitors');
}

// Scrape specific competitor
async function scrapeCompetitor(competitorId) {
    try {
        // This would call a specific endpoint for scraping one competitor
        alert(`Starting scrape for competitor ID: ${competitorId}`);
        await triggerScraping();
    } catch (error) {
        console.error('Error scraping competitor:', error);
        alert('Error scraping competitor');
    }
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', function() {
    loadDashboard();

    // Auto-refresh every 30 seconds
    setInterval(loadDashboard, 30000);
});