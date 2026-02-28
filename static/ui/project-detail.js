/**
 * project-detail.js
 * 项目详情页逻辑：iframe 通讯、数据展示（filehashmap / projectfile）、文本弹框。
 * 仅保留渲染与数据交互，主页面 project.html 负责挂载。
 */

const ProjectDetail = (() => {
  // ─── 状态 ───
  let releaseData = null; // 完整 release 对象
  let owner = '';
  let project = '';
  let githash = '';

  // ─── DOM 引用（由 init 注入） ───
  let $detailCard, $detailMsg, $preview, $filehashSection, $projectfileSection, $modal, $modalTitle, $modalBody, $modalClose;

  // ═══════════════════════════════════════════════
  //  1. 初始化
  // ═══════════════════════════════════════════════
  function init(opts) {
    owner = opts.owner;
    project = opts.project;
    githash = opts.githash;
    $detailCard = opts.$detailCard;
    $detailMsg = opts.$detailMsg;
    $preview = opts.$preview;
    $filehashSection = opts.$filehashSection;
    $projectfileSection = opts.$projectfileSection;
    $modal = opts.$modal;
    $modalTitle = opts.$modalTitle;
    $modalBody = opts.$modalBody;
    $modalClose = opts.$modalClose;

    bindModalEvents();
    loadDetail();
  }

  // ═══════════════════════════════════════════════
  //  2. 加载数据
  // ═══════════════════════════════════════════════
  async function loadDetail() {
    if (!owner || !project || !githash) {
      $detailCard.innerHTML = '';
      FG.hint($detailMsg, '缺少参数 o/p/g，无法展示详情。');
      return;
    }
    FG.hint($detailMsg, '加载中...');
    $detailCard.innerHTML = '';

    const url = `${FG.API_BASE}/projects/${encodeURIComponent(owner)}/${encodeURIComponent(project)}/${encodeURIComponent(githash)}`;
    try {
      const data = await FG.fetchJSON(url);
      if (data.ret && data.ret !== '') throw new Error(data.ret);
      const r = data.release;
      if (!r) throw new Error('未找到对应 release');

      releaseData = r;
      renderBasicInfo(r);
      renderFilehashmap(r.filehashmap || {});
      renderProjectfile(r.projectfile);
      setupIframe(r);

      FG.hint($detailMsg, '');
    } catch (e) {
      FG.hint($detailMsg, `加载失败: ${e.message}`);
    }
  }

  // ═══════════════════════════════════════════════
  //  3. 基本信息渲染
  // ═══════════════════════════════════════════════
  function renderBasicInfo(r) {
    const fileCount = r.filehashmap ? Object.keys(r.filehashmap).length : 0;
    $detailCard.innerHTML = `
      <div class="card-title">${FG.text(r.projectname)}</div>
      <div class="detail-row"><span class="detail-key">Owner:</span>${FG.text(r.owner)}</div>
      <div class="detail-row"><span class="detail-key">Githash:</span>${FG.text(r.githash)}</div>
      <div class="detail-row"><span class="detail-key">Author:</span>${FG.text(r.author)}</div>
      <div class="detail-row"><span class="detail-key">Time:</span>${FG.text(r.time)}</div>
      <div class="detail-row"><span class="detail-key">Files:</span>${fileCount}</div>
      <button class="btn" id="toCommits">查看提交历史</button>
    `;
    document.getElementById('toCommits').addEventListener('click', () => {
      location.href = FG.linkTo('/ui/commits.html', { o: r.owner, p: r.projectname });
    });
  }

  // ═══════════════════════════════════════════════
  //  4. filehashmap 展示
  // ═══════════════════════════════════════════════
  function renderFilehashmap(map) {
    const entries = Object.entries(map);
    if (!entries.length) {
      $filehashSection.innerHTML = '<div class="hint">无文件记录</div>';
      return;
    }

    let html = `<table class="fhm-table">
      <thead><tr><th>文件路径</th><th>Hash（前 8 位）</th><th>操作</th></tr></thead><tbody>`;
    for (const [filepath, hash] of entries) {
      const rawUrl = `/raw/${encodeURIComponent(owner)}/${encodeURIComponent(project)}/${encodeURIComponent(githash)}/${filepath}`;
      const shortHash = hash ? hash.substring(0, 8) : '-';
      html += `<tr>
        <td class="fhm-path" title="${escapeAttr(filepath)}">${escapeHtml(filepath)}</td>
        <td class="fhm-hash" title="${escapeAttr(hash)}">${shortHash}</td>
        <td class="fhm-ops">
          <a class="link" href="${rawUrl}" target="_blank">查看</a>
          <a class="link" href="${rawUrl}?download=1">下载</a>
          <button class="btn btn-sm" data-action="preview-file" data-path="${escapeAttr(filepath)}" data-hash="${escapeAttr(hash)}">预览</button>
        </td>
      </tr>`;
    }
    html += '</tbody></table>';
    $filehashSection.innerHTML = html;

    // 预览按钮事件委托
    $filehashSection.addEventListener('click', async (e) => {
      const btn = e.target.closest('[data-action="preview-file"]');
      if (!btn) return;
      const path = btn.dataset.path;
      const hash = btn.dataset.hash;
      await previewFileContent(path, hash);
    });
  }

  async function previewFileContent(filepath, hash) {
    const rawUrl = `/raw/${encodeURIComponent(owner)}/${encodeURIComponent(project)}/${encodeURIComponent(githash)}/${filepath}`;
    try {
      const res = await fetch(rawUrl);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const contentType = res.headers.get('content-type') || '';
      if (contentType.startsWith('image/')) {
        showModal(`预览: ${filepath}`, `<img src="${rawUrl}" style="max-width:100%;max-height:70vh;" />`);
      } else {
        const text = await res.text();
        showModal(`预览: ${filepath}`, `<pre class="modal-pre">${escapeHtml(text)}</pre>`);
      }
    } catch (e) {
      showModal(`预览失败: ${filepath}`, `<div class="hint">${escapeHtml(e.message)}</div>`);
    }
  }

  // ═══════════════════════════════════════════════
  //  5. projectfile 展开/折叠视图
  // ═══════════════════════════════════════════════
  function renderProjectfile(projectfile) {
    if (!projectfile) {
      $projectfileSection.innerHTML = '<div class="hint">无 projectfile 数据</div>';
      return;
    }
    // projectfile 包含 flow/config/nodes/record 四个 JSON
    const keys = Object.keys(projectfile);
    let html = '<div class="pf-tree">';
    for (const key of keys) {
      const val = projectfile[key];
      const id = 'pf-' + key;
      const jsonStr = typeof val === 'string' ? val : JSON.stringify(val, null, 2);
      const preview = truncate(jsonStr, 120);
      html += `
        <div class="pf-node">
          <div class="pf-header" data-toggle="${id}">
            <span class="pf-arrow">&#9654;</span>
            <span class="pf-key">${escapeHtml(key)}</span>
            <span class="pf-preview">${escapeHtml(preview)}</span>
          </div>
          <div class="pf-body" id="${id}" style="display:none;">
            <pre class="pf-json">${escapeHtml(jsonStr)}</pre>
            <button class="btn btn-sm pf-expand-btn" data-action="expand-json" data-key="${escapeAttr(key)}">在弹框中查看</button>
          </div>
        </div>`;
    }
    html += '</div>';
    $projectfileSection.innerHTML = html;

    // 折叠事件委托
    $projectfileSection.addEventListener('click', (e) => {
      const header = e.target.closest('[data-toggle]');
      if (header) {
        const target = document.getElementById(header.dataset.toggle);
        if (target) {
          const isHidden = target.style.display === 'none';
          target.style.display = isHidden ? 'block' : 'none';
          header.querySelector('.pf-arrow').innerHTML = isHidden ? '&#9660;' : '&#9654;';
        }
        return;
      }
      const expandBtn = e.target.closest('[data-action="expand-json"]');
      if (expandBtn) {
        const key = expandBtn.dataset.key;
        const val = projectfile[key];
        const jsonStr = typeof val === 'string' ? val : JSON.stringify(val, null, 2);
        showModal(`projectfile.${key}`, `<pre class="modal-pre">${escapeHtml(jsonStr)}</pre>`);
      }
    });
  }

  // ═══════════════════════════════════════════════
  //  6. 大段文本弹框
  // ═══════════════════════════════════════════════
  function showModal(title, bodyHtml) {
    $modalTitle.textContent = title;
    $modalBody.innerHTML = bodyHtml;
    $modal.classList.add('show');
    document.body.style.overflow = 'hidden';
  }

  function hideModal() {
    $modal.classList.remove('show');
    document.body.style.overflow = '';
  }

  function bindModalEvents() {
    $modalClose.addEventListener('click', hideModal);
    $modal.addEventListener('click', (e) => {
      if (e.target === $modal) hideModal();
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') hideModal();
    });
  }

  // ═══════════════════════════════════════════════
  //  7. iframe 通讯（双向事件桥接）
  // ═══════════════════════════════════════════════

  /**
   * 对接 connectAPI.js 的 fromdfgsiframe 模式。
   * iframe 内 board 通过 window.parent.postMessage 发送命令，
   * 此处监听并响应，模拟 extension.js 的 recieveMessage 协议。
   */
  function setupIframe(r) {
    $preview.src = '/data-flow-graph-node/board/index.html?fromdfgsiframe=1';

    // 从 projectfile 中提取 config/nodes/record
    const pf = r.projectfile || {};
    const config = pf.config || {};
    const nodes = pf.nodes || [];
    const record = pf.record || [];

    // 监听来自 iframe 的消息
    window.addEventListener('message', (event) => {
      const message = event.data;
      if (!message || !message.command) return;
      handleIframeMessage(message, { config, nodes, record });
    });
  }

  /**
   * 处理 iframe 发来的命令，参考 extension.js recieveMessage 协议
   */
  function handleIframeMessage(message, data) {
    const iframe = $preview;
    const iframeWindow = iframe.contentWindow;
    if (!iframeWindow) return;

    const handlers = {
      requestConfig() {
        iframeWindow.postMessage({ command: 'config', content: data.config }, '*');
      },
      requestNodes() {
        iframeWindow.postMessage({ command: 'nodes', content: data.nodes }, '*');
      },
      requestRecord() {
        iframeWindow.postMessage({ command: 'record', content: data.record.current }, '*');
      },
      showFile(msg) {
        // 尝试从 filehashmap 中匹配文件并展示
        const filename = msg.filename || msg.file || '';
        if (releaseData && releaseData.filehashmap) {
          const hash = releaseData.filehashmap[filename];
          if (hash) {
            previewFileContent(filename, hash);
            return;
          }
        }
        showModal('文件: ' + filename, '<div class="hint">服务器上未找到该文件</div>');
      },
      showText(msg) {
        const text = msg.text || '';
        showModal('文本输出', `<pre class="modal-pre">${escapeHtml(text)}</pre>`);
      },
      showInfo(msg) {
        const text = msg.text || '';
        showModal('提示', `<div style="padding:12px;">${escapeHtml(text)}</div>`);
      },
      prompt(msg) {
        const result = window.prompt(msg.show || '', msg.text || '');
        iframeWindow.postMessage({ command: 'prompt', content: result }, '*');
      },
      editCurrentLine() { /* 服务器端只读，忽略 */ },
      readSVGFile() { /* 服务器端只读，忽略 */ },
      requestCustom() {
        iframeWindow.postMessage({ command: 'custom', content: { operate: [] } }, '*');
      },
    };

    if (message.command in handlers) {
      handlers[message.command](message);
    } else {
      console.log('[project-detail] unhandled iframe message:', message);
    }
  }

  // ═══════════════════════════════════════════════
  //  工具函数
  // ═══════════════════════════════════════════════
  function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function escapeAttr(str) {
    return escapeHtml(str);
  }

  function truncate(str, maxLen) {
    if (!str) return '';
    str = str.replace(/\n/g, ' ');
    return str.length > maxLen ? str.substring(0, maxLen) + '...' : str;
  }

  return { init, showModal, hideModal };
})();
