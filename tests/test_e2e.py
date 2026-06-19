"""端到端测试：模拟完整评估流程"""
import json
import urllib.request
import random

BASE = "http://127.0.0.1:5000"


def post(url, data):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get(url):
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read().decode("utf-8"))


def simulate_personality(profile_type="average"):
    """为不同人格类型生成模拟回答"""
    profiles = {
        "average": {
            "default": lambda: random.choice([2, 3, 3, 3, 3, 4]),
        },
        "high_openness_low_agreeableness": {
            "openness": lambda: random.choice([4, 4, 5, 4, 5]),
            "agreeableness": lambda: random.choice([1, 2, 1, 2, 2]),
            "default": lambda: random.choice([2, 3, 3, 4]),
        },
        "high_neuroticism": {
            "neuroticism": lambda: random.choice([4, 5, 4, 5, 4]),
            "default": lambda: random.choice([2, 3, 3, 4]),
        },
        "low_conscientiousness": {
            "conscientiousness": lambda: random.choice([1, 2, 1, 2, 2]),
            "default": lambda: random.choice([2, 3, 3, 4]),
        },
    }
    return profiles.get(profile_type, profiles["average"])


def generate_answer(item_id, profile):
    prefix = item_id.split("_")[0]
    if prefix == "bfi2":
        domain = item_id.split("_")[1]
        func = profile.get(domain, profile.get("default", lambda: 3))
    else:
        func = profile.get("default", lambda: 3)
    return func()


def run_assessment(profile_type="average", verbose=True):
    print(f"\n{'='*60}")
    print(f"测试: {profile_type}")
    print(f"{'='*60}")

    sim = simulate_personality(profile_type)

    # 开始
    data = post(f"{BASE}/assessment/start", {})
    session_id = data["session_id"]
    print(f"会话: {session_id}")

    answered = 0
    complete = False

    while not complete:
        # 获取当前题目
        qdata = get(f"{BASE}/assessment/question?session_id={session_id}")

        if qdata.get("phase_complete"):
            # 阶段转换——发送一个空答案推进
            adata = post(f"{BASE}/assessment/answer", {
                "session_id": session_id,
                "item_id": "_phase_transition",
                "score": 0,
                "direction": "next",
            })

            if adata.get("complete"):
                complete = True
                print(f"  评估完成!")
                break

            if adata.get("phase_complete"):
                print(f"  阶段{adata['phase']}->{adata.get('next_phase','?')}: {adata.get('message','')[:80]}")
            continue

        item = qdata.get("question", {})
        if not item:
            print(f"  错误: 无题目数据")
            break

        item_id = item["id"]
        scale_type = item.get("scale_type", "likert")

        # 生成答案
        if scale_type == "open_text":
            answer = f"测试回答 ({profile_type})"
        elif scale_type == "forced_choice":
            answer = random.choice(["A", "B"])
        else:
            answer = generate_answer(item_id, sim)

        # 提交
        adata = post(f"{BASE}/assessment/answer", {
            "session_id": session_id,
            "item_id": item_id,
            "score": answer,
            "direction": "next",
        })
        answered += 1

        if adata.get("complete"):
            complete = True
            print(f"  完成! {answered}题")
            break

        if adata.get("phase_complete"):
            print(f"  阶段{adata['phase']}完成->阶段{adata.get('next_phase','?')}")

        if verbose and answered % 20 == 0:
            print(f"  ...{answered}题已答")

    print(f"共回答: {answered}题")

    # 获取报告
    if session_id:
        print("获取报告...")
        try:
            rdata = get(f"{BASE}/report/{session_id}/data")
            report = rdata.get("report", {})

            # 验证
            bfi2 = report.get("bfi2_profile", {}).get("domains", {})
            weaknesses = report.get("weakness_focus", [])
            patterns = report.get("cross_domain_patterns", [])
            audit = report.get("_honesty_audit", {})

            print(f"  BFI-2维度: {len(bfi2)}")
            for d, info in bfi2.items():
                print(f"    {info.get('name', d)}: {info.get('percentile')}% ({info.get('classification')})")

            rses = report.get("rses", {})
            if rses:
                print(f"  RSES: {rses.get('classification')} (raw={rses.get('raw')})")

            sd3 = report.get("sd3_profile", {}).get("traits", {})
            if sd3:
                print(f"  SD3: {len(sd3)}特质")
                for t, info in sd3.items():
                    print(f"    {t}: {info.get('percentile')}% ({info.get('classification')})")

            ecr = report.get("ecr_r", {})
            if ecr:
                print(f"  ECR-R: {ecr.get('quadrant')}")

            crt = report.get("crt", {})
            if crt:
                print(f"  CRT: {crt.get('classification')} ({crt.get('correct')}/{crt.get('total')})")

            print(f"  跨维度模式: {len(patterns)}")
            for p in patterns:
                print(f"    [{p['severity']}] {p['title']}")

            print(f"  弱项: {len(weaknesses)}")
            print(f"  诚实审计: {audit.get('total_strengths')}优势/{audit.get('total_risks')}风险")

            return True
        except Exception as e:
            print(f"报告获取失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    return False


if __name__ == "__main__":
    print("人格分析系统 — 端到端测试\n")

    tests = [
        ("average", "average"),
        ("high_neuroticism", "high_neuroticism"),
        ("narcissistic", "high_openness_low_agreeableness"),
    ]

    results = []
    for name, ptype in tests:
        try:
            ok = run_assessment(ptype, verbose=True)
            results.append((name, ok))
        except Exception as e:
            print(f"  异常: {e}")
            results.append((name, False))

    print(f"\n{'='*60}")
    print("结果:")
    all_pass = True
    for name, ok in results:
        s = "PASS" if ok else "FAIL"
        if not ok:
            all_pass = False
        print(f"  [{s}] {name}")

    print(f"\n{'全部通过!' if all_pass else '有测试失败，需要修复'}")
