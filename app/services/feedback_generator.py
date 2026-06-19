"""反馈文案生成器 — 从模板生成客观、诚实的分析文案"""

import json
import os
import random
from config import Config


class FeedbackGenerator:
    def __init__(self):
        self.templates = self._load_templates()

    def _load_templates(self):
        path = os.path.join(Config.FEEDBACK_DIR, "templates_zh.json")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_bfi2_domain_feedback(self, domain, score_data):
        """为BFI-2的某个维度生成反馈"""
        domain_key = {
            "openness": "openness",
            "conscientiousness": "conscientiousness",
            "extraversion": "extraversion",
            "agreeableness": "agreeableness",
            "neuroticism": "neuroticism",
        }.get(domain, domain)

        classification = score_data.get("classification", "average")
        percentile = score_data.get("percentile", 50)

        tpl = self.templates.get("bfi2", {}).get(domain_key, {}).get(classification)
        if not tpl:
            tpl = self.templates.get("bfi2", {}).get(domain_key, {}).get("average", {})

        # 替换模板变量
        summary = (tpl.get("summary", "") or "").replace("{percentile}", str(int(percentile)))

        return {
            "domain": domain,
            "label": tpl.get("label", ""),
            "classification": classification,
            "percentile": percentile,
            "summary": summary,
            "strengths": tpl.get("strengths", []),
            "risks": tpl.get("risks", []),
            "recommendations": tpl.get("recommendations", []),
            "work_implications": tpl.get("work", ""),
            "relationship_implications": tpl.get("relationship", ""),
        }

    def get_sd3_feedback(self, trait, score_data):
        """为SD3某个特质生成反馈"""
        classification = score_data.get("classification", "average")
        tpl = self.templates.get("sd3", {}).get(trait, {}).get(classification, {})

        return {
            "trait": trait,
            "label": tpl.get("label", ""),
            "classification": classification,
            "percentile": score_data.get("percentile", 50),
            "summary": tpl.get("summary", ""),
            "strengths": tpl.get("strengths", []),
            "risks": tpl.get("risks", []),
            "recommendations": tpl.get("recommendations", []),
            "work_implications": tpl.get("work", ""),
            "relationship_implications": tpl.get("relationship", ""),
        }

    def get_rses_feedback(self, score_data):
        """生成Rosenberg自尊反馈"""
        classification = score_data.get("classification", "average")
        tpl = self.templates.get("rses", {}).get(classification, {})

        return {
            "classification": classification,
            "raw": score_data.get("raw"),
            "percentile": score_data.get("percentile"),
            "label": tpl.get("label", ""),
            "summary": tpl.get("summary", ""),
            "strengths": tpl.get("strengths", []),
            "risks": tpl.get("risks", []),
            "recommendations": tpl.get("recommendations", []),
        }

    def get_ecr_r_feedback(self, score_data):
        """生成依恋风格反馈"""
        quadrant = score_data.get("quadrant", "secure")
        tpl = self.templates.get("ecr_r", {}).get(quadrant, {})

        return {
            "quadrant": quadrant,
            "label": tpl.get("label", quadrant),
            "anxiety": score_data.get("anxiety"),
            "avoidance": score_data.get("avoidance"),
            "summary": tpl.get("summary", ""),
            "strengths": tpl.get("strengths", []),
            "risks": tpl.get("risks", []),
            "recommendations": tpl.get("recommendations", []),
        }

    def get_crt_feedback(self, score_data):
        """生成CRT反馈"""
        classification = score_data.get("classification", "balanced")
        tpl = self.templates.get("crt", {}).get(classification, {})

        return {
            "classification": classification,
            "label": tpl.get("label", ""),
            "correct": score_data.get("correct"),
            "total": score_data.get("total"),
            "summary": tpl.get("summary", ""),
            "strengths": tpl.get("strengths", []),
            "risks": tpl.get("risks", []),
            "recommendations": tpl.get("recommendations", []),
        }

    def get_rotter_feedback(self, score_data):
        """生成Rotter I-E反馈"""
        classification = score_data.get("classification", "balanced")
        tpl = self.templates.get("rotter_ie", {}).get(classification, {})

        return {
            "classification": classification,
            "label": tpl.get("label", ""),
            "external": score_data.get("external"),
            "total": score_data.get("total"),
            "summary": tpl.get("summary", ""),
            "strengths": tpl.get("strengths", []),
            "risks": tpl.get("risks", []),
            "recommendations": tpl.get("recommendations", []),
        }

    def enforce_honesty(self, report):
        """诚实验证：确保报告包含足够的批评性内容"""
        total_strengths = 0
        total_risks = 0
        total_recommendations = 0

        # 统计整个报告中的优势和风险数量
        for section_key in ["bfi2_profile", "sd3_profile", "rses", "ecr_r", "crt", "rotter"]:
            section = report.get(section_key, {})
            if isinstance(section, dict):
                # BFI-2有多个维度
                if section_key == "bfi2_profile":
                    for domain_data in section.values():
                        if isinstance(domain_data, dict):
                            total_strengths += len(domain_data.get("strengths", []))
                            total_risks += len(domain_data.get("risks", []))
                            total_recommendations += len(domain_data.get("recommendations", []))
                else:
                    total_strengths += len(section.get("strengths", []))
                    total_risks += len(section.get("risks", []))
                    total_recommendations += len(section.get("recommendations", []))

        # 1. 风险和弱项至少与优势一样多
        if total_risks < total_strengths:
            report["_honesty_note"] = "注意：本报告的批评性内容少于赞誉性内容。这可能意味着系统需要更严格地审查你的分数。请认真对待已列出的每一条风险。"

        # 2. 检查是否有极端分数但没有对应警告
        report["_honesty_audit"] = {
            "total_strengths": total_strengths,
            "total_risks": total_risks,
            "total_recommendations": total_recommendations,
            "risk_to_strength_ratio": round(total_risks / max(total_strengths, 1), 2),
        }

        return report
