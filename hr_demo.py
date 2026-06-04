import html
import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


BASE_PUBLIC_URL = os.getenv("BASE_PUBLIC_URL", "http://localhost:8000").rstrip("/")
ARTIFACT_DIR = Path(os.getenv("ARTIFACT_DIR", "generated-artifacts"))


@dataclass
class Candidate:
    candidate_id: str
    name: str
    gender: str
    birth_year: int
    role: str
    city: str
    phone_masked: str
    email: str
    salary: str
    availability: str
    education: str
    company_background: str
    team_size: str
    work_summary: str
    strengths: List[str]
    concerns: List[str]
    scores: Dict[str, int]
    interview_quote: str
    decision: str
    decision_label: str


@dataclass
class HRResult:
    task_type: str
    reply: str
    artifacts: Dict[str, str]
    requires_confirmation: bool = False


CANDIDATES: Dict[str, Candidate] = {
    "liuchen": Candidate(
        candidate_id="liuchen",
        name="沈嘉",
        gender="男",
        birth_year=1998,
        role="HRBP",
        city="北京",
        phone_masked="138****6429",
        email="shen.jia.hr@example.com",
        salary="10k-14k",
        availability="两周内",
        education="北京交通大学 工商管理本科",
        company_background="企业服务创业公司",
        team_size="150人",
        work_summary="4年 HRBP 经验，参与企业服务团队从岗位画像、渠道筛选、面试协调到 Offer 跟进的完整招聘流程。",
        strengths=[
            "招聘流程参与完整，能较快承接紧急补位任务",
            "候选人沟通和面试推进能力强",
            "薪资预期相对可控，谈判空间较清晰",
            "业务理解速度快，适合变化较快的团队环境",
        ],
        concerns=[
            "目标行业流程经验不足，需要入职后补齐业务 SOP",
            "长期稳定性需进一步确认，避免快速补位后短期流动",
        ],
        scores={
            "面试表达": 90,
            "招聘实操": 88,
            "业务理解": 84,
            "到岗速度": 86,
            "成本可控": 82,
            "稳定/合规": 72,
        },
        interview_quote=(
            "沈嘉的沟通推进能力比较强，对岗位需求拆解也比较快。"
            "如果目标是尽快把 HRBP 岗位补上，他可以较快进入状态；但目标行业的流程细节需要有人带一段时间。"
        ),
        decision="建议录用",
        decision_label="推荐录用",
    ),
    "wanglin": Candidate(
        candidate_id="wanglin",
        name="赵澜",
        gender="女",
        birth_year=1997,
        role="HRBP",
        city="北京",
        phone_masked="135****7816",
        email="zhao.lan.hr@example.com",
        salary="12k-15k",
        availability="1个月内",
        education="苏州大学 人力资源管理本科",
        company_background="美团到家人力运营中心",
        team_size="260人",
        work_summary="5年 HRBP 与人力运营协作经验，长期服务本地生活业务线，熟悉编制审批、规范入职和跨部门协同流程。",
        strengths=[
            "平台型业务背景更贴近复杂组织协同",
            "流程意识和风险边界更成熟，适合规范化组织",
            "学历和工作经历完整，长期稳定性更好",
        ],
        concerns=[
            "到岗时间较慢，短期补位成本更高",
            "薪资预期更高，需要确认预算弹性",
            "面试表达偏谨慎，可能需要进一步验证业务推动力度",
        ],
        scores={
            "面试表达": 78,
            "招聘实操": 82,
            "业务理解": 86,
            "到岗速度": 68,
            "成本可控": 70,
            "稳定/合规": 90,
        },
        interview_quote=(
            "赵澜的流程意识和风险判断比较稳，平台型业务协作经验也有参考价值。"
            "她不是最快到岗的人选，薪资也更高，但如果团队更看重长期稳定和规范化落地，值得进入二面。"
        ),
        decision="建议二面",
        decision_label="待定",
    ),
}


HIGH_RISK_KEYWORDS = [
    "录用",
    "淘汰",
    "拒绝候选人",
    "发offer",
    "发 offer",
    "offer",
    "调薪",
    "降薪",
    "辞退",
    "解雇",
    "解除劳动合同",
    "修改薪资",
    "删除员工",
    "开除",
    "权限变更",
]


TASK_KEYWORDS = {
    "identity": ["介绍", "你是谁", "能做到", "哪些事情", "能力", "好久不见"],
    "recruitment_pipeline": ["未读邮件", "新简历", "下载", "转成", "markdown", "md格式", "候选人简历"],
    "candidate_compare": ["对比", "哪位", "更合适", "更快", "沈嘉", "赵澜", "推荐"],
    "interview_email": ["邮件", "通知", "面试邀请", "gmail", "qq邮箱", "发送邮件"],
    "interview_evaluation": ["录音", "转写", "面试结果", "面试评估", "反馈"],
    "onboarding": ["入职", "onboarding", "报到", "工位", "账号", "新人"],
    "policy_qa": ["制度", "政策", "年假", "请假", "社保", "公积金", "加班", "报销", "福利"],
    "resume_screening": ["简历", "候选人", "筛选", "面试", "投递", "招聘"],
}


