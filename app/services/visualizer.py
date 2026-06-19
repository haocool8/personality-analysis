"""图表数据生成器 — 为前端Chart.js提供数据结构"""


class Visualizer:
    def build_bfi2_radar_data(self, bfi2_profile):
        """BFI-2 五维度雷达图数据"""
        domains = bfi2_profile.get("domains", {})
        domain_order = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]

        labels = [domains.get(d, {}).get("name", d) for d in domain_order if d in domains]
        percentiles = [domains.get(d, {}).get("percentile", 50) for d in domain_order if d in domains]
        raw_scores = [domains.get(d, {}).get("raw_score", 3) for d in domain_order if d in domains]

        return {
            "type": "radar",
            "labels": labels,
            "datasets": [
                {
                    "label": "百分位",
                    "data": percentiles,
                    "backgroundColor": "rgba(233, 69, 96, 0.2)",
                    "borderColor": "rgba(233, 69, 96, 1)",
                    "pointBackgroundColor": "rgba(233, 69, 96, 1)",
                    "borderWidth": 2,
                }
            ],
            "options": {
                "scales": {
                    "r": {
                        "min": 0,
                        "max": 100,
                        "ticks": {"stepSize": 20},
                    }
                },
                "plugins": {
                    "title": {
                        "display": True,
                        "text": "大五人格剖面图（百分位）",
                    }
                },
            },
        }

    def build_bfi2_facets_data(self, bfi2_profile):
        """BFI-2 15侧面条形图数据"""
        facets = bfi2_profile.get("facets", {})

        labels = []
        scores = []
        for f_key, f_data in facets.items():
            labels.append(f_data.get("name", f_key))
            scores.append(f_data.get("score", 3))

        colors = []
        for s in scores:
            if s >= 4:
                colors.append("rgba(233, 69, 96, 0.7)")
            elif s >= 3:
                colors.append("rgba(46, 204, 113, 0.7)")
            else:
                colors.append("rgba(52, 152, 219, 0.7)")

        return {
            "type": "bar",
            "labels": labels,
            "datasets": [
                {
                    "label": "平均分",
                    "data": scores,
                    "backgroundColor": colors,
                    "borderRadius": 4,
                }
            ],
            "options": {
                "indexAxis": "y",
                "scales": {
                    "x": {"min": 1, "max": 5},
                },
                "plugins": {
                    "title": {
                        "display": True,
                        "text": "15个侧面详细得分",
                    }
                },
            },
        }

    def build_sd3_bar_data(self, sd3_profile):
        """SD3 黑暗三联征柱状图"""
        traits = sd3_profile.get("traits", {})

        labels = [v.get("name", k) for k, v in traits.items()]
        scores = [v.get("raw_score", 0) for k, v in traits.items()]
        percentiles = [v.get("percentile", 50) for k, v in traits.items()]

        colors = []
        for pct in percentiles:
            if pct >= 80:
                colors.append("rgba(231, 76, 60, 0.8)")
            elif pct >= 60:
                colors.append("rgba(243, 156, 18, 0.8)")
            else:
                colors.append("rgba(46, 204, 113, 0.6)")

        return {
            "type": "bar",
            "labels": labels,
            "datasets": [
                {
                    "label": "原始分",
                    "data": scores,
                    "backgroundColor": colors,
                    "borderRadius": 4,
                }
            ],
            "options": {
                "scales": {
                    "y": {"min": 1, "max": 5},
                },
                "plugins": {
                    "title": {
                        "display": True,
                        "text": "黑暗三联征得分",
                    }
                },
            },
        }

    def build_attachment_scatter_data(self, ecr_r_data):
        """依恋风格散点图数据"""
        anxiety = ecr_r_data.get("anxiety", 3.5)
        avoidance = ecr_r_data.get("avoidance", 3.5)
        quadrant = ecr_r_data.get("quadrant_cn", "未知")

        return {
            "type": "scatter",
            "point": {"x": anxiety, "y": avoidance},
            "quadrant": quadrant,
            "options": {
                "scales": {
                    "x": {"min": 1, "max": 7, "title": {"text": "焦虑维度"}},
                    "y": {"min": 1, "max": 7, "title": {"text": "回避维度"}},
                },
                "plugins": {
                    "title": {
                        "display": True,
                        "text": f"依恋风格：{quadrant}",
                    },
                    "annotation": {
                        "annotations": {
                            "centerLine": {
                                "type": "line",
                                "xMin": 3.5,
                                "xMax": 3.5,
                                "yMin": 1,
                                "yMax": 7,
                                "borderColor": "rgba(0,0,0,0.3)",
                                "borderDash": [6, 6],
                            },
                            "centerLineY": {
                                "type": "line",
                                "yMin": 3.5,
                                "yMax": 3.5,
                                "xMin": 1,
                                "xMax": 7,
                                "borderColor": "rgba(0,0,0,0.3)",
                                "borderDash": [6, 6],
                            },
                        }
                    },
                },
            },
        }

    def build_all_chart_data(self, all_scores):
        """生成所有图表数据"""
        charts = {}

        bfi2 = all_scores.get("bfi2") or {}
        if bfi2:
            profile = {
                "domains": {},
                "facets": {},
            }
            normative = bfi2.get("normative", {}).get("domains", {})
            domains = bfi2.get("domains", {})
            facets = bfi2.get("facets", {})

            domain_names = {
                "openness": "开放性",
                "conscientiousness": "尽责性",
                "extraversion": "外倾性",
                "agreeableness": "宜人性",
                "neuroticism": "神经质",
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

            for d, score in domains.items():
                dn = normative.get(d, {})
                profile["domains"][d] = {
                    "name": domain_names.get(d, d),
                    "raw_score": score,
                    "percentile": dn.get("percentile", 50),
                    "classification": dn.get("classification", "average"),
                }

            for f, score in facets.items():
                profile["facets"][f] = {
                    "name": facet_names.get(f, f),
                    "score": score,
                }

            charts["bfi2_radar"] = self.build_bfi2_radar_data(profile)
            charts["bfi2_facets"] = self.build_bfi2_facets_data(profile)

        sd3 = all_scores.get("sd3") or {}
        if sd3:
            sd3_traits = {}
            sd3_domains = sd3.get("domains", {})
            sd3_norm = sd3.get("normative", {})
            trait_names = {
                "narcissism": "自恋",
                "machiavellianism": "马基雅维利主义",
                "psychopathy": "精神病态",
            }
            for k, v in sd3_domains.items():
                norm = sd3_norm.get(k, {})
                sd3_traits[k] = {
                    "name": trait_names.get(k, k),
                    "raw_score": v,
                    "percentile": norm.get("percentile", 50),
                }
            charts["sd3_bar"] = self.build_sd3_bar_data({"traits": sd3_traits})

        ecr_r = all_scores.get("ecr_r") or {}
        if ecr_r.get("anxiety") is not None:
            charts["attachment_scatter"] = self.build_attachment_scatter_data(ecr_r)

        return charts
