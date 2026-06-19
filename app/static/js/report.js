/**
 * 报告页面控制器
 */

class ReportController {
    constructor(sessionId) {
        this.sessionId = sessionId;
    }

    async init() {
        try {
            const resp = await fetch(`/report/${this.sessionId}/data`);
            const data = await resp.json();

            if (data.error) {
                this.showError(data.error);
                return;
            }

            this.render(data.report, data.charts);
        } catch (err) {
            this.showError('加载报告失败，请刷新页面重试。');
        }
    }

    render(report, charts) {
        const app = document.getElementById('report-app');
        let html = '';

        // 导航
        html += this.buildNav(report);

        // 1. 总览摘要
        html += this.buildExecutiveSummary(report.executive_summary);

        // 2. 大五人格
        html += this.buildBFI2Section(report.bfi2_profile);

        // 3. 黑暗三联征
        if (report.sd3_profile) {
            html += this.buildSD3Section(report.sd3_profile);
        }

        // 4. 自尊
        if (report.rses) {
            html += this.buildRSESSection(report.rses);
        }

        // 5. 依恋
        if (report.ecr_r) {
            html += this.buildECRSection(report.ecr_r);
        }

        // 6. 认知风格
        if (report.crt) {
            html += this.buildCRTSection(report.crt);
        }

        // 7. 控制点
        if (report.rotter) {
            html += this.buildRotterSection(report.rotter);
        }

        // 8. 跨维度模式
        html += this.buildPatternsSection(report.cross_domain_patterns);

        // 9. 弱项聚焦
        html += this.buildWeaknessSection(report.weakness_focus);

        // 10. 发展建议
        html += this.buildDevelopmentSection(report.development_plan);

        app.innerHTML = html;

        // 渲染图表
        ChartRenderer.destroyAll();
        if (charts.bfi2_radar) {
            ChartRenderer.renderRadar('chart-bfi2-radar', charts.bfi2_radar);
        }
        if (charts.bfi2_facets) {
            ChartRenderer.renderHorizontalBar('chart-bfi2-facets', charts.bfi2_facets);
        }
        if (charts.sd3_bar) {
            ChartRenderer.renderSD3Bar('chart-sd3', charts.sd3_bar);
        }
        if (charts.attachment_scatter) {
            ChartRenderer.renderAttachmentScatter('chart-attachment', charts.attachment_scatter);
        }
    }

    buildNav(report) {
        let links = '<div class="report-nav">';
        links += '<a href="#summary">总览</a>';
        if (report.bfi2_profile) links += '<a href="#bfi2">大五人格</a>';
        if (report.sd3_profile) links += '<a href="#sd3">黑暗三联征</a>';
        if (report.rses) links += '<a href="#rses">自尊</a>';
        if (report.ecr_r) links += '<a href="#ecr">依恋</a>';
        if (report.crt) links += '<a href="#crt">认知风格</a>';
        links += '<a href="#patterns">模式分析</a>';
        links += '<a href="#weaknesses">弱项聚焦</a>';
        links += '<a href="#development">发展建议</a>';
        links += '</div>';
        return links;
    }

    buildExecutiveSummary(summary) {
        if (!summary) return '';
        const paras = summary.paragraphs.map(p => `<p>${p}</p>`).join('');
        return `
            <section class="report-section" id="summary">
                <h2>总览摘要</h2>
                <div class="card executive-summary">${paras}</div>
            </section>`;
    }

    buildBFI2Section(profile) {
        if (!profile) return '';
        const domains = profile.domains || {};

        let domainCards = '';
        for (const [key, d] of Object.entries(domains)) {
            const cls = this.scoreClass(d.classification);
            domainCards += `
                <div class="card" id="bfi2-${key}">
                    <h3>${d.name} <span class="score-indicator score-${cls}">${d.label || d.classification}（${d.percentile}百分位）</span></h3>
                    <p style="margin: 12px 0; line-height: 1.8;">${d.summary || ''}</p>
                    ${d.strengths && d.strengths.length ? `<p><strong>优势：</strong></p><ul>${d.strengths.map(s => `<li>${s}</li>`).join('')}</ul>` : ''}
                    ${d.risks && d.risks.length ? `<div class="risk-section"><h4>潜在风险</h4><ul>${d.risks.map(r => `<li>${r}</li>`).join('')}</ul></div>` : ''}
                    ${d.recommendations && d.recommendations.length ? `<p style="margin-top:12px;"><strong>建议：</strong></p><ul>${d.recommendations.map(r => `<li>${r}</li>`).join('')}</ul>` : ''}
                    ${d.work_implications ? `<p style="margin-top:12px;"><strong>工作启示：</strong>${d.work_implications}</p>` : ''}
                    ${d.relationship_implications ? `<p><strong>关系启示：</strong>${d.relationship_implications}</p>` : ''}
                </div>`;
        }

        return `
            <section class="report-section" id="bfi2">
                <h2>大五人格画像</h2>
                <div class="chart-wrapper">
                    <canvas id="chart-bfi2-radar" width="400" height="400"></canvas>
                </div>
                <div class="chart-wrapper" style="max-width: 700px;">
                    <canvas id="chart-bfi2-facets" width="500"></canvas>
                </div>
                <h3 style="margin-top: 32px;">维度详细分析</h3>
                ${domainCards}
            </section>`;
    }

