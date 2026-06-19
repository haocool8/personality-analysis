"""评分引擎 — 所有量表的原始分计算与常模转换"""


class ScoringEngine:
    def __init__(self, norms_manager=None):
        self.norms = norms_manager

    def _reverse_score(self, raw, max_points):
        return (max_points + 1) - raw

    def _sum_items(self, items, responses, max_points):
        """计算一组题目的总分，自动处理反向计分"""
        total = 0
        count = 0
        for item in items:
            item_id = item["id"]
            if item_id not in responses:
                continue
            score = responses[item_id]
            if item.get("reverse_keyed", False):
                score = self._reverse_score(score, max_points)
            total += score
            count += 1
        if count == 0:
            return None
        return total / count  # 返回平均分便于跨量表比较

    def score_bfi2(self, responses, instrument):
        """BFI-2 评分：5维度 + 15侧面"""
        max_pts = instrument["response_scale"]["points"]

        # 按领域和侧面分组
        domain_items = {d: [] for d in instrument["domains"]}
        facet_items = {f: [] for f in instrument["facets"]}

        for item in instrument["items"]:
            domain_items[item["domain"]].append(item)
            if "facet" in item:
                facet_items[item["facet"]].append(item)

        domains = {}
        for d, items in domain_items.items():
            score = self._sum_items(items, responses, max_pts)
            if score is not None:
                domains[d] = round(score, 2)

        facets = {}
        for f, items in facet_items.items():
            score = self._sum_items(items, responses, max_pts)
            if score is not None:
                facets[f] = round(score, 2)

        result = {"domains": domains, "facets": facets}

        if self.norms:
            result["normative"] = self.norms.compute_bfi2_norms(domains, facets)

        return result

    def score_rses(self, responses, instrument):
        """Rosenberg 自尊量表评分"""
        max_pts = instrument["response_scale"]["points"]
        total = 0
        count = 0
        for item in instrument["items"]:
            if item["id"] not in responses:
                continue
            score = responses[item["id"]]
            if item.get("reverse_keyed", False):
                score = self._reverse_score(score, max_pts)
            total += score
            count += 1

        if count == 0:
            return {"raw": None, "classification": "unknown"}

        raw = total
        # 10题，每题1-4分，范围10-40
        classification = "low"
        if raw >= 30:
            classification = "high"
        elif raw >= 20:
            classification = "average"

        result = {"raw": raw, "classification": classification}

        if self.norms:
            result["percentile"] = self.norms.rses_raw_to_percentile(raw)

        return result

    def score_sd3(self, responses, instrument):
        """SD3 黑暗三联征评分"""
        max_pts = instrument["response_scale"]["points"]

        domain_items = {d: [] for d in instrument["domains"]}
        for item in instrument["items"]:
            domain_items[item["domain"]].append(item)

        domains = {}
        for d, items in domain_items.items():
            score = self._sum_items(items, responses, max_pts)
            if score is not None:
                domains[d] = round(score, 2)

        result = {"domains": domains}

        # 确定主要黑暗特质
        if domains:
            primary = max(domains, key=domains.get)
            result["primary_trait"] = primary

        if self.norms:
            result["normative"] = self.norms.compute_sd3_norms(domains)

        return result

    def score_ecr_r(self, responses, instrument):
        """ECR-R 依恋风格评分"""
        max_pts = instrument["response_scale"]["points"]

        anxiety_items = []
        avoidance_items = []
        for item in instrument["items"]:
            if item.get("subscale") == "anxiety":
                anxiety_items.append(item)
            elif item.get("subscale") == "avoidance":
                avoidance_items.append(item)

        anxiety = self._sum_items(anxiety_items, responses, max_pts)
        avoidance = self._sum_items(avoidance_items, responses, max_pts)

        if anxiety is None or avoidance is None:
            return {"anxiety": anxiety, "avoidance": avoidance, "quadrant": "unknown"}

        anxiety = round(anxiety, 2)
        avoidance = round(avoidance, 2)

        # 象限分类（使用中位数 3.5 作为分界）
        mid = (max_pts + 1) / 2
        if anxiety < mid and avoidance < mid:
            quadrant = "secure"
            quadrant_cn = "安全型"
        elif anxiety >= mid and avoidance < mid:
            quadrant = "preoccupied"
            quadrant_cn = "焦虑型（迷恋型）"
        elif anxiety < mid and avoidance >= mid:
            quadrant = "dismissing"
            quadrant_cn = "回避型（疏离型）"
        else:
            quadrant = "fearful"
            quadrant_cn = "恐惧型（混乱型）"

        result = {
            "anxiety": anxiety,
            "avoidance": avoidance,
            "quadrant": quadrant,
            "quadrant_cn": quadrant_cn,
        }

        if self.norms:
            result["normative"] = self.norms.compute_ecr_r_norms(anxiety, avoidance)

        return result

    def score_crt(self, responses, instrument):
        """认知反射测试评分"""
        correct_count = 0
        total = 0
        for item in instrument["items"]:
            if item["id"] not in responses:
                continue
            user_answer = str(responses[item["id"]]).strip()
            correct = str(item.get("correct_answer", "")).strip()
            if user_answer.lower() == correct.lower():
                correct_count += 1
            total += 1

        if total == 0:
            return {"correct": 0, "total": 0, "classification": "unknown"}

        ratio = correct_count / total
        if ratio >= 0.7:
            classification = "analytical"
        elif ratio <= 0.3:
            classification = "intuitive"
        else:
            classification = "balanced"

        result = {
            "correct": correct_count,
            "total": total,
            "ratio": round(ratio, 2),
            "classification": classification,
        }

        if self.norms:
            result["percentile"] = self.norms.crt_raw_to_percentile(correct_count, total)

        return result

    def score_rotter_ie(self, responses, instrument):
        """Rotter I-E 控制点量表评分"""
        external_count = 0
        total = 0
        for item in instrument["items"]:
            if item["id"] not in responses:
                continue
            # 选择外控选项得1分
            choice = responses[item["id"]]
            if choice == item.get("external_choice", "B"):
                external_count += 1
            total += 1

        if total == 0:
            return {"external": None, "total": 0, "classification": "unknown"}

        ratio = external_count / total
        if ratio > 0.6:
            classification = "external"
        elif ratio < 0.4:
            classification = "internal"
        else:
            classification = "balanced"

        result = {
            "external": external_count,
            "total": total,
            "ratio": round(ratio, 2),
            "classification": classification,
        }

        if self.norms:
            result["percentile"] = self.norms.rotter_raw_to_percentile(external_count, total)

        return result
