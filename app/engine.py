"""
打分引擎：把用户答案映射到人格类型。

纯 Python 标准库，零依赖。数据源是 data/*.json（结构化题库 + 报告）。
计分方式：统计 A/B/C/D 出现最多的那项，即命中对应的人格类型。
"""
import json
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


def load_test(test_id: str) -> dict:
    """加载一个测试的完整数据（题库 + 结果）。"""
    path = DATA_DIR / f"{test_id}.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def list_tests() -> list[dict]:
    """列出所有可用测试（只返回轻量元信息，不含题库/报告正文）。"""
    tests = []
    for path in sorted(DATA_DIR.glob("*.json")):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        tests.append({
            "id": data["id"],
            "title": data["title"],
            "category": data["category"],
            "question_count": len(data["questions"]),
            "result_count": len(data["results"]),
        })
    return tests


def score(test: dict, answers: list[str]) -> dict:
    """
    根据答案返回命中的结果对象（完整报告）。

    answers: 每题的 key，例如 ["A", "B", "A", ...]，长度须等于题目数。
    计分规则：出现次数最多的 key 命中对应结果；并列时取先出现者（Counter 顺序稳定）。
    """
    if len(answers) != len(test["questions"]):
        raise ValueError(
            f"需要 {len(test['questions'])} 个答案，实际给了 {len(answers)} 个"
        )
    valid_keys = {r["key"] for r in test["results"]}
    for a in answers:
        if a not in valid_keys:
            raise ValueError(f"非法答案 '{a}'，合法 key 为 {sorted(valid_keys)}")

    tally = Counter(answers)
    # Counter.most_common 对并列次数保持插入顺序（即首次出现顺序），结果稳定
    top_key = tally.most_common(1)[0][0]
    return next(r for r in test["results"] if r["key"] == top_key)


def get_result(test_id: str, answers: list[str]) -> dict:
    """便捷入口：加载测试并打分。"""
    return score(load_test(test_id), answers)


if __name__ == "__main__":
    # 命令行自测：python3 engine.py
    print("可用测试：")
    for t in list_tests():
        print(f"  {t['id']:8s} {t['title']}（{t['question_count']} 题 / {t['result_count']} 种结果）")

    demo_answers = ["A"] * 7 + ["B"] * 5
    result = get_result("love", demo_answers)
    print(f"\n自测示例（7 个 A + 5 个 B）：命中 → {result['type']}（{result['tagline']}）")
    print(f"钩子：{result['hook']}")