    buildSD3Section(profile) {
        if (!profile) return '';
        const traits = profile.traits || {};

        let traitCards = '';
        for (const [key, t] of Object.entries(traits)) {
            const cls = this.scoreClass(t.classification);
            traitCards += `
                <div class="card">
                    <h3>${t.name} <span class="score-indicator score-${cls}">${t.label || t.classification}（${t.percentile}百分位）</span></h3>
                    <p style="margin: 12px 0; line-height: 1.8;">${t.summary || ''}</p>
                    ${t.strengths && t.strengths.length ? `<p><strong>优势：</strong></p><ul>${t.strengths.map(s => `<li>${s}</li>`).join('')}</ul>` : ''}
                    ${t.risks && t.risks.length ? `<div class="risk-section"><h4>风险警告</h4><ul>${t.risks.map(r => `<li>${r}</li>`).join('')}</ul></div>` : ''}
                    ${t.recommendations && t.recommendations.length ? `<p style="margin-top:12px;"><strong>建议：</strong></p><ul>${t.recommendations.map(r => `<li>${r}</li>`).join('')}</ul>` : ''}
                </div>`;
        }

        return `
            <section class="report-section" id="sd3">
                <h2>黑暗三联征评估</h2>
                <div class="chart-wrapper">
                    <canvas id="chart-sd3" width="400" height="250"></canvas>
                </div>
                <p style="color: var(--color-text-secondary); font-size: 0.9rem; margin-bottom: 16px;">
                    注意：以下分析基于经科学验证的SD3量表。高得分不代表你是'坏人'，但研究表明这些特质与特定的人际和职业风险相关。
                    请以开放的心态阅读。
                </p>
                ${traitCards}
            </section>`;
    }

    buildRSESSection(rses) {
        if (!rses) return '';
        const cls = rses.classification === 'low' ? 'low' : rses.classification === 'high' ? 'high' : 'average';
        return `
            <section class="report-section" id="rses">
                <h2>自尊水平</h2>
                <div class="card">
                    <h3>${rses.label || '自尊'} <span class="score-indicator score-${cls}">原始分：${rses.raw}/40（${rses.percentile || '—'}百分位）</span></h3>
                    <p style="margin: 12px 0; line-height: 1.8;">${rses.summary || ''}</p>
                    ${rses.strengths && rses.strengths.length ? `<p><strong>优势：</strong></p><ul>${rses.strengths.map(s => `<li>${s}</li>`).join('')}</ul>` : ''}
                    ${rses.risks && rses.risks.length ? `<div class="risk-section"><h4>需要注意</h4><ul>${rses.risks.map(r => `<li>${r}</li>`).join('')}</ul></div>` : ''}
                    ${rses.recommendations && rses.recommendations.length ? `<p style="margin-top:12px;"><strong>建议：</strong></p><ul>${rses.recommendations.map(r => `<li>${r}</li>`).join('')}</ul>` : ''}
                </div>
            </section>`;
    }

    buildECRSection(ecr) {
        if (!ecr) return '';
        return `
            <section class="report-section" id="ecr">
                <h2>依恋风格</h2>
                <div class="chart-wrapper">
                    <canvas id="chart-attachment" width="400" height="400"></canvas>
                </div>
                <div class="card">
                    <h3>${ecr.label || ecr.quadrant}</h3>
                    <p style="line-height: 1.8;">${ecr.summary || ''}</p>
                    <p style="margin-top: 12px;">焦虑得分：${ecr.anxiety?.toFixed(1) || '—'} / 7 | 回避得分：${ecr.avoidance?.toFixed(1) || '—'} / 7</p>
                    ${ecr.risks && ecr.risks.length ? `<div class="risk-section"><h4>潜在风险</h4><ul>${ecr.risks.map(r => `<li>${r}</li>`).join('')}</ul></div>` : ''}
                    ${ecr.recommendations && ecr.recommendations.length ? `<p style="margin-top:12px;"><strong>建议：</strong></p><ul>${ecr.recommendations.map(r => `<li>${r}</li>`).join('')}</ul>` : ''}
                </div>
            </section>`;
    }

    buildCRTSection(crt) {
        if (!crt) return '';
        return `
            <section class="report-section" id="crt">
                <h2>认知风格</h2>
                <div class="card">
                    <h3>${crt.label || crt.classification}</h3>
                    <p style="margin: 12px 0;">答对 ${crt.correct}/${crt.total} 题（${crt.percentile || '—'}百分位）</p>
                    <p style="line-height: 1.8;">${crt.summary || ''}</p>
                    ${crt.risks && crt.risks.length ? `<div class="risk-section"><h4>潜在局限</h4><ul>${crt.risks.map(r => `<li>${r}</li>`).join('')}</ul></div>` : ''}
                    ${crt.recommendations && crt.recommendations.length ? `<p style="margin-top:12px;"><strong>建议：</strong></p><ul>${crt.recommendations.map(r => `<li>${r}</li>`).join('')}</ul>` : ''}
                </div>
            </section>`;
    }

