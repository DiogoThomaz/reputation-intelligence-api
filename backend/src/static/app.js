(() => {
  // ajuste se necessário
  const API_BASE = (new URLSearchParams(location.search).get('api') || 'http://187.127.3.91:8000').replace(/\/$/, '');
  document.getElementById('apiBaseLabel').textContent = API_BASE;

  const el = (id) => document.getElementById(id);
  const btnStart = el('btnStart');
  const btnStop = el('btnStop');
  const btnClear = el('btnClear');
  const list = el('list');

  const statusBox = el('statusBox');
  const statusTitle = el('statusTitle');
  const statusSub = el('statusSub');
  const searchIdPill = el('searchIdPill');

  const kpis = el('kpis');
  const kTotal = el('kTotal');
  const kPS = el('kPS');
  const kUpdated = el('kUpdated');

  let pollTimer = null;
  let searchId = null;

  const fmtTime = () => new Date().toLocaleTimeString();

  async function api(path, opts = {}) {
    const res = await fetch(API_BASE + path, {
      headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) },
      ...opts,
    });
    if (!res.ok) {
      const t = await res.text().catch(() => '');
      throw new Error(`HTTP ${res.status} ${res.statusText} :: ${t}`);
    }
    return res.json();
  }

  function sentimentClass(s) {
    if (s === 'positivo') return 'pos';
    if (s === 'negativo') return 'neg';
    return 'neu';
  }

  function renderItems(items) {
    list.innerHTML = '';
    for (const it of items) {
      const div = document.createElement('div');
      div.className = 'item';

      const sent = (it.sentiment || 'neutro').toLowerCase();
      const tags = Array.isArray(it.intent_tags) ? it.intent_tags : [];

      div.innerHTML = `
        <div class="top">
          <div class="badge">${it.source || ''} • ${it.date || ''} • ⭐ ${it.rating ?? ''}</div>
          <div class="pill sent ${sentimentClass(sent)}">${sent}</div>
        </div>
        <div class="tags">
          ${tags.map(t => `<span class="tag">${t}</span>`).join('')}
        </div>
        <div class="txt">${(it.comment_text || '').replace(/</g,'&lt;')}</div>
      `;
      list.appendChild(div);
    }

    if (!items.length) {
      const empty = document.createElement('div');
      empty.className = 'item';
      empty.innerHTML = `<div class="badge">Sem itens ainda. Aguarde alguns segundos…</div>`;
      list.appendChild(empty);
    }
  }

  async function refresh() {
    if (!searchId) return;

    // summary
    const s = await api(`/search/${encodeURIComponent(searchId)}`);
    statusTitle.textContent = `Status: ${s.status}`;

    const total = (s.summary && s.summary.total_items) || 0;
    const bySource = (s.summary && s.summary.by_source) || {};

    kTotal.textContent = total;
    kPS.textContent = bySource.play_store || 0;
    kUpdated.textContent = fmtTime();

    // items
    const items = await api(`/reviews?search_id=${encodeURIComponent(searchId)}&source=play_store`);
    // mostra os mais recentes primeiro
    renderItems(items.slice().reverse().slice(0, 60));

    statusSub.textContent = `Atualizado às ${fmtTime()} • ${items.length} itens retornados`;
  }

  function startPolling() {
    stopPolling();
    pollTimer = setInterval(() => refresh().catch(err => {
      statusSub.textContent = `Erro: ${err.message}`;
    }), 1500);
    btnStop.disabled = false;
  }

  function stopPolling() {
    if (pollTimer) clearInterval(pollTimer);
    pollTimer = null;
    btnStop.disabled = true;
  }

  btnStart.addEventListener('click', async (e) => {
    e.preventDefault();

    btnStart.disabled = true;
    statusBox.style.display = 'flex';
    kpis.style.display = 'grid';
    statusTitle.textContent = 'Criando pesquisa…';
    statusSub.textContent = 'Enviando request…';

    const payload = {
      company_name: el('companyName').value.trim() || 'Empresa',
      playstore_app_id: el('appId').value.trim() || null,
      max_reviews: Number(el('maxReviews').value || 30),
    };

    try {
      const r = await api('/search', { method: 'POST', body: JSON.stringify(payload) });
      searchId = r.search_id;
      searchIdPill.textContent = searchId;
      statusTitle.textContent = 'Processando…';
      statusSub.textContent = 'Coletando e classificando avaliações em background.';

      await refresh();
      startPolling();
    } catch (err) {
      statusTitle.textContent = 'Falha ao iniciar';
      statusSub.textContent = err.message;
    } finally {
      btnStart.disabled = false;
    }
  });

  btnStop.addEventListener('click', (e) => {
    e.preventDefault();
    stopPolling();
    statusSub.textContent = 'Atualização pausada.';
  });

  btnClear.addEventListener('click', (e) => {
    e.preventDefault();
    stopPolling();
    searchId = null;
    searchIdPill.textContent = '—';
    statusBox.style.display = 'none';
    kpis.style.display = 'none';
    list.innerHTML = '';
  });

  // first paint
  renderItems([]);
})();
