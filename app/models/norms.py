"""常模管理器 — 将原始分转换为百分位"""

import json
import os
from config import Config
from scipy.stats import norm as normal_dist


class NormsManager:
    def __init__(self):
        self._cache = {}

    def _load_norms(self, instrument_id):
        if instrument_id in self._cache:
            return self._cache[instrument_id]
        path = os.path.join(Config.NORMS_DIR, f"{instrument_id}_norms.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                self._cache[instrument_id] = json.load(f)
        else:
            self._cache[instrument_id] = None
        return self._cache[instrument_id]

    def _z_to_percentile(self, z):
        """z分数转百分位"""
        return round(normal_dist.cdf(z) * 100, 1)

    def _lookup_percentile(self, raw_score, lookup_table):
        """从查表中获取百分位"""
        if not lookup_table:
            return None
        # 查找最近的分数
        keys = sorted(lookup_table.keys(), key=float)
        for i, k in enumerate(keys):
            if raw_score <= float(k):
                return lookup_table[k]
        return lookup_table[keys[-1]]

    def compute_bfi2_norms(self, domains, facets):
        """基于Soto & John (2017)常模计算BFI-2百分位"""
        norms = self._load_norms("bfi2")
        result = {"domains": {}, "facets": {}}

        # 如果没有常模文件，使用基于已发表均值和标准差的近似
        # Soto & John (2017) 报告的均值和标准差（5点量表平均分）
        published_norms = {
            "openness": {"mean": 3.61, "sd": 0.67},
            "conscientiousness": {"mean": 3.68, "sd": 0.72},
            "extraversion": {"mean": 3.39, "sd": 0.80},
            "agreeableness": {"mean": 3.85, "sd": 0.59},
            "neuroticism": {"mean": 2.81, "sd": 0.82},
        }

        for d, score in domains.items():
            if d in published_norms:
                z = (score - published_norms[d]["mean"]) / published_norms[d]["sd"]
                result["domains"][d] = {
                    "percentile": self._z_to_percentile(z),
                    "classification": self._classify(self._z_to_percentile(z)),
                }

        return result

    def compute_sd3_norms(self, domains):
        """SD3常模转换"""
        published_norms = {
            "narcissism": {"mean": 2.88, "sd": 0.71},
            "machiavellianism": {"mean": 2.84, "sd": 0.73},
            "psychopathy": {"mean": 2.05, "sd": 0.64},
        }

        result = {}
        for d, score in domains.items():
            if d in published_norms:
                z = (score - published_norms[d]["mean"]) / published_norms[d]["sd"]
                result[d] = {
                    "percentile": self._z_to_percentile(z),
                    "classification": self._classify(self._z_to_percentile(z)),
                }
        return result

    def rses_raw_to_percentile(self, raw):
        """RSES原始分转百分位（范围10-40，均值约30，SD约5）"""
        z = (raw - 30) / 5
        return self._z_to_percentile(z)

    def compute_ecr_r_norms(self, anxiety, avoidance):
        """ECR-R常模"""
        result = {}
        for label, score, mean, sd in [
            ("anxiety", anxiety, 3.56, 1.06),
            ("avoidance", avoidance, 2.98, 0.92),
        ]:
            z = (score - mean) / sd
            result[label] = {
                "percentile": self._z_to_percentile(z),
                "classification": self._classify(self._z_to_percentile(z)),
            }
        return result

    def crt_raw_to_percentile(self, correct, total):
        """CRT常模（均值约4.2/7，SD约1.8）"""
        if total == 0:
            return None
        z = (correct - 4.2) / 1.8
        return self._z_to_percentile(z)

    def rotter_raw_to_percentile(self, external, total):
        """Rotter I-E常模（外控均值约10/23，SD约4）"""
        if total == 0:
            return None
        z = (external - 10) / 4
        # 注意：高外控 -> 高百分位
        return self._z_to_percentile(z)

    def _classify(self, percentile):
        """将百分位转换为分类标签"""
        if percentile >= 95:
            return "very_high"
        elif percentile >= 75:
            return "high"
        elif percentile >= 35:
            return "average"
        elif percentile >= 15:
            return "low"
        else:
            return "very_low"