    buildRotterSection(rotter) {
        if (!rotter) return '';
        return `
            <section class="report-section">
                <h2>控制点</h2>
                <div class="card">
                    <h3>${rotter.label || rotter.classification}</h3>
                    <p style="margin: 12px 0;">外控选择：${rotter.external}/${rotter.total}</p>
                    <p style="line-height: 1.8;">${rotter.summary || ''}</p>
                    ${rotter.risks && rotter.risks.length ? `<div class="risk-section"><h4>潜在风险</h4><ul>${rotter.risks.map(r => `<li>${r}</li>`).join('')}</ul></div>` : ''}
                    ${rotter.recommendations && rotter.recommendations.length ? `<p style="margin-top:12px;"><strong>建议：</strong></p><ul>${rotter.recommendations.map(r => `<li>${r}</li>`).join('')}</ul>` : ''}
                </div>
            </section>`;
    }

    buildPatternsSection(patterns) {
        if (!patterns || !patterns.length) return '';
        const cards = patterns.map(p => {
            const cls = p.severity === 'critical' ? 'danger' : p.severity === 'high' ? 'warning' : '';
            return `
                <div class="pattern-card" style="${cls === 'danger' ? 'border-left-color: var(--color-danger); background: #fff5f5;' : ''}">
                    <h4>${p.title} ${cls === 'danger' ? '<span class="text-danger">[严重警告]</span>' : ''}</h4>
                    <p>${p.description}</p>
                </div>`;
        }).join('');

        return `
            <section class="report-section" id="patterns">
                <h2>跨维度模式分析</h2>
                <p style="color: var(--color-text-secondary); margin-bottom: 16px;">
                    以下分析基于你多个维度得分的组合。单一维度描述不了你，但维度之间的相互作用可以揭示更深层的行为模式。
                </p>
                ${cards}
                ${patterns.length === 0 ? '<div class="card"><p>未检测到显著的跨维度模式。你的各项人格维度之间没有形成典型的协同或冲突模式。</p></div>' : ''}
            </section>`;
    }

    buildWeaknessSection(weaknesses) {
        if (!weaknesses || !weaknesses.length) return '';
        const items = weaknesses.map(w => {
            const cls = w.severity === 'critical' || w.severity === 'high' ? 'danger' : 'warning';
            return `
                <div class="risk-section" style="${w.severity === 'critical' ? 'border-left-color: #c0392b;' : ''}">
                    <h4>${w.source} <span class="text-${cls}">[${w.severity === 'critical' ? '严重' : w.severity === 'high' ? '重要' : '建议关注'}]</span></h4>
                    <p>${w.detail}</p>
                </div>`;
        }).join('');

        return `
            <section class="report-section" id="weaknesses">
                <h2>弱项与风险聚焦</h2>
                <p style="color: var(--color-text-secondary); margin-bottom: 16px;">
                    以下是根据你的评估结果识别出的需要特别关注的方面。<strong>将其放在显眼位置是刻意的——我们不希望你忽略这些内容。</strong>
                </p>
                ${items}
            </section>`;
    }

    buildDevelopmentSection(plan) {
        if (!plan || !plan.length) return '';
        const items = plan.map(item => `
            <li>
                <strong>${item.domain}</strong>：${item.recommendation}
            </li>`).join('');

        return `
            <section class="report-section" id="development">
                <h2>发展建议</h2>
                <p style="color: var(--color-text-secondary); margin-bottom: 16px;">
                    以下建议基于你的具体分数生成。它们不是空洞的'自我提升'口号，而是针对你特定人格模式的可操作建议。
                </p>
                <ul class="recommendation-list">${items}</ul>
            </section>`;
    }

    scoreClass(classification) {
        const map = {
            'very_high': 'very-high',
            'high': 'high',
            'average': 'average',
            'low': 'low',
            'very_low': 'very-low',
        };
        return map[classification] || 'average';
    }

    showError(msg) {
        document.getElementById('report-app').innerHTML = `
            <div class="card text-center" style="padding: 60px 40px;">
                <h2 style="color: var(--color-danger);">加载失败</h2>
                <p style="margin: 16px 0;">${msg}</p>
                <a href="/" class="btn btn-primary">返回首页</a>
            </div>`;
    }
}


// 页面加载时启动
document.addEventListener('DOMContentLoaded', () => {
    const sessionId = document.querySelector('#report-app')?.dataset?.sessionId;
    // 从URL中提取session_id
    const pathMatch = window.location.pathname.match(/\/report\/(.+)/);
    if (pathMatch) {
        const controller = new ReportController(pathMatch[1]);
        controller.init();
    }
});
