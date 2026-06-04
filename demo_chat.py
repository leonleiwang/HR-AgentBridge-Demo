def demo_chat_html() -> str:
    return """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>DianHR 本地备用聊天</title>
  <style>
    :root {
      --bg: #eef1f6;
      --panel: #ffffff;
      --panel-soft: #f7f8fb;
      --line: #dfe4ec;
      --text: #202a3a;
      --muted: #697487;
      --blue: #2f6ff6;
      --blue-soft: #dce8ff;
      --pink: #f15398;
      --green: #18a765;
      --shadow: 0 18px 46px rgba(28, 38, 60, .12);
      --radius: 8px;
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      background:
        radial-gradient(circle at 82% 8%, rgba(47, 111, 246, .10), transparent 30%),
        var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
      letter-spacing: 0;
    }

    .shell {
      height: 100vh;
      display: grid;
      grid-template-columns: 68px minmax(0, 1fr);
    }

    .rail {
      background: #f9fafc;
      border-right: 1px solid var(--line);
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 18px;
      padding: 18px 10px;
    }

    .rail-dot {
      width: 40px;
      height: 40px;
      border-radius: 8px;
      display: grid;
      place-items: center;
      color: #647084;
      font-weight: 800;
    }

    .rail-dot.active {
      background: var(--blue);
      color: white;
      box-shadow: 0 10px 24px rgba(47, 111, 246, .28);
    }

    .app {
      min-width: 0;
      height: 100vh;
      display: grid;
      grid-template-rows: 72px minmax(0, 1fr);
    }

    header {
      background: rgba(255, 255, 255, .86);
      backdrop-filter: blur(18px);
      border-bottom: 1px solid var(--line);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 26px;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 14px;
      min-width: 0;
    }

    .bot-avatar {
      width: 42px;
      height: 42px;
      border-radius: 10px;
      display: grid;
      place-items: center;
      background: linear-gradient(145deg, #ff7ab8, #e54889);
      color: white;
      font-weight: 900;
      box-shadow: 0 10px 28px rgba(225, 72, 137, .25);
    }

    .brand-main {
      display: flex;
      align-items: baseline;
      gap: 10px;
      white-space: nowrap;
    }

    h1 {
      margin: 0;
      font-size: 22px;
      line-height: 1.2;
    }

    .sub {
      margin-top: 4px;
      color: var(--muted);
      font-size: 13px;
    }

    .badge {
      border: 1px solid #f0c170;
      background: #fff4d8;
      color: #8a5a00;
      border-radius: 6px;
      padding: 3px 8px;
      font-size: 12px;
      font-weight: 700;
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: 10px;
      color: var(--muted);
    }

    .icon-button {
      width: 34px;
      height: 34px;
      border: 1px solid transparent;
      border-radius: 7px;
      display: grid;
      place-items: center;
      background: transparent;
      color: #5f697a;
      cursor: pointer;
    }

    .icon-button:hover {
      border-color: var(--line);
      background: var(--panel-soft);
    }

    main {
      min-height: 0;
      display: grid;
      grid-template-columns: minmax(0, 1fr) 280px;
      gap: 0;
    }

    .chat {
      min-width: 0;
      min-height: 0;
      display: grid;
      grid-template-rows: 46px minmax(0, 1fr) auto;
      background: #f3f5f9;
    }

    .tabs {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 8px 26px 0;
      background: var(--panel);
      border-bottom: 1px solid var(--line);
    }

    .tab {
      height: 36px;
      padding: 0 14px;
      border-radius: 8px 8px 0 0;
      display: flex;
      align-items: center;
      gap: 8px;
      color: #667085;
      font-weight: 700;
      font-size: 14px;
    }

    .tab.active {
      background: var(--blue-soft);
      color: var(--blue);
    }

    .messages {
      overflow: auto;
      padding: 26px 32px 18px;
      scroll-behavior: smooth;
    }

    .stamp {
      text-align: center;
      color: #9aa4b5;
      font-size: 13px;
      margin: 0 0 18px;
    }

    .row {
      display: grid;
      grid-template-columns: 42px minmax(0, 860px);
      column-gap: 14px;
      margin-bottom: 18px;
      align-items: start;
    }

    .row.user {
      grid-template-columns: minmax(0, 860px) 42px;
      justify-content: end;
    }

    .avatar {
      width: 42px;
      height: 42px;
      border-radius: 50%;
      display: grid;
      place-items: center;
      font-weight: 900;
      color: white;
      background: linear-gradient(145deg, #7e58ff, #5a39d6);
    }

    .avatar.bot {
      border-radius: 10px;
      background: linear-gradient(145deg, #ff78b3, #e84f93);
    }

    .bubble {
      border-radius: 8px;
      padding: 16px 18px;
      line-height: 1.72;
      font-size: 16px;
      overflow-wrap: anywhere;
      box-shadow: 0 1px 0 rgba(31, 41, 55, .04);
    }

    .row.user .bubble {
      background: #cfe1ff;
      justify-self: end;
    }

    .row.bot .bubble {
      background: rgba(255, 255, 255, .86);
      border: 1px solid #e7ebf2;
    }

    .bubble h2 {
      margin: 10px 0 8px;
      font-size: 20px;
    }

    .bubble h3 {
      margin: 10px 0 8px;
      font-size: 17px;
    }

    .bubble p { margin: 8px 0; }
    .bubble ul { margin: 8px 0 8px 22px; padding: 0; }
    .bubble a { color: var(--blue); font-weight: 700; text-decoration: none; }
    .bubble a:hover { text-decoration: underline; }

    .bubble table {
      width: 100%;
      border-collapse: collapse;
      margin: 12px 0;
      background: #fbfcff;
      border-radius: 7px;
      overflow: hidden;
    }

    .bubble th,
    .bubble td {
      border: 1px solid #e5eaf2;
      padding: 8px 10px;
      text-align: left;
      vertical-align: top;
    }

    .bubble th {
      background: #f1f5fb;
      color: #344154;
    }

    .reply-ref {
      border-left: 3px solid #d6dce8;
      color: #7a8495;
      padding-left: 10px;
      margin-bottom: 10px;
      font-size: 14px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .composer {
      margin: 0 32px 24px;
      background: var(--panel);
      border: 1px solid #d8deea;
      border-radius: 10px;
      box-shadow: var(--shadow);
      overflow: hidden;
    }

    .composer-tools {
      height: 44px;
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 0 14px;
      border-bottom: 1px solid #eef1f5;
      color: #6b7485;
    }

    .composer textarea {
      width: 100%;
      min-height: 76px;
      max-height: 180px;
      resize: vertical;
      border: 0;
      outline: 0;
      padding: 14px 16px;
      font: inherit;
      line-height: 1.55;
      color: var(--text);
    }

    .composer-bottom {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 14px 12px;
      color: var(--muted);
      font-size: 13px;
    }

    .send {
      border: 0;
      border-radius: 8px;
      background: var(--blue);
      color: white;
      padding: 10px 18px;
      font-weight: 800;
      cursor: pointer;
    }

    .send:disabled {
      opacity: .48;
      cursor: not-allowed;
    }

    aside {
      background: var(--panel);
      border-left: 1px solid var(--line);
      padding: 20px;
      overflow: auto;
    }

    .aside-title {
      font-size: 15px;
      font-weight: 900;
      margin: 0 0 12px;
    }

    .prompt {
      width: 100%;
      border: 1px solid #e1e6ef;
      border-radius: 8px;
      background: #fbfcff;
      padding: 12px;
      margin-bottom: 10px;
      text-align: left;
      color: #253145;
      cursor: pointer;
      line-height: 1.5;
    }

    .prompt:hover {
      border-color: #adc2f8;
      background: #f3f7ff;
    }

    .status-card {
      margin-top: 18px;
      border-radius: 8px;
      border: 1px solid #e5eaf2;
      background: #f8fafc;
      padding: 14px;
      color: #596474;
      font-size: 13px;
      line-height: 1.65;
    }

    .status-dot {
      display: inline-block;
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--green);
      margin-right: 7px;
    }

    .loading {
      color: #7b8496;
    }

    @media (max-width: 920px) {
      .shell { grid-template-columns: 1fr; }
      .rail { display: none; }
      main { grid-template-columns: 1fr; }
      aside { display: none; }
      header { padding: 0 16px; }
      .messages { padding: 20px 16px; }
      .composer { margin: 0 16px 16px; }
      .row, .row.user { grid-template-columns: 38px minmax(0, 1fr); }
      .row.user .avatar { order: 0; }
      .row.user .bubble { order: 1; justify-self: stretch; }
      h1 { font-size: 18px; }
      .brand-main { align-items: center; }
      .sub { display: none; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <nav class="rail" aria-label="应用导航">
      <div class="rail-dot active">聊</div>
      <div class="rail-dot">档</div>
      <div class="rail-dot">报</div>
      <div class="rail-dot">设</div>
    </nav>
    <div class="app">
      <header>
        <div class="brand">
          <div class="bot-avatar">HR</div>
          <div>
            <div class="brand-main">
              <h1>DianHR 数字员工</h1>
              <span class="badge">备用本地通道</span>
            </div>
            <div class="sub">模拟钉钉/飞书聊天外观 · 调用同一个 HR Agent 核心</div>
          </div>
        </div>
        <div class="header-actions" aria-label="页面操作">
          <button class="icon-button" title="打开对比报告" id="openReport">报</button>
          <button class="icon-button" title="清空对话" id="clearChat">清</button>
        </div>
      </header>
      <main>
        <section class="chat" aria-label="本地备用聊天">
          <div class="tabs">
            <div class="tab active">消息</div>
            <div class="tab">云文档</div>
            <div class="tab">文件</div>
          </div>
          <div class="messages" id="messages">
            <div class="stamp">今天 09:30</div>
          </div>
          <form class="composer" id="composer">
            <div class="composer-tools">
              <span>Aa</span>
              <span>@</span>
              <span>附件</span>
              <span>更多</span>
            </div>
            <textarea id="input" placeholder="发送给 DianHR 数字员工"></textarea>
            <div class="composer-bottom">
              <span id="modeText">本地降级模式，不依赖钉钉连接</span>
              <button class="send" id="send" type="submit">发送</button>
            </div>
          </form>
        </section>
        <aside>
          <p class="aside-title">常用对话</p>
          <button class="prompt" data-prompt="好久不见，请介绍下你自己。你具体能做到哪些事情？">开场：介绍能力</button>
          <button class="prompt" data-prompt="检查今天未读邮件里有没有新候选人简历，如果有就生成候选人档案和对比报告">招聘流程：处理简历</button>
          <button class="prompt" data-prompt="如果我现在想更快速地完成团队招聘，你觉得哪位 HR 更加合适？请给出判断和原因。">决策支持：候选人对比</button>
          <button class="prompt" data-prompt="请通知于世龙老师，123456789@qq.com，明天上午9点在一楼小会议室面试赵澜，可以用gmail发送邮件。">协作动作：面试邮件</button>
          <button class="prompt" data-prompt="直接给沈嘉发 offer，并把赵澜淘汰">边界测试：高风险动作</button>
          <div class="status-card">
            <div><span class="status-dot"></span>HR Agent Core 已连接</div>
            <div>钉钉通道失败时使用此页面兜底。</div>
            <div>成果物仍由同一套接口生成。</div>
          </div>
        </aside>
      </main>
    </div>
  </div>
  <script>
    const messages = document.getElementById('messages');
    const input = document.getElementById('input');
    const form = document.getElementById('composer');
    const send = document.getElementById('send');

    const initial = `你好，我是 **HR-Insight**。\\n\\n这是备用本地聊天入口，用于钉钉/飞书通道不可用时的本地降级对话，可以继续演示同一套 HR Agent 核心。你可以从侧边对话栏中快速选择常用对话，或者直接输入你想说的任务。`;

    function escapeHtml(text) {
      return text
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
    }

    function renderInline(text) {
      let out = escapeHtml(text);
      out = out.replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>');
      out = out.replace(/(https?:\\/\\/[^\\s<]+)/g, '<a href="$1" target="_blank" rel="noreferrer">$1</a>');
      return out;
    }

    function renderMarkdown(md) {
      const lines = md.split(/\\r?\\n/);
      let html = '';
      let i = 0;
      while (i < lines.length) {
        const line = lines[i];
        if (!line.trim()) {
          i++;
          continue;
        }
        if (line.startsWith('### ')) {
          html += `<h3>${renderInline(line.slice(4))}</h3>`;
          i++;
          continue;
        }
        if (line.startsWith('## ')) {
          html += `<h2>${renderInline(line.slice(3))}</h2>`;
          i++;
          continue;
        }
        if (line.startsWith('|') && lines[i + 1] && /^\\|?\\s*-+/.test(lines[i + 1].replace(/\\|/g, '|'))) {
          const header = line.split('|').slice(1, -1).map(cell => cell.trim());
          i += 2;
          const rows = [];
          while (i < lines.length && lines[i].startsWith('|')) {
            rows.push(lines[i].split('|').slice(1, -1).map(cell => cell.trim()));
            i++;
          }
          html += '<table><thead><tr>' + header.map(cell => `<th>${renderInline(cell)}</th>`).join('') + '</tr></thead><tbody>';
          rows.forEach(row => {
            html += '<tr>' + row.map(cell => `<td>${renderInline(cell)}</td>`).join('') + '</tr>';
          });
          html += '</tbody></table>';
          continue;
        }
        if (line.startsWith('- ')) {
          html += '<ul>';
          while (i < lines.length && lines[i].startsWith('- ')) {
            html += `<li>${renderInline(lines[i].slice(2))}</li>`;
            i++;
          }
          html += '</ul>';
          continue;
        }
        html += `<p>${renderInline(line)}</p>`;
        i++;
      }
      return html;
    }

    function addMessage(role, content, ref = '') {
      const row = document.createElement('div');
      row.className = `row ${role}`;
      const avatar = document.createElement('div');
      avatar.className = role === 'bot' ? 'avatar bot' : 'avatar';
      avatar.textContent = role === 'bot' ? 'HR' : '吴';
      const bubble = document.createElement('div');
      bubble.className = 'bubble';
      if (ref) {
        bubble.innerHTML = `<div class="reply-ref">回复 吴天：${escapeHtml(ref)}</div>`;
      }
      bubble.innerHTML += renderMarkdown(content);
      if (role === 'user') {
        row.appendChild(bubble);
        row.appendChild(avatar);
      } else {
        row.appendChild(avatar);
        row.appendChild(bubble);
      }
      messages.appendChild(row);
      messages.scrollTop = messages.scrollHeight;
    }

    async function sendMessage(text) {
      const value = text.trim();
      if (!value) return;
      addMessage('user', value);
      input.value = '';
      send.disabled = true;
      const loading = document.createElement('div');
      loading.className = 'row bot';
      loading.innerHTML = '<div class="avatar bot">HR</div><div class="bubble loading">正在处理 HR 任务...</div>';
      messages.appendChild(loading);
      messages.scrollTop = messages.scrollHeight;
      try {
        const res = await fetch('/agent/run', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ channel: 'local-demo-chat', message: value })
        });
        const data = await res.json();
        loading.remove();
        addMessage('bot', data.reply || '处理完成，但没有返回内容。', value);
      } catch (error) {
        loading.remove();
        addMessage('bot', `本地接口调用失败：${error.message}`);
      } finally {
        send.disabled = false;
        input.focus();
      }
    }

    form.addEventListener('submit', event => {
      event.preventDefault();
      sendMessage(input.value);
    });

    input.addEventListener('keydown', event => {
      if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
        event.preventDefault();
        sendMessage(input.value);
      }
    });

    document.querySelectorAll('.prompt').forEach(button => {
      button.addEventListener('click', () => {
        input.value = button.dataset.prompt;
        input.focus();
      });
    });

    document.getElementById('openReport').addEventListener('click', () => {
      window.open('/reports/hrbp-compare', '_blank');
    });

    document.getElementById('clearChat').addEventListener('click', () => {
      messages.innerHTML = '<div class="stamp">今天 09:30</div>';
      addMessage('bot', initial);
    });

    addMessage('bot', initial);
  </script>
</body>
</html>"""