def ensure_artifact_dir() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def public_url(path: str) -> str:
    return f"{BASE_PUBLIC_URL}{path}"


def detect_task_type(content: str) -> str:
    lowered = content.lower()
    if "gmail" in lowered or "@" in content:
        return "interview_email"
    for task_type, keywords in TASK_KEYWORDS.items():
        if any(keyword.lower() in lowered for keyword in keywords):
            return task_type
    return "policy_qa"


def detect_risk_level(content: str) -> str:
    lowered = content.lower()
    return "high" if any(keyword.lower() in lowered for keyword in HIGH_RISK_KEYWORDS) else "normal"


def risk_notice(risk_level: str) -> str:
    if risk_level != "high":
        return "当前任务未识别为高风险动作，但关键事实仍建议 HR 复核。"
    return "requires HR confirmation。检测到高风险 HR 动作，系统只生成分析和草稿，不自动执行最终录用、淘汰、发 offer、调薪或权限变更。"


def candidate_doc_markdown(candidate: Candidate) -> str:
    strengths = "\n".join(f"- {item}" for item in candidate.strengths)
    concerns = "\n".join(f"- {item}" for item in candidate.concerns)
    score_rows = "\n".join(f"| {name} | {score}/100 |" for name, score in candidate.scores.items())
    return f"""# 候选人信息 - {candidate.name} ({candidate.role})

文档更新时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}

## 基本信息

- 姓名：{candidate.name}
- 性别：{candidate.gender}
- 出生年份：{candidate.birth_year}
- 现居城市：{candidate.city}
- 联系电话：{candidate.phone_masked}
- 邮箱：{candidate.email}
- 求职意向：{candidate.role}
- 期望薪资：{candidate.salary}
- 到岗时间：{candidate.availability}

## 教育背景

{candidate.education}

## 工作经历

{candidate.work_summary}

## 能力评估

| 维度 | 评分 |
|---|---|
{score_rows}

## 优势

{strengths}

## 关注点

{concerns}

## 面试官原始评价

> {candidate.interview_quote}

## 当前建议

{candidate.decision}

## 风控边界

本档案仅作为招聘决策支持，不代表最终录用结论。最终录用、淘汰、薪资和 offer 必须由 HR 人工确认。
"""


def write_candidate_doc(candidate: Candidate) -> Path:
    ensure_artifact_dir()
    path = ARTIFACT_DIR / f"candidate_{candidate.candidate_id}.md"
    path.write_text(candidate_doc_markdown(candidate), encoding="utf-8")
    return path


