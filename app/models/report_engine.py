"""报告引擎 — 编排所有评分和反馈，生成完整的分析报告"""

from app.services.feedback_generator import FeedbackGenerator


class ReportEngine:
    def __init__(self):
        self.feedback = FeedbackGenerator()

    def generate(self, all_scores, open_text_responses=None):
        """生成完整的分析报告"""
        report = {}

        # 1. 大五人格画像
        bfi2 = all_scores.get("bfi2") or {}
        if bfi2:
            report["bfi2_profile"] = self._build_bfi2_section(bfi2)

        # 2. 自尊
        rses = all_scores.get("rses") or {}
        if rses:
            report["rses"] = self.feedback.get_rses_feedback(rses)

        # 3. 黑暗三联征
        sd3 = all_scores.get("sd3") or {}
        if sd3:
            report["sd3_profile"] = self._build_sd3_section(sd3)

        # 4. 依恋风格
        ecr_r = all_scores.get("ecr_r") or {}
        if ecr_r:
            report["ecr_r"] = self.feedback.get_ecr_r_feedback(ecr_r)

        # 5. 认知风格
        crt = all_scores.get("crt") or {}
        if crt:
            report["crt"] = self.feedback.get_crt_feedback(crt)

        # 6. 控制点
        rotter = all_scores.get("rotter_ie") or {}
        if rotter:
            report["rotter"] = self.feedback.get_rotter_feedback(rotter)

        # 7. 跨维度模式分析
        report["cross_domain_patterns"] = self._detect_patterns(all_scores)

        # 8. 弱项聚焦
        report["weakness_focus"] = self._identify_weaknesses(report)

        # 9. 总览摘要
        report["executive_summary"] = self._generate_summary(report)

        # 10. 发展建议
        report["development_plan"] = self._generate_development_plan(report)

        # 11. 诚实校验
        report = self.feedback.enforce_honesty(report)

        return report

    def _build_bfi2_section(self, bfi2_scores):
        """构建BFI-2详细分析"""
        profile = {}
        normative = bfi2_scores.get("normative", {})
        domain_norms = normative.get("domains", {})
        domains = bfi2_scores.get("domains", {})
        facets = bfi2_scores.get("facets", {})

        domain_names = {
            "openness": {"cn": "开放性", "en": "Openness"},
            "conscientiousness": {"cn": "尽责性", "en": "Conscientiousness"},
            "extraversion": {"cn": "外倾性", "en": "Extraversion"},
            "agreeableness": {"cn": "宜人性", "en": "Agreeableness"},
            "neuroticism": {"cn": "神经质", "en": "Neuroticism"},
        }

        facet_names = {
            "o_intellectual_curiosity": "求知欲",
            "o_aesthetic_sensitivity": "审美感受",
            "o_creative_imagination": "创造性想象",
            "c_organization": "条理性",
            "c_productiveness": "高效性",
            "c_responsibility": "责任感",
            "e_sociability": "社交性",
            "e_assertiveness": "自信主导",
            "e_energy_level": "活力水平",
            "a_compassion": "同情心",
            "a_respectfulness": "尊重他人",
            "a_trust": "信任",
            "n_anxiety": "焦虑",
            "n_depression": "抑郁倾向",
            "n_emotional_volatility": "情绪波动",
        }

        # 各维度分析
        for domain, score in domains.items():
            dn = domain_norms.get(domain, {})
            percentile = dn.get("percentile", 50)
            dn["classification"] = dn.get("classification", "average")

            feedback = self.feedback.get_bfi2_domain_feedback(domain, dn)
            profile[domain] = {
                "name": domain_names.get(domain, {}).get("cn", domain),
                "raw_score": score,
                "percentile": percentile,
                "classification": dn.get("classification", "average"),
                **feedback,
            }

        # 侧面分析
        facet_details = {}
        for f, score in facets.items():
            facet_details[f] = {
                "name": facet_names.get(f, f),
                "score": score,
            }

        return {
            "domains": profile,
            "facets": facet_details,
            "normative": normative,
        }

    def _build_sd3_section(self, sd3_scores):
        """构建SD3分析"""
        profile = {}
        normative = sd3_scores.get("normative", {})
        domains = sd3_scores.get("domains", {})

        trait_names = {
            "narcissism": {"cn": "自恋", "en": "Narcissism"},
            "machiavellianism": {"cn": "马基雅维利主义", "en": "Machiavellianism"},
            "psychopathy": {"cn": "精神病态", "en": "Psychopathy"},
        }

        for trait, score in domains.items():
            tn = normative.get(trait, {})
            percentile = tn.get("percentile", 50)
            tn["classification"] = tn.get("classification", "average")
            tn["percentile"] = percentile

            feedback = self.feedback.get_sd3_feedback(trait, tn)
            profile[trait] = {
                "name": trait_names.get(trait, {}).get("cn", trait),
                "raw_score": score,
                "percentile": percentile,
                **feedback,
            }

        return {
            "traits": profile,
            "primary_trait": sd3_scores.get("primary_trait"),
            "normative": normative,
        }

    def _detect_patterns(self, all_scores):
        """检测跨维度模式"""
        patterns = []

        bfi2 = all_scores.get("bfi2") or {}
        bfi2_norm = bfi2.get("normative", {}).get("domains", {})
        sd3 = all_scores.get("sd3") or {}
        sd3_domains = sd3.get("domains", {})
        sd3_norm = sd3.get("normative", {})

        def pct(d):
            return bfi2_norm.get(d, {}).get("percentile", 50)

        def sd3_pct(t):
            return sd3_norm.get(t, {}).get("percentile", 50) if sd3_norm else 50

        # 模式1：高外倾 + 低宜人 + 高自恋 = 剥削型社交
        if pct("extraversion") >= 70 and pct("agreeableness") <= 30 and sd3_pct("narcissism") >= 70:
            patterns.append({
                "title": "可能的社交支配-剥削模式",
                "severity": "high",
                "description": "高外倾性结合低宜人性和高自恋倾向，构成了一种在社交中占据主导地位但不考虑他人利益的模式。你可能善于社交但并不真正关心你交往的人——这可能导致利用完他人后关系的崩塌。建议你认真反思自己的社交动机。",
            })

        # 模式2：高神经质 + 低尽责性 = 压力管理困难
        if pct("neuroticism") >= 70 and pct("conscientiousness") <= 30:
            patterns.append({
                "title": "压力管理薄弱",
                "severity": "high",
                "description": "高神经质意味着你强烈地体验到负面情绪，而低尽责性意味着你缺乏系统的方法来管理生活。这种组合会导致压力不断累积而无法有效应对。建议你从极小的日常习惯开始建立结构化的应对系统。",
            })

        # 模式3：低外倾 + 高神经质 + 高依恋焦虑 = 社交退缩循环
        if pct("extraversion") <= 30 and pct("neuroticism") >= 70:
            ecr = all_scores.get("ecr_r") or {}
            if ecr.get("quadrant") in ("preoccupied", "fearful"):
                patterns.append({
                    "title": "社交退缩-焦虑循环",
                    "severity": "high",
                    "description": "你既渴望亲密关系又害怕社交互动，这种矛盾可能导致你在孤独和焦虑之间反复循环。你可能在短暂尝试社交后因焦虑而退缩，进而加深孤独感和自我怀疑。打破这个循环需要专业帮助。",
                })

        # 模式4：高尽责 + 低外倾 = 孤独的成就者
        if pct("conscientiousness") >= 75 and pct("extraversion") <= 30:
            patterns.append({
                "title": "高效但孤立的模式",
                "severity": "medium",
                "description": "你有很强的执行力和自律，但社交退缩倾向可能导致你的成就无法得到应有的认可，或者在需要团队合作完成更大目标时遇到瓶颈。",
            })

        # 模式5：高开放性 + 低尽责性 = 创意但缺乏落地
        if pct("openness") >= 75 and pct("conscientiousness") <= 30:
            patterns.append({
                "title": "创意丰富但执行力不足",
                "severity": "medium",
                "description": "你有丰富的想法和创造力，但缺乏将想法转化为现实的持续执行力。你的生活可能充满了启动但未完成的项目。建议你为每一个新创意强制设定最小可行性目标。",
            })

        # 模式6：黑暗三联征警告
        high_sd3_traits = []
        for t, s in sd3_domains.items():
            if s >= 3.8:
                high_sd3_traits.append(t)
        if len(high_sd3_traits) >= 2:
            trait_names = {
                "narcissism": "自恋",
                "machiavellianism": "马基雅维利主义",
                "psychopathy": "精神病态",
            }
            names = [trait_names.get(t, t) for t in high_sd3_traits]
            patterns.append({
                "title": "多重黑暗特质警告",
                "severity": "critical",
                "description": f"你在黑暗三联征的多个维度上同时得分较高：{'、'.join(names)}。这种组合表明你在人际互动中可能存在系统性的问题模式——利用、操纵或伤害他人。这是本报告中最严重的警告，强烈建议你认真反思并寻求专业帮助。",
            })

        # 模式7：极端内控 + 高尽责 = 过度自责
        rotter = all_scores.get("rotter_ie") or {}
        if rotter.get("classification") == "internal" and pct("conscientiousness") >= 80:
            patterns.append({
                "title": "过度自责倾向",
                "severity": "medium",
                "description": "你相信一切取决于自己且对自身有极高的标准。这虽然能推动成就，但也可能让你把本不由你负责的失败归咎于自己，导致不必要的内疚和压力。",
            })

        return patterns

    def _identify_weaknesses(self, report):
        """识别并列出所有显著弱项"""
        weaknesses = []

        # 从BFI-2各维度收集风险
        bfi2 = report.get("bfi2_profile", {}).get("domains", {})
        for domain, data in bfi2.items():
            if data.get("classification") in ("very_low", "very_high"):
                # 极端分数都带风险
                for risk in data.get("risks", [])[:2]:
                    weaknesses.append({
                        "source": f"大五人格·{data.get('name', domain)}",
                        "severity": "high" if data["classification"] == "very_low" else "medium",
                        "detail": risk,
                    })

        # 从SD3收集
        sd3 = report.get("sd3_profile", {}).get("traits", {})
        for trait, data in sd3.items():
            if data.get("classification") in ("very_high", "high"):
                for risk in data.get("risks", [])[:2]:
                    weaknesses.append({
                        "source": f"黑暗三联征·{data.get('name', trait)}",
                        "severity": "high" if data["classification"] == "very_high" else "medium",
                        "detail": risk,
                    })

        # 从模式分析收集
        for pattern in report.get("cross_domain_patterns", []):
            if pattern["severity"] in ("high", "critical"):
                weaknesses.append({
                    "source": "跨维度模式分析",
                    "severity": pattern["severity"],
                    "detail": pattern["description"],
                })

        # 从自尊
        rses = report.get("rses", {})
        if rses.get("classification") == "low":
            for risk in rses.get("risks", [])[:2]:
                weaknesses.append({
                    "source": "自尊评估",
                    "severity": "medium",
                    "detail": risk,
                })

        return weaknesses

    def _generate_summary(self, report):
        """生成总览摘要"""
        bfi2 = report.get("bfi2_profile", {}).get("domains", {})

        # 识别最高和最低维度
        sorted_domains = sorted(bfi2.items(), key=lambda x: x[1].get("percentile", 50), reverse=True)

        highest = sorted_domains[:2] if len(sorted_domains) >= 2 else sorted_domains
        lowest = sorted_domains[-2:] if len(sorted_domains) >= 2 else []

        sd3 = report.get("sd3_profile", {})
        patterns = report.get("cross_domain_patterns", [])
        critical_patterns = [p for p in patterns if p["severity"] == "critical"]
        high_patterns = [p for p in patterns if p["severity"] == "high"]

        parts = []

        # 开头：诚实基调
        parts.append("以下是对你人格和心理特征的客观分析。请理解：没有任何人格特征本身是'好'或'坏'的——每种特征在不同环境中都有优势和劣势。本报告的目的不是评判你，而是帮助你看到你可能看不到的自我面向。")

        # 核心人格特征
        if highest and lowest:
            parts.append(
                f"你的人格最突出的维度是{'和'.join([h[1].get('name', '') for h in highest])}，"
                f"而相对最弱的是{'和'.join([l[1].get('name', '') for l in lowest])}。"
                f"这个组合形塑了你独特的行为模式和生活体验。"
            )

        # 人际关系模式
        e_pct = bfi2.get("extraversion", {}).get("percentile", 50)
        a_pct = bfi2.get("agreeableness", {}).get("percentile", 50)
        if e_pct >= 70 and a_pct <= 30:
            parts.append("在人际关系中，你倾向于主动接触他人但缺乏合作和妥协的意愿。这是一种可能让你在短期获利但长期导致关系破裂的模式。")
        elif e_pct <= 30 and a_pct >= 70:
            parts.append("你在人际关系中温和友善但不主动。你可能是别人眼中'安静的好人'，但你的社交圈可能因缺乏主动拓展而较小。")
        elif e_pct >= 65 and a_pct >= 60:
            parts.append("你在人际关系中兼具主动性和合作性——这是社交能力最强的人格组合之一。")

        # 情绪状况
        n_pct = bfi2.get("neuroticism", {}).get("percentile", 50)
        rses_data = report.get("rses", {})
        if n_pct >= 80:
            parts.append("你的情绪系统处于高度敏感状态。你体验到的焦虑、担忧和负面情绪远多于大多数人。这不仅是心理上的负担——长期的高度负面情绪会影响身体健康、决策质量和人际关系。建议将情绪管理作为优先事项，必要时寻求专业帮助。")
        elif n_pct <= 20:
            parts.append("你拥有极强的情绪稳定性，这是你最大的心理资产之一。但请注意：情绪稳定不等于情感丰富。确保你在需要时仍能与自己的感受保持连接。")

        if rses_data.get("classification") == "low":
            parts.append("你的自尊水平偏低。这种自我认知偏差可能潜移默化地影响着你几乎所有的人生决策——从职业选择到伴侣选择。低自尊不是一个'性格问题'，而是可以被改变的认知模式。")

        # 黑暗特质警告
        if sd3:
            sd3_traits = sd3.get("traits", {})
            critical_traits = [t for t, d in sd3_traits.items() if d.get("classification") == "very_high"]
            if critical_traits:
                names = [sd3_traits.get(t, {}).get("name", t) for t in critical_traits]
                parts.append(
                    f"特别提示：你在{'和'.join(names)}维度上得分极高。"
                    f"这些特质在专业心理学中被视为'社会不适应'特质，与长期的人际关系问题和职业风险相关。"
                    f"这是我们不会为了讨好你而软化的发现——请认真对待。"
                )

        # 关键模式
        if critical_patterns:
            parts.append(critical_patterns[0]["description"])
        elif high_patterns:
            parts.append(high_patterns[0]["description"])

        return {
            "paragraphs": parts,
            "tone": "direct",  # 标记为直接风格
        }

    def _generate_development_plan(self, report):
        """生成发展建议"""
        recommendations = []

        # 从各维度收集建议
        bfi2 = report.get("bfi2_profile", {}).get("domains", {})
        for domain, data in bfi2.items():
            for rec in data.get("recommendations", [])[:1]:
                recommendations.append({
                    "domain": data.get("name", domain),
                    "recommendation": rec,
                })

        # 从SD3收集
        sd3 = report.get("sd3_profile", {}).get("traits", {})
        for trait, data in sd3.items():
            for rec in data.get("recommendations", [])[:1]:
                recommendations.append({
                    "domain": data.get("name", trait),
                    "recommendation": rec,
                })

        # 从自尊
        rses = report.get("rses", {})
        for rec in rses.get("recommendations", [])[:2]:
            recommendations.append({
                "domain": "自尊",
                "recommendation": rec,
            })

        # 按严重性排序：SD3相关优先，然后是非常低/高的维度
        return recommendations
