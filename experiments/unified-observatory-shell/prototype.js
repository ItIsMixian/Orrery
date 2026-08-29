(() => {
  'use strict';

  const state = { mode: 'dynamic', team: false, view: 'overview', toastTimer: null };
  const body = document.body;
  const pages = [...document.querySelectorAll('[data-page]')];
  const navItems = [...document.querySelectorAll('[data-view]')];
  const modeButtons = [...document.querySelectorAll('[data-mode]')];
  const menuButton = document.getElementById('menu-button');
  const scrim = document.getElementById('scrim');
  const workspace = document.getElementById('workspace');
  const toast = document.getElementById('toast');

  function announce(message) {
    window.clearTimeout(state.toastTimer);
    toast.textContent = message;
    toast.classList.add('show');
    state.toastTimer = window.setTimeout(() => toast.classList.remove('show'), 2600);
  }

  function setMenu(open) {
    body.classList.toggle('nav-open', open);
    menuButton.setAttribute('aria-expanded', String(open));
    menuButton.setAttribute('aria-label', open ? '关闭导航' : '打开导航');
  }

  function showView(view, { focus = true } = {}) {
    const exists = pages.some(page => page.dataset.page === view);
    state.view = exists ? view : 'overview';
    pages.forEach(page => page.classList.toggle('active', page.dataset.page === state.view));
    navItems.forEach(item => {
      const active = item.dataset.view === state.view;
      item.classList.toggle('active', active);
      if (active) item.setAttribute('aria-current', 'page');
      else item.removeAttribute('aria-current');
    });
    if (location.hash !== `#/${state.view}`) history.replaceState(null, '', `#/${state.view}`);
    setMenu(false);
    if (focus) workspace.focus({ preventScroll: true });
  }

  function renderMode() {
    const dynamic = state.mode === 'dynamic';
    modeButtons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.mode === state.mode)));
    const strip = document.getElementById('boundary-strip');
    strip.innerHTML = dynamic
      ? `<b>DYNAMIC LOCAL</b><span>Personal zero-network</span><span>Default no console</span><span>Team ${state.team ? 'opted in' : 'off'}</span>`
      : '<b>STATIC READ-ONLY</b><span>No server / cookie / control</span><span>Precomputed views only</span><span>Team unavailable</span>';
    document.getElementById('socket-label').textContent = dynamic ? '127.0.0.1 · helpers supervised' : 'file: · no runtime';
    document.getElementById('network-signal').textContent = state.team && dynamic ? 'Team opt-in' : 'Zero-network';
    document.getElementById('provider-button').disabled = !dynamic;
    if (!dynamic && state.team) {
      state.team = false;
      renderTeam();
    }
    const teamButton = document.getElementById('team-toggle');
    teamButton.disabled = !dynamic;
    if (!dynamic) teamButton.textContent = '静态模式不可用';
    else teamButton.textContent = state.team ? '关闭 synthetic Team' : '显式开启 synthetic Team';
    document.querySelectorAll('.maintenance-preflight').forEach(button => { button.disabled = !dynamic; });
    document.getElementById('preflight-panel').hidden = true;
  }

  function renderTeam() {
    const on = state.team && state.mode === 'dynamic';
    document.getElementById('team-badge').textContent = on ? 'TEAM OPTED IN' : 'TEAM OFF';
    document.getElementById('team-badge').classList.toggle('safe', on);
    document.getElementById('team-title-state').textContent = on ? 'Synthetic Team Mode 已显式开启' : 'Team Mode 未开启';
    document.getElementById('team-copy').textContent = on
      ? 'Metadata-only projection available; central can view and send requests, never execute.'
      : 'Personal Mode 保持 zero-network；没有发现、Host、同步或 heartbeat。';
    document.getElementById('team-nav-state').textContent = on ? 'Request-only' : 'Opt-in';
    document.getElementById('team-cap-state').textContent = on ? 'REQUEST-ONLY' : 'OFF';
    document.getElementById('team-toggle').textContent = state.mode === 'static' ? '静态模式不可用' : (on ? '关闭 synthetic Team' : '显式开启 synthetic Team');
    renderMode();
  }

  navItems.forEach(button => button.addEventListener('click', () => showView(button.dataset.view)));
  document.querySelectorAll('[data-jump]').forEach(button => button.addEventListener('click', () => showView(button.dataset.jump)));
  modeButtons.forEach(button => button.addEventListener('click', () => {
    state.mode = button.dataset.mode;
    renderMode();
    announce(state.mode === 'static' ? '静态只读：没有服务、cookie 或控制 capability。' : '本地动态：一个可见 URL；隐藏 helper 由 synthetic supervisor 管理。');
  }));

  menuButton.addEventListener('click', () => setMenu(!body.classList.contains('nav-open')));
  scrim.addEventListener('click', () => setMenu(false));
  window.addEventListener('keydown', event => { if (event.key === 'Escape') setMenu(false); });
  window.addEventListener('hashchange', () => showView(location.hash.replace(/^#\/?/, ''), { focus: false }));

  document.getElementById('team-toggle').addEventListener('click', () => {
    if (state.mode !== 'dynamic') {
      announce('Team 在静态模式保持 Unavailable。');
      return;
    }
    state.team = !state.team;
    renderTeam();
    announce(state.team ? 'Synthetic Team 已开启：metadata-only，central request-only。' : 'Synthetic Team 已关闭：恢复 Personal zero-network。');
  });

  document.getElementById('provider-button').addEventListener('click', () => {
    announce(state.mode === 'dynamic' ? 'Broker capability 未配置；没有发送网络请求。' : '静态模式没有 Provider 设置。');
  });
  document.getElementById('authority-check').addEventListener('click', () => announce('A3 contract 仍 Unavailable；shell 与其他 consumer 保持 operational。'));
  document.getElementById('diagnostics-button').addEventListener('click', () => announce('Synthetic diagnostics：默认无控制台；runtime log 保持 Git-private，本原型不打开文件。'));

  const search = document.getElementById('doc-search');
  search.addEventListener('input', () => {
    const term = search.value.trim().toLowerCase();
    document.querySelectorAll('[data-search-text]').forEach(row => {
      row.hidden = term !== '' && !row.dataset.searchText.toLowerCase().includes(term) && !row.textContent.toLowerCase().includes(term);
    });
  });
  document.querySelectorAll('[data-search-text]').forEach(row => row.addEventListener('click', () => announce('Synthetic document row selected; no repository document was opened.')));

  const preflight = document.getElementById('preflight-panel');
  document.querySelectorAll('.maintenance-preflight').forEach(button => button.addEventListener('click', () => {
    if (state.mode !== 'dynamic') return;
    preflight.hidden = false;
    preflight.scrollIntoView({ block: 'nearest', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
    document.getElementById('cancel-preflight').focus({ preventScroll: true });
  }));
  document.getElementById('cancel-preflight').addEventListener('click', () => { preflight.hidden = true; announce('Synthetic preflight cancelled.'); });
  document.getElementById('confirm-preflight').addEventListener('click', () => {
    preflight.hidden = true;
    announce('Synthetic receipt recorded. No filesystem action; branch and commit preserved.');
  });

  const initial = location.hash.replace(/^#\/?/, '') || 'overview';
  showView(initial, { focus: false });
  renderTeam();
})();