def candidate_card_html(candidate: Candidate) -> str:
    rows = "".join(
        f"<tr><th>{html.escape(name)}</th><td>{score}</td></tr>"
        for name, score in candidate.scores.items()
    )
    strengths = "".join(f"<li>{html.escape(item)}</li>" for item in candidate.strengths)
    concerns = "".join(f"<li>{html.escape(item)}</li>" for item in candidate.concerns)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>候选人信息 - {html.escape(candidate.name)}</title>
  <style>
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f6f8fb; color: #1f2937; }}
    main {{ max-width: 920px; margin: 0 auto; padding: 40px 24px 72px; }}
    h1 {{ font-size: 40px; margin: 0 0 12px; }}
    .meta {{ color: #64748b; margin-bottom: 28px; }}
    section {{ background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 24px; margin: 18px 0; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border-bottom: 1px solid #e5e7eb; padding: 12px 8px; text-align: left; }}
    th {{ color: #475569; width: 180px; }}
    .badge {{ display: inline-block; padding: 6px 12px; border-radius: 999px; background: #dcfce7; color: #166534; font-weight: 700; }}
    .warn {{ background: #fff7ed; color: #9a3412; }}
  </style>
</head>
<body>
  <main>
    <h1>候选人信息 - {html.escape(candidate.name)} ({html.escape(candidate.role)})</h1>
    <div class="meta">DianHR AgentBridge · 今天修改 · 决策支持档案</div>
    <section>
      <span class="badge">{html.escape(candidate.decision_label)}</span>
      <table>
        <tr><th>姓名</th><td>{html.escape(candidate.name)}</td></tr>
        <tr><th>城市</th><td>{html.escape(candidate.city)}</td></tr>
        <tr><th>学历</th><td>{html.escape(candidate.education)}</td></tr>
        <tr><th>期望薪资</th><td>{html.escape(candidate.salary)}</td></tr>
        <tr><th>到岗时间</th><td>{html.escape(candidate.availability)}</td></tr>
        <tr><th>工作概览</th><td>{html.escape(candidate.work_summary)}</td></tr>
      </table>
    </section>
    <section>
      <h2>能力评分</h2>
      <table>{rows}</table>
    </section>
    <section>
      <h2>优势</h2>
      <ul>{strengths}</ul>
    </section>
    <section>
      <h2>关注点</h2>
      <ul>{concerns}</ul>
    </section>
    <section>
      <h2>风控边界</h2>
      <p>本页面只用于招聘辅助分析。最终录用、淘汰、薪资和 offer 必须由 HR 人工确认。</p>
    </section>
  </main>
</body>
</html>"""


def write_candidate_html(candidate: Candidate) -> Path:
    ensure_artifact_dir()
    path = ARTIFACT_DIR / f"candidate_{candidate.candidate_id}.html"
    path.write_text(candidate_card_html(candidate), encoding="utf-8")
    return path


def report_html() -> str:
    liu = CANDIDATES["liuchen"]
    wang = CANDIDATES["wanglin"]
    labels = list(liu.scores.keys())
    liu_scores = [liu.scores[label] for label in labels]
    wang_scores = [wang.scores[label] for label in labels]
    liu_avg = round(sum(liu_scores) / len(liu_scores), 1)
    wang_avg = round(sum(wang_scores) / len(wang_scores), 1)
    rows = "".join(
        f"""<tr>
          <th>{html.escape(label)}</th>
          <td><span class="score">{liu.scores[label]}</span><div class="meter"><i style="width:{liu.scores[label]}%"></i></div></td>
          <td><span class="score">{wang.scores[label]}</span><div class="meter amber"><i style="width:{wang.scores[label]}%"></i></div></td>
          <td>{html.escape(_compare_note(label))}</td>
        </tr>"""
        for label in labels
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>HRBP 候选人对比报告</title>
  <style>
    :root {{
      color-scheme: light;
      --paper: #f4f6f8;
      --card: #ffffff;
      --ink: #172033;
      --muted: #657085;
      --line: #dbe1ea;
      --line-strong: #c9d2df;
      --blue: #2f6ff6;
      --green: #198c63;
      --green-soft: #e8f6ef;
      --amber: #b87505;
      --amber-soft: #fff3d7;
      --slate: #2d3a52;
      --shadow: 0 18px 46px rgba(31, 42, 68, .10);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--paper);
      color: var(--ink);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
      letter-spacing: 0;
    }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 34px 28px 64px; }}
    .topbar {{ display: flex; justify-content: space-between; align-items: center; gap: 16px; margin-bottom: 26px; }}
    .eyebrow {{ color: var(--blue); font-size: 13px; font-weight: 700; margin-bottom: 8px; }}
    h1 {{ margin: 0; font-size: 32px; line-height: 1.18; color: var(--ink); }}
    h2 {{ margin: 0 0 18px; font-size: 18px; color: var(--ink); }}
    h3 {{ margin: 0 0 8px; font-size: 15px; color: var(--slate); }}
    .sub {{ color: var(--muted); margin-top: 9px; font-size: 14px; }}
    .stamp {{ border: 1px solid var(--line); background: rgba(255,255,255,.72); padding: 9px 12px; border-radius: 8px; color: var(--muted); font-size: 13px; white-space: nowrap; }}
    .layout {{ display: grid; grid-template-columns: 1fr; gap: 18px; align-items: start; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }}
    .card {{ background: var(--card); border: 1px solid var(--line); border-radius: 8px; padding: 22px; box-shadow: var(--shadow); }}
    .candidate {{ position: relative; overflow: hidden; }}
    .candidate::before {{ content: ""; position: absolute; inset: 0 auto 0 0; width: 4px; background: var(--green); }}
    .candidate.alt::before {{ background: var(--amber); }}
    .identity {{ display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }}
    .avatar {{ width: 44px; height: 44px; border-radius: 8px; display: grid; place-items: center; color: white; background: var(--green); font-weight: 900; font-size: 19px; flex: 0 0 auto; }}
    .alt .avatar {{ background: var(--amber); }}
    .name {{ font-size: 23px; font-weight: 850; margin-bottom: 4px; }}
    .meta {{ color: var(--muted); font-size: 13px; line-height: 1.55; }}
    .tag {{ display: inline-flex; align-items: center; height: 28px; margin-top: 12px; padding: 0 11px; border-radius: 999px; background: var(--green-soft); color: var(--green); font-weight: 800; font-size: 13px; }}
    .alt .tag {{ background: var(--amber-soft); color: var(--amber); }}
    .facts {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; margin-top: 18px; }}
    .fact {{ border: 1px solid var(--line); border-radius: 8px; padding: 12px; color: var(--muted); font-size: 12px; background: #fbfcfe; min-height: 72px; }}
    .fact b {{ display: block; color: var(--ink); margin-top: 5px; font-size: 15px; line-height: 1.3; }}
    .decision {{ display: grid; gap: 14px; padding: 26px 28px; }}
    .decision-top {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }}
    .verdict {{ border-left: 4px solid var(--green); background: #f8fbfa; padding: 16px; border-radius: 8px; }}
    .verdict strong {{ color: var(--green); font-size: 20px; }}
    .audit {{ border-left: 4px solid var(--amber); background: #fffaf0; padding: 16px; border-radius: 8px; color: #5e4a1f; }}
    .score-strip {{ border: 1px solid var(--line); border-radius: 8px; padding: 16px; background: #fbfcfe; }}
    .score-strip h3 {{ margin-bottom: 12px; }}
    .score-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }}
    .split {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }}
    .mini {{ border: 1px solid var(--line); border-radius: 8px; padding: 14px; background: #fbfcfe; }}
    .mini ul {{ margin: 8px 0 0; padding-left: 18px; color: var(--muted); line-height: 1.75; }}
    canvas {{ width: 100%; height: 340px; display: block; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    th, td {{ border-bottom: 1px solid var(--line); padding: 13px 10px; text-align: left; vertical-align: top; }}
    th {{ color: #31405b; font-weight: 800; white-space: nowrap; }}
    td {{ color: var(--muted); }}
    .score {{ display: inline-block; min-width: 28px; color: var(--ink); font-weight: 800; }}
    .meter {{ display: inline-block; width: 92px; height: 6px; margin-left: 8px; border-radius: 999px; background: #e9edf4; vertical-align: middle; overflow: hidden; }}
    .meter i {{ display: block; height: 100%; background: var(--green); border-radius: inherit; }}
    .meter.amber i {{ background: var(--amber); }}
    .quotes {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }}
    blockquote {{ margin: 0; padding: 15px 16px; border-radius: 8px; background: #f8fafc; border: 1px solid var(--line); color: #354258; line-height: 1.75; }}
    .footer-note {{ margin-top: 22px; color: var(--muted); font-size: 12px; text-align: center; }}
    @media (max-width: 880px) {{
      main {{ padding: 24px 14px 48px; }}
      .topbar, .layout, .grid, .split, .quotes, .decision-top, .score-grid {{ grid-template-columns: 1fr; display: grid; }}
      .stamp {{ white-space: normal; }}
      h1 {{ font-size: 27px; }}
      canvas {{ height: 300px; }}
      .meter {{ width: 64px; }}
    }}
  </style>
</head>
<body>
  <main>
    <div class="topbar">
      <div>
        <div class="eyebrow">DianHR AgentBridge · 决策支持报告</div>
        <h1>HRBP 候选人对比</h1>
        <div class="sub">基于简历档案、面试记录与“快速补位 + 目标岗位适配”双目标生成</div>
      </div>
      <div class="stamp">生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M")} · requires HR confirmation</div>
    </div>

    <div class="layout">
      <section class="card decision">
        <h2>结论摘要</h2>
        <div class="decision-top">
          <div class="verdict">
            <strong>当前倾向：{html.escape(liu.name)}</strong>
            <p>更适合“尽快完成团队招聘”的现场目标，优势集中在沟通推进、招聘实操、到岗速度和成本可控。</p>
          </div>
          <div class="audit">
            <b>需要人工复核</b>
            <p>{html.escape(wang.name)} 在平台型业务背景与稳定/合规维度更强，不应直接淘汰。建议 HR 结合预算、到岗时间和培养成本后确认最终 offer 策略。</p>
          </div>
        </div>
        <div class="score-strip">
          <h3>综合均分</h3>
          <div class="score-grid">
            <div class="mini">
              <h3>{html.escape(liu.name)}</h3>
              <div class="name">{liu_avg}</div>
              <div class="meta">推荐录用，但需补齐目标行业 SOP</div>
            </div>
            <div class="mini">
              <h3>{html.escape(wang.name)}</h3>
              <div class="name">{wang_avg}</div>
              <div class="meta">建议二面，重点确认到岗与预算</div>
            </div>
          </div>
        </div>
        <div class="split">
          <div class="mini">
            <h3>{html.escape(liu.name)} 更强项</h3>
            <ul><li>候选人沟通与面试推进</li><li>短期补位速度</li><li>薪资谈判空间</li></ul>
          </div>
          <div class="mini">
            <h3>{html.escape(wang.name)} 更强项</h3>
            <ul><li>平台型业务协作背景</li><li>流程规范与风险意识</li><li>长期稳定性</li></ul>
          </div>
        </div>
      </section>
    </div>

    <div class="grid" style="margin-top:18px">
      <section class="card candidate">
        <div class="identity">
          <div>
            <div class="name">{html.escape(liu.name)}</div>
            <div class="meta">{html.escape(liu.role)} · {html.escape(liu.education)} · {html.escape(liu.company_background)}</div>
            <span class="tag">{html.escape(liu.decision_label)}</span>
          </div>
          <div class="avatar">{html.escape(liu.name[:1])}</div>
        </div>
        <div class="facts">
          <div class="fact">期望薪资<b>{html.escape(liu.salary)}</b></div>
          <div class="fact">到岗时间<b>{html.escape(liu.availability)}</b></div>
          <div class="fact">服务团队规模<b>{html.escape(liu.team_size)}</b></div>
          <div class="fact">主要风险<b>行业合规经验需补齐</b></div>
        </div>
      </section>
      <section class="card candidate alt">
        <div class="identity">
          <div>
            <div class="name">{html.escape(wang.name)}</div>
            <div class="meta">{html.escape(wang.role)} · {html.escape(wang.education)} · {html.escape(wang.company_background)}</div>
            <span class="tag">{html.escape(wang.decision_label)}</span>
          </div>
          <div class="avatar">{html.escape(wang.name[:1])}</div>
        </div>
        <div class="facts">
          <div class="fact">期望薪资<b>{html.escape(wang.salary)}</b></div>
          <div class="fact">到岗时间<b>{html.escape(wang.availability)}</b></div>
          <div class="fact">服务团队规模<b>{html.escape(wang.team_size)}</b></div>
          <div class="fact">主要风险<b>补位速度与预算压力</b></div>
        </div>
      </section>
    </div>

    <div class="grid" style="margin-top:18px">
      <section class="card">
        <h2>能力维度雷达图</h2>
        <canvas id="radar"></canvas>
      </section>
      <section class="card">
        <h2>综合评分对比</h2>
        <canvas id="bars"></canvas>
      </section>
    </div>
    <section class="card" style="margin-top:18px">
      <h2>面试官原始评价</h2>
      <div class="quotes">
        <blockquote><b>{html.escape(liu.name)}：</b>{html.escape(liu.interview_quote)}</blockquote>
        <blockquote><b>{html.escape(wang.name)}：</b>{html.escape(wang.interview_quote)}</blockquote>
      </div>
    </section>
    <section class="card" style="margin-top:18px">
      <h2>详细对比表</h2>
      <table>
        <tr><th>评估维度</th><th>{html.escape(liu.name)}</th><th>{html.escape(wang.name)}</th><th>人工复核提示</th></tr>
        {rows}
      </table>
    </section>
    <section class="card" style="margin-top:18px">
      <h2>招聘建议</h2>
      <div class="split">
        <div class="mini">
          <h3>建议动作</h3>
          <p>优先推进 {html.escape(liu.name)} 的 offer 预算确认，同时保留 {html.escape(wang.name)} 进入二面或备选池。</p>
        </div>
        <div class="mini">
          <h3>风控边界</h3>
          <p>系统只提供决策支持，不自动执行录用、淘汰、薪资调整或 offer 发放。requires HR confirmation</p>
        </div>
      </div>
    </section>
    <div class="footer-note">DianHR AgentBridge · Local fallback artifact · Generated from synthetic demo data</div>
  </main>
  <script>
    const labels = {json.dumps(labels, ensure_ascii=False)};
    const liu = {json.dumps(liu_scores)};
    const wang = {json.dumps(wang_scores)};
    function setup(canvas) {{
      const ratio = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * ratio;
      canvas.height = Math.max(320, rect.height || 360) * ratio;
      const ctx = canvas.getContext('2d');
      ctx.scale(ratio, ratio);
      return {{ ctx, w: rect.width, h: Math.max(320, rect.height || 360) }};
    }}
    function polygonPoints(values, cx, cy, radius) {{
      return values.map((v, i) => {{
        const angle = -Math.PI / 2 + i * Math.PI * 2 / values.length;
        const r = radius * v / 100;
        return [cx + Math.cos(angle) * r, cy + Math.sin(angle) * r];
      }});
    }}
    function drawPoly(ctx, points, stroke, fill) {{
      ctx.beginPath();
      points.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y));
      ctx.closePath();
      ctx.fillStyle = fill;
      ctx.strokeStyle = stroke;
      ctx.lineWidth = 2;
      ctx.fill();
      ctx.stroke();
    }}
    function drawRadar() {{
      const canvas = document.getElementById('radar');
      const {{ctx, w, h}} = setup(canvas);
      const cx = w / 2, cy = h / 2, radius = Math.min(w, h) * 0.34;
      ctx.clearRect(0, 0, w, h);
      ctx.font = '12px -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      for (let ring = 1; ring <= 5; ring++) {{
        const points = polygonPoints(new Array(labels.length).fill(ring * 20), cx, cy, radius);
        drawPoly(ctx, points, '#d6deea', 'transparent');
      }}
      labels.forEach((label, i) => {{
        const angle = -Math.PI / 2 + i * Math.PI * 2 / labels.length;
        const x = cx + Math.cos(angle) * (radius + 42);
        const y = cy + Math.sin(angle) * (radius + 24);
        ctx.strokeStyle = '#e1e7f0';
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(cx + Math.cos(angle) * radius, cy + Math.sin(angle) * radius);
        ctx.stroke();
        ctx.fillStyle = '#5d687a';
        ctx.fillText(label, x, y);
      }});
      drawPoly(ctx, polygonPoints(liu, cx, cy, radius), '#198c63', 'rgba(25,140,99,.16)');
      drawPoly(ctx, polygonPoints(wang, cx, cy, radius), '#b87505', 'rgba(184,117,5,.14)');
      ctx.fillStyle = '#198c63'; ctx.fillRect(cx - 72, h - 24, 16, 10); ctx.fillStyle = '#5d687a'; ctx.fillText('{html.escape(liu.name)}', cx - 26, h - 19);
      ctx.fillStyle = '#b87505'; ctx.fillRect(cx + 32, h - 24, 16, 10); ctx.fillStyle = '#5d687a'; ctx.fillText('{html.escape(wang.name)}', cx + 78, h - 19);
    }}
    function drawBars() {{
      const canvas = document.getElementById('bars');
      const {{ctx, w, h}} = setup(canvas);
      const pad = 46, chartH = h - 90, chartW = w - pad * 2;
      ctx.clearRect(0, 0, w, h);
      ctx.strokeStyle = '#e1e7f0';
      ctx.fillStyle = '#5d687a';
      ctx.font = '12px -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif';
      for (let t = 0; t <= 100; t += 20) {{
        const y = pad + chartH * (1 - t / 100);
        ctx.beginPath(); ctx.moveTo(pad, y); ctx.lineTo(w - pad, y); ctx.stroke();
        ctx.fillText(String(t), 18, y + 4);
      }}
      const groupW = chartW / labels.length;
      labels.forEach((label, i) => {{
        const x = pad + i * groupW + groupW * 0.22;
        const bW = groupW * 0.24;
        const lh = chartH * liu[i] / 100;
        const wh = chartH * wang[i] / 100;
        ctx.fillStyle = '#198c63'; ctx.fillRect(x, pad + chartH - lh, bW, lh);
        ctx.fillStyle = '#b87505'; ctx.fillRect(x + bW + 5, pad + chartH - wh, bW, wh);
        ctx.save(); ctx.translate(x + bW, h - 34); ctx.rotate(-0.35);
        ctx.fillStyle = '#5d687a'; ctx.textAlign = 'right'; ctx.fillText(label, 0, 0); ctx.restore();
      }});
      ctx.fillStyle = '#198c63'; ctx.fillRect(w / 2 - 86, h - 18, 16, 10); ctx.fillStyle = '#5d687a'; ctx.fillText('{html.escape(liu.name)}', w / 2 - 58, h - 9);
      ctx.fillStyle = '#b87505'; ctx.fillRect(w / 2 + 18, h - 18, 16, 10); ctx.fillStyle = '#5d687a'; ctx.fillText('{html.escape(wang.name)}', w / 2 + 46, h - 9);
    }}
    drawRadar();
    drawBars();
    window.addEventListener('resize', () => {{ drawRadar(); drawBars(); }});
  </script>
</body>
</html>"""


def _compare_note(label: str) -> str:
    notes = {
        "面试表达": "沈嘉推进感更强，赵澜表达更谨慎",
        "招聘实操": "沈嘉更适合短期补位，赵澜流程意识更强",
        "业务理解": "赵澜平台型业务背景更贴近复杂组织协同",
        "到岗速度": "沈嘉更快，适合演示中的紧急招聘目标",
        "成本可控": "沈嘉薪资区间更低，但仍需预算确认",
        "稳定/合规": "赵澜在规范化和长期稳定上更强，不能直接淘汰",
    }
    return notes.get(label, "")


def write_compare_report() -> Path:
    ensure_artifact_dir()
    path = ARTIFACT_DIR / "hrbp_candidate_compare.html"
    path.write_text(report_html(), encoding="utf-8")
    return path


def build_recruitment_pipeline_result() -> HRResult:
    liu = CANDIDATES["liuchen"]
    wang = CANDIDATES["wanglin"]
    liu_doc = write_candidate_doc(liu)
    wang_doc = write_candidate_doc(wang)
    write_candidate_html(liu)
    write_candidate_html(wang)
    report = write_compare_report()
    artifacts = {
        f"{liu.name}候选人档案": public_url("/candidates/liuchen"),
        f"{wang.name}候选人档案": public_url("/candidates/wanglin"),
        "候选人对比报告": public_url("/reports/hrbp-compare"),
        f"{liu.name}Markdown": str(liu_doc),
        f"{wang.name}Markdown": str(wang_doc),
        "HTML报告文件": str(report),
    }
    reply = f"""✅ 新候选人简历已处理！

已完成的操作：

| 步骤 | 状态 |
|---|---|
| ✅ 检查未读邮件 | 发现 2 份候选人简历 |
| ✅ 保存 PDF | 已保存到本地演示目录 |
| ✅ 转化 Markdown | 已生成结构化候选人档案 |
| ✅ 创建候选人文档 | 已生成可查看页面 |
| ✅ 生成对比报告 | 已生成领导汇报页面 |

候选人速览：

| 维度 | {liu.name} | {wang.name} |
|---|---|---|
| 岗位 | HRBP | HRBP |
| 背景 | {liu.company_background} | {wang.company_background} |
| 团队规模 | {liu.team_size} | {wang.team_size} |
| 经验 | 4年 HRBP | 5年 HRBP/共享服务协作 |
| 期望薪资 | {liu.salary} | {wang.salary} |
| 到岗时间 | {liu.availability} | {wang.availability} |

📄 {liu.name}档案：{artifacts[f"{liu.name}候选人档案"]}
📄 {wang.name}档案：{artifacts[f"{wang.name}候选人档案"]}
📊 候选人对比报告：{artifacts["候选人对比报告"]}

当前建议：倾向 {liu.name}，因为更适合“快速补位”的现场目标；但 {wang.name} 在平台型业务背景和稳定/合规维度更强，建议保留二面或备选。

风险边界：最终录用、淘汰、薪资和 offer 仍需 HR 人工确认。requires HR confirmation
"""
    return HRResult("recruitment_pipeline", reply, artifacts, requires_confirmation=True)


def build_candidate_compare_result() -> HRResult:
    report = write_compare_report()
    artifacts = {"候选人对比报告": public_url("/reports/hrbp-compare")}
    liu = CANDIDATES["liuchen"]
    wang = CANDIDATES["wanglin"]
    reply = f"""基于“快速完成团队招聘”这个目标，我的判断是：

## ✅ 当前倾向：{liu.name}

核心理由：推进更快、成本更可控、短期补位风险更低

| 维度 | {liu.name} | {wang.name} | 观察 |
|---|---|---|---|
| 到岗时间 | {liu.availability} | {wang.availability} | {liu.name} 更快 |
| 薪资预期 | {liu.salary} | {wang.salary} | {liu.name} 成本压力较低 |
| 招聘推进 | 沟通推进强 | 流程规范强 | 目标不同，不能只看总分 |
| 组织适配 | 需补齐目标行业 SOP | 平台业务协作经验更成熟 | {wang.name} 胜出 |
| 稳定/合规 | 需要复核长期稳定性 | 稳定/合规更成熟 | {wang.name} 胜出 |

具体原因：

1. 如果现场目标是“快速把招聘工作跑起来”，{liu.name} 更容易立刻进入推进节奏。
2. {wang.name} 的平台业务经验和流程意识更强，说明她不应被自动淘汰，适合进入二面或备选。
3. 最终决策要让 HR 结合预算、到岗时间、行业培养成本和团队长期稳定性一起判断。

📊 领导汇报报告：{artifacts["候选人对比报告"]}

边界提醒：这是决策支持，不是最终录用决定。发 offer 前必须由 HR 确认预算、薪资和审批流程。requires HR confirmation
"""
    return HRResult("candidate_compare", reply, artifacts, requires_confirmation=True)


def build_interview_email_result(content: str) -> HRResult:
    candidate = CANDIDATES["wanglin"] if "赵澜" in content else CANDIDATES["liuchen"]
    email_match = re.search(r"[\w.\-+]+@[\w.\-]+\.\w+", content)
    recipient = email_match.group(0) if email_match else "123456789@qq.com"
    time_text = "明天上午9点" if "上午" in content or "9" in content else "明天下午2点"
    location = "一楼小会议室" if "一楼" in content else "2楼会议室"
    subject = f"面试通知 - {time_text} | 候选人：{candidate.name} ({candidate.role})"
    artifacts = {"候选人档案": public_url(f"/candidates/{candidate.candidate_id}")}
    reply = f"""✅ 邮件已发送成功！

📧 收件人：{recipient}
📋 主题：{subject}
🕘 发送时间：刚刚

邮件内容包括：
- 面试时间：{time_text}
- 面试地点：{location}
- 候选人核心信息（{candidate.name}，{candidate.work_summary}）
- 候选人档案链接：{artifacts["候选人档案"]}

说明：本地降级模式下会生成“邮件发送成功”的演示结果；接入 Gmail/企业邮箱 API 后可真实发送。
"""
    return HRResult("interview_email", reply, artifacts)


def build_interview_evaluation_result() -> HRResult:
    report = write_compare_report()
    artifacts = {"候选人对比报告": public_url("/reports/hrbp-compare")}
    liu = CANDIDATES["liuchen"]
    wang = CANDIDATES["wanglin"]
    reply = f"""✅ 两份面试录音都转录完成！

## 📋 面试评估报告

### 候选人一：{liu.name}

| 维度 | 评估 |
|---|---|
| 综合表现 | ✅ 优秀 |
| 沟通推进 | ⭐⭐⭐⭐☆ 推进感强 |
| 招聘实操 | ⭐⭐⭐⭐☆ 参与链路完整 |
| 组织适配 | ⭐⭐⭐☆☆ 目标行业 SOP 需补齐 |
| 风险点 | 长期稳定性和行业合规经验需确认 |

面试官评价：
> {liu.interview_quote}

### 候选人二：{wang.name}

| 维度 | 评估 |
|---|---|
| 综合表现 | ⚠️ 建议二面 |
| 平台业务背景 | ⭐⭐⭐⭐⭐ 更贴近复杂组织协同 |
| 稳定/合规 | ⭐⭐⭐⭐⭐ 流程边界更成熟 |
| 到岗速度 | ⭐⭐⭐☆☆ 需要等待交接 |
| 风险点 | 到岗时间与薪资预算需确认 |

面试官评价：
> {wang.interview_quote}

## 🎯 综合建议

当前倾向 {liu.name}，前提是 HR 接受其目标行业流程经验需要补齐；{wang.name} 不建议直接淘汰，可作为二面或备选人选。

📊 领导汇报报告：{artifacts["候选人对比报告"]}

边界提醒：面试评估不等于最终录用结论。requires HR confirmation
"""
    return HRResult("interview_evaluation", reply, artifacts, requires_confirmation=True)


def build_onboarding_result(content: str, risk_level: str) -> HRResult:
    reply = f"""### ✅ 入职办理草稿已生成

识别到的入职需求：
{content}

待办事项：
1. 合同与入职材料：待 HR 确认合同模板
2. 账号权限：邮箱、钉钉/飞书、OA、知识库权限
3. 设备与工位：电脑、门禁、工位
4. 入职首日安排：公司介绍、制度说明、主管 1:1、Buddy 指定

风险边界：
{risk_notice(risk_level)}
"""
    return HRResult("onboarding", reply, {}, risk_level == "high")


def build_policy_result(content: str) -> HRResult:
    reply = f"""### ✅ HR 制度答复草稿

员工问题：
{content}

初步处理：
- 年假/请假类问题需要结合公司制度、累计工龄、当年已休假、地区政策确认。
- 若涉及医疗隐私、劳动争议、薪酬调整或处分，应转 HR 专员处理。
- 当前回答只提供办理路径和需确认信息，不替代正式制度解释。

需要 HR 确认：
1. 员工累计社会工龄
2. 当年已休年假天数
3. 公司年假折算规则
4. 是否存在影响假期资格的特殊情形
"""
    return HRResult("policy_qa", reply, {})


def build_identity_result() -> HRResult:
    reply = """你好！我是 **HR-Insight**，DianHR 数字员工。

我的定位不是闲聊机器人，而是一个专门支持招聘与 HR 决策的 AI 分析助理。我的工作方式是把零散信息整理成清晰、可比较、可追踪的结构。

我能帮你做这些事：

**简历处理**
- 把候选人简历整理成结构化 Markdown 档案
- 提取关键字段：技能、经历、项目、薪资、到岗时间
- 对比多个候选人，标出优势、差异和风险点

**面试支持**
- 整理面试记录，区分事实、观点和推论
- 生成候选人评估摘要
- 给出面试追问建议和待确认问题

**信息整合**
- 生成候选人档案页面
- 生成领导可看的候选人对比报告
- 准备面试通知邮件草稿

**安全边界**
- 我可以辅助分析，但不能替 HR 做最终录用、淘汰、薪资、offer 或权限决定
- 高风险动作必须标记：requires HR confirmation

你可以直接给我一个招聘任务，我会尽量把结果做成可交付的工作成果。"""
    return HRResult("identity", reply, {})


def build_resume_screening_result(content: str, risk_level: str) -> HRResult:
    known_names = ["沈嘉", "赵澜"]
    return build_recruitment_pipeline_result() if any(name in content for name in known_names) else HRResult(
        "resume_screening",
        f"""### ✅ 简历初筛结果

候选信息：
{content}

岗位匹配度：较高

匹配点：
- 技能或经历与目标岗位存在明显关联。
- 可进入人工面试评估。
- 需要补充项目细节、稳定性、薪资期望和到岗时间。

风险边界：
{risk_notice(risk_level)}
""",
        {},
        risk_level == "high",
    )


def build_offer_boundary_result(content: str) -> HRResult:
    report = write_compare_report()
    artifacts = {"候选人对比报告": public_url("/reports/hrbp-compare")}
    reply = f"""⚠️ 已识别高风险 HR 动作

你的请求涉及最终录用、offer 或候选人处置：
{content}

系统不会自动执行以下动作：
- 不自动发 offer
- 不自动淘汰候选人
- 不自动承诺薪资
- 不自动修改候选人状态为最终录用

我可以提供：
1. 候选人对比分析
2. offer 准备清单
3. 邮件草稿
4. 审批前风险提示

📊 决策支持报告：{artifacts["候选人对比报告"]}

requires HR confirmation
"""
    return HRResult("risk_boundary", reply, artifacts, True)


def run_local_hr_demo(content: str) -> HRResult:
    risk_level = detect_risk_level(content)
    if risk_level == "high":
        return build_offer_boundary_result(content)

    task_type = detect_task_type(content)
    if task_type == "identity":
        return build_identity_result()
    if task_type == "recruitment_pipeline":
        return build_recruitment_pipeline_result()
    if task_type == "candidate_compare":
        return build_candidate_compare_result()
    if task_type == "interview_email":
        return build_interview_email_result(content)
    if task_type == "interview_evaluation":
        return build_interview_evaluation_result()
    if task_type == "onboarding":
        return build_onboarding_result(content, risk_level)
    if task_type == "resume_screening":
        return build_resume_screening_result(content, risk_level)
    return build_policy_result(content)


def get_candidate(candidate_id: str) -> Optional[Candidate]:
    return CANDIDATES.get(candidate_id)


def get_artifact_path(filename: str) -> Path:
    safe = Path(filename).name
    return ARTIFACT_DIR / safe


def result_to_dict(result: HRResult, source: str) -> Dict[str, Any]:
    return {
        "success": True,
        "task_type": result.task_type,
        "source": source,
        "reply": result.reply,
        "artifacts": result.artifacts,
        "requires_confirmation": result.requires_confirmation,
        "generated_at": now_iso(),
    }


def candidate_to_dict(candidate: Candidate) -> Dict[str, Any]:
    return asdict(candidate)
