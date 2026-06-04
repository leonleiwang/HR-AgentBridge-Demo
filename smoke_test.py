from app import run_hr_agent
from hr_demo import ARTIFACT_DIR


def assert_contains(text: str, needle: str) -> None:
    if needle not in text:
        raise AssertionError(f"Expected to find {needle!r} in response")


def main() -> int:
    pipeline = run_hr_agent("检查今天未读邮件里有没有新的候选人简历，如果有就生成候选人档案和对比报告")
    assert pipeline["success"] is True
    assert pipeline["task_type"] == "recruitment_pipeline"
    assert_contains(pipeline["reply"], "候选人对比报告")
    assert_contains(pipeline["reply"], "沈嘉")
    assert_contains(pipeline["reply"], "赵澜")
    assert "候选人对比报告" in pipeline["artifacts"]

    compare = run_hr_agent("如果我现在想更快速地完成团队招聘，你觉得哪位 HR 更加合适？")
    assert compare["task_type"] == "candidate_compare"
    assert_contains(compare["reply"], "当前倾向：沈嘉")
    assert_contains(compare["reply"], "赵澜 胜出")

    interview_email = run_hr_agent("请通知于世龙老师，123456789@qq.com，明天上午9点在一楼小会议室面试赵澜，可以用gmail发送邮件。")
    assert interview_email["task_type"] == "interview_email"
    assert_contains(interview_email["reply"], "123456789@qq.com")

    boundary = run_hr_agent("直接给沈嘉发 offer，并把赵澜淘汰")
    assert boundary["requires_confirmation"] is True
    assert_contains(boundary["reply"], "requires HR confirmation")

    expected_files = [
        ARTIFACT_DIR / "candidate_liuchen.md",
        ARTIFACT_DIR / "candidate_wanglin.md",
        ARTIFACT_DIR / "hrbp_candidate_compare.html",
    ]
    missing = [str(path) for path in expected_files if not path.exists()]
    if missing:
        raise AssertionError(f"Missing generated artifacts: {missing}")

    print("Smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
