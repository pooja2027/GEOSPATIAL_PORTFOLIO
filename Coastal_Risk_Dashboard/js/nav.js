// ===== SIDEBAR NAV =====
const NAV_PAGES = [
  { id:'index',    href:'index.html',        icon:'🏠', label:'Overview',      badge:'HOME' },
  { id:'spatial',  href:'spatial.html',       icon:'🗺️', label:'Spatial Risk',  badge:'MAP' },
  { id:'comparison',href:'comparison.html',   icon:'📊', label:'Comparison',    badge:'' },
  { id:'trends',   href:'trends.html',        icon:'📈', label:'Trends',        badge:'' },
  { id:'distribution',href:'distribution.html',icon:'📉',label:'Distribution',  badge:'' },
  { id:'relationships',href:'relationships.html',icon:'🔗',label:'Relationships',badge:'' },
  { id:'composition',href:'composition.html', icon:'🧩', label:'Composition',   badge:'' },
  { id:'multivariate',href:'multivariate.html',icon:'🎯',label:'Multivariate',  badge:'' },
  { id:'methodology',href:'methodology.html', icon:'📋', label:'Methodology',   badge:'DOCS' }
];

function buildSidebar(activePage) {
  const el = document.getElementById('sidebar');
  if (!el) return;
  el.innerHTML = `
    <div class="sb-logo">
      <div class="sb-tag">GEOSPATIAL ANALYSIS</div>
      <div class="sb-title">TN <span>Coastal Risk</span></div>
      <div class="sb-sub">12 Districts · 2010–2023</div>
    </div>
    <div class="sb-section">Navigation</div>
    <nav class="sb-nav">
      ${NAV_PAGES.map(p => `
        <a href="${p.href}" class="sb-link ${p.id === activePage ? 'active' : ''}">
          <span class="sb-icon">${p.icon}</span>
          ${p.label}
          ${p.badge ? `<span class="sb-badge">${p.badge}</span>` : ''}
        </a>`).join('')}
    </nav>
    <div class="sb-footer">
      POOJA P<br/>
      B.E. Geoinformatics<br/>
      Civil Dept · Sem VI<br/>
      Data Visualization
    </div>`;
}
