"""自适应引擎 — 根据阶段一结果决定后续评估内容"""


class AdaptiveEngine:
    # 阶段二触发规则
    BRANCHING_RULES = [
        {
            "id": "low_agreeableness",
            "condition": {"domain": "agreeableness", "percentile_max": 30},
            "instruments": ["sd3"],
            "priority": 1,
        },
        {
            "id": "high_neuroticism",
            "condition": {"domain": "neuroticism", "percentile_min": 70},
            "instruments": ["ecr_r"],
            "priority": 1,
        },
        {
            "id": "low_conscientiousness",
            "condition": {"domain": "conscientiousness", "percentile_max": 20},
            "instruments": ["crt"],
            "priority": 2,
        },
        {
            "id": "high_openness",
            "condition": {"domain": "openness", "percentile_min": 85},
            "instruments": ["crt"],
            "priority": 2,
        },
    ]

    FALLBACK_INSTRUMENTS = ["rotter_ie"]

    def determine_phase2(self, phase1_scores):
        """根据阶段一分数决定阶段二量表"""
        triggered = set()

        bfi2_scores = phase1_scores.get("bfi2", {})
        bfi2_normative = phase1_scores.get("bfi2_normative", {})

        # 获取各维度的百分位
        for rule in self.BRANCHING_RULES:
            domain = rule["condition"].get("domain")
            pct = self._get_percentile(domain, phase1_scores)

            if pct is None:
                continue

            if "percentile_min" in rule["condition"] and pct >= rule["condition"]["percentile_min"]:
                for inst in rule["instruments"]:
                    triggered.add(inst)

            if "percentile_max" in rule["condition"] and pct <= rule["condition"]["percentile_max"]:
                for inst in rule["instruments"]:
                    triggered.add(inst)

        # 如果没有触发任何分支，使用默认补充量表
        instruments = list(triggered)
        if not instruments:
            instruments = self.FALLBACK_INSTRUMENTS[:]

        # 最多4个额外量表，按优先级
        return instruments[:4]

    def _get_percentile(self, domain, phase1_scores):
        """从阶段一分数中提取某维度的百分位"""
        bfi2 = phase1_scores.get("bfi2", {})
        raw = bfi2.get(domain)
        if raw is None:
            return None

        # 使用常模近似计算百分位
        norms = {
            "openness": (3.61, 0.67),
            "conscientiousness": (3.68, 0.72),
            "extraversion": (3.39, 0.80),
            "agreeableness": (3.85, 0.59),
            "neuroticism": (2.81, 0.82),
        }

        if domain in norms:
            mean, sd = norms[domain]
            from scipy.stats import norm as normal_dist
            z = (raw - mean) / sd
            return round(normal_dist.cdf(z) * 100, 1)

        return None

    def generate_phase3_questions(self, all_scores):
        """根据所有评分生成阶段三的开放式问题"""
        questions = []

        bfi2 = all_scores.get("bfi2", {}) if all_scores else {}
        bfi2_domains = bfi2.get("domains", {}) if bfi2 else {}
        bfi2_norm = bfi2.get("normative", {}) if bfi2 else {}
        bfi2_domains_norm = bfi2_norm.get("domains", {}) if bfi2_norm else {}

        # 针对极端分数生成问题
        extreme_domains = []
        for d, n in bfi2_domains_norm.items():
            pct = n.get("percentile", 50)
            if pct <= 20 or pct >= 80:
                extreme_domains.append((d, pct))

        domain_questions = {
            "neuroticism": {
                "high": [
                    {"text": "描述过去一周让你感到显著担忧或压力的一件事。你是如何应对的？", "instructions": "请具体描述事件和你的应对方式。不用回避负面情绪，如实回答。"},
                    {"text": "回顾你的生活，你认为是什么因素让你容易体验到负面情绪？", "instructions": "可以从成长经历、性格、生活环境等方面思考。"},
                ],
                "low": [
                    {"text": "你通常如何保持情绪稳定？请分享一个面对重大压力时你成功保持冷静的经历。", "instructions": "请具体描述事件及你的应对策略。"},
                ],
            },
            "agreeableness": {
                "low": [
                    {"text": "描述一次最近的争执或冲突。你是如何处理的？回过头看，你会有什么不同的做法？", "instructions": "请如实描述，不必美化自己的行为。"},
                    {"text": "在什么情况下，你最难与他人合作？你认为问题的根源是什么？", "instructions": "请坦诚作答，这不代表评判。"},
                ],
                "high": [
                    {"text": "描述一次你为了维护关系而牺牲自己需求的经历。回过头看，你觉得当时应该怎么做？", "instructions": "请具体描述场景和你的真实感受。"},
                ],
            },
            "conscientiousness": {
                "low": [
                    {"text": "描述你对一件截止日期较远的事情的典型处理方式。请如实谈谈你的拖延习惯。", "instructions": "坦诚最重要。我们想了解真实的行为模式。"},
                ],
                "high": [
                    {"text": "你是否曾因为过度追求完美或秩序而让自己或他人感到压力？请举例说明。", "instructions": "请具体描述场景。"},
                ],
            },
            "openness": {
                "high": [
                    {"text": "你的广泛兴趣和好奇心是否曾让你难以在某件事上深入坚持？请举例。", "instructions": "请描述具体经历。"},
                ],
            },
            "extraversion": {
                "low": [
                    {"text": "描述一个你觉得社交让你精疲力竭的场景。独处对你来说意味着什么？", "instructions": "请如实描述你的感受。"},
                ],
                "high": [
                    {"text": "你是否曾因过于主导或话多而影响了与他人的关系？请回顾具体经历。", "instructions": "请坦诚描述。"},
                ],
            },
        }

        # 选择2-3个针对性的问题
        for d, pct in extreme_domains[:2]:
            level = "high" if pct >= 80 else "low"
            dq = domain_questions.get(d, {}).get(level, [])
            if dq:
                questions.append(dq[0])

        # 如果极端维度不足，添加通用自述题
        if len(questions) < 2:
            questions.append({
                "text": "用你自己的话描述一下，你认为你的性格中最大的优势和最大的弱点分别是什么？",
                "instructions": "请尽可能诚实。这不是自我表扬的机会，而是自我审视的时刻。",
            })

        # 黑暗三联征相关追问
        sd3 = all_scores.get("sd3", {}) if all_scores else {}
        sd3_domains = sd3.get("domains", {}) if sd3 else {}
        if sd3_domains:
            max_trait = max(sd3_domains, key=sd3_domains.get)
            if sd3_domains[max_trait] >= 3.5:
                questions.append({
                    "text": f"你在某些人格特质量表上得分较高。请回想一下，是否曾因为你的某些行为方式而与他人产生过严重冲突？你如何看待这些反馈？",
                    "instructions": "请如实描述具体事件和你当时的想法。",
                })

        return questions[:5]
