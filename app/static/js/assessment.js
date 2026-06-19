/**
 * 评估问卷前端控制器
 */
class AssessmentController {
    constructor() {
        this.sessionId = null;
        this.totalItems = 0;
        this.currentIndex = 0;
        this.phase = 1;
        this.currentAnswer = null;
        this.currentQuestionId = null;
    }

    async init() {
        try {
            const resp = await fetch('/assessment/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
            });
            const data = await resp.json();
            this.sessionId = data.session_id;
            this.phase = data.phase;
            this.totalItems = data.total_items;
            this.currentIndex = data.current_index;
            this.renderQuestion(data.question);
            this.updateProgress(data.current_index, data.total_items);
        } catch (err) {
            this.showError('初始化失败，请刷新页面重试。');
        }
    }

    renderQuestion(question) {
        this.currentQuestionId = question.id;
        const card = document.getElementById('question-card');
        const instructions = document.getElementById('question-instructions');
        const text = document.getElementById('question-text');
        const options = document.getElementById('question-options');
        const btnPrev = document.getElementById('btn-prev');
        const btnNext = document.getElementById('btn-next');

        card.style.display = '';
        document.getElementById('phase-transition').style.display = 'none';
        document.getElementById('completion-message').style.display = 'none';

        instructions.textContent = question.instructions;
        text.innerHTML = `<span class="question-number">第 ${question.number} / ${question.total} 题</span><br>${question.text}`;
        options.innerHTML = '';

        // 根据题型渲染不同组件
        if (question.scale_type === 'likert') {
            this.renderLikertScale(options, question);
        } else if (question.scale_type === 'open_text') {
            this.renderOpenText(options, question);
        } else if (question.scale_type === 'forced_choice') {
            this.renderForcedChoice(options, question);
        }

        // 上一题按钮
        if (this.currentIndex > 0) {
            btnPrev.style.display = '';
            btnPrev.onclick = () => this.navigate('prev');
        } else {
            btnPrev.style.display = 'none';
        }

        // 下一题按钮
        btnNext.textContent = '下一题';
        btnNext.disabled = !this.currentAnswer;
        btnNext.onclick = () => this.submitAnswer();

        // 恢复之前的选择
        if (this.currentAnswer !== null) {
            if (question.scale_type === 'likert' || question.scale_type === 'forced_choice') {
                const radio = options.querySelector(`input[value="${this.currentAnswer}"]`);
                if (radio) radio.checked = true;
            }
        }
    }

    renderLikertScale(container, question) {
        const scaleDiv = document.createElement('div');
        scaleDiv.className = 'likert-scale';

        for (let i = 1; i <= question.scale_points; i++) {
            const label = document.createElement('label');
            label.className = 'likert-option';

            const input = document.createElement('input');
            input.type = 'radio';
            input.name = 'likert';
            input.value = i;
            input.addEventListener('change', () => {
                this.currentAnswer = i;
                document.getElementById('btn-next').disabled = false;
            });

            const btn = document.createElement('span');
            btn.className = 'likert-btn';
            btn.textContent = i;

            label.appendChild(input);
            label.appendChild(btn);
            scaleDiv.appendChild(label);
        }

        container.appendChild(scaleDiv);

        // 标签
        const labelsDiv = document.createElement('div');
        labelsDiv.className = 'likert-labels';
        const labels = question.scale_labels;
        if (labels && Object.keys(labels).length > 0) {
            // 显示两端标签
            const keys = Object.keys(labels).sort();
            const leftSpan = document.createElement('span');
            leftSpan.textContent = labels[keys[0]];
            const rightSpan = document.createElement('span');
            rightSpan.textContent = labels[keys[keys.length - 1]];
            labelsDiv.appendChild(leftSpan);
            for (let i = 1; i < keys.length - 1; i++) {
                const mid = document.createElement('span');
                labelsDiv.appendChild(mid);
            }
            labelsDiv.appendChild(rightSpan);
        }
        container.appendChild(labelsDiv);
    }

    renderOpenText(container, question) {
        const textarea = document.createElement('textarea');
        textarea.className = 'open-text-area';
        textarea.placeholder = '请在此输入你的回答...';
        textarea.addEventListener('input', () => {
            this.currentAnswer = textarea.value;
            document.getElementById('btn-next').disabled = !textarea.value.trim();
            const countEl = document.querySelector('.char-count span');
            if (countEl) {
                countEl.textContent = textarea.value.length;
            }
        });

        if (this.currentAnswer) {
            textarea.value = this.currentAnswer;
        }

        container.appendChild(textarea);

        const countDiv = document.createElement('div');
        countDiv.className = 'char-count';
        countDiv.innerHTML = '已输入 <span>0</span> 字';
        container.appendChild(countDiv);
    }

    renderForcedChoice(container, question) {
        const fcDiv = document.createElement('div');
        fcDiv.className = 'forced-choice';

        ['A', 'B'].forEach(choice => {
            const optionText = choice === 'A' ? question.text_a : question.text_b;
            if (!optionText) return;

            const label = document.createElement('label');
            label.className = 'forced-choice-option';

            const input = document.createElement('input');
            input.type = 'radio';
            input.name = 'forced';
            input.value = choice;
            input.addEventListener('change', () => {
                this.currentAnswer = choice;
                document.getElementById('btn-next').disabled = false;
            });

            const span = document.createElement('span');
            span.className = 'fc-label';
            span.textContent = `${choice}. ${optionText}`;

            label.appendChild(input);
            label.appendChild(span);
            fcDiv.appendChild(label);
        });

        // 恢复之前的选择
        if (this.currentAnswer) {
            const radio = fcDiv.querySelector(`input[value="${this.currentAnswer}"]`);
            if (radio) radio.checked = true;
        }

        container.appendChild(fcDiv);
    }

    async submitAnswer() {
        if (!this.currentAnswer && this.currentAnswer !== 0) return;

        const btnNext = document.getElementById('btn-next');
        btnNext.disabled = true;
        btnNext.textContent = '提交中...';

        try {
            const resp = await fetch('/assessment/answer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    item_id: this._currentQuestionId,
                    score: this.currentAnswer,
                    direction: 'next',
                }),
            });
            const data = await resp.json();

            if (data.phase_complete) {
                this.handlePhaseTransition(data);
            } else if (data.complete) {
                this.handleCompletion(data);
            } else if (data.status === 'ok') {
                this.currentIndex = data.current_index;
                this.totalItems = data.total_items;
                this.currentAnswer = null;
                this.loadQuestion();
            }
        } catch (err) {
            this.showError('提交失败，请重试。');
            btnNext.disabled = false;
            btnNext.textContent = '下一题';
        }
    }

    async navigate(direction) {
        if (direction === 'prev' && this.currentIndex > 0) {
            try {
                await fetch('/assessment/answer', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        session_id: this.sessionId,
                        item_id: this._currentQuestionId,
                        score: this.currentAnswer,
                        direction: 'prev',
                    }),
                });
                this.currentAnswer = null;
                this.loadQuestion();
            } catch (err) {
                this.showError('导航失败，请重试。');
            }
        }
    }

    async loadQuestion() {
        try {
            const resp = await fetch(`/assessment/question?session_id=${this.sessionId}`);
            const data = await resp.json();
            this.currentIndex = data.current_index;
            this.totalItems = data.total_items;
            this.phase = data.phase;
            this.currentAnswer = data.current_answer || null;
            this.renderQuestion(data.question);
            this.updateProgress(data.current_index, data.total_items);
        } catch (err) {
            this.showError('加载题目失败，请刷新页面。');
        }
    }

    handlePhaseTransition(data) {
        const card = document.getElementById('question-card');
        const transition = document.getElementById('phase-transition');
        const title = document.getElementById('phase-transition-title');
        const desc = document.getElementById('phase-transition-desc');
        const btnContinue = document.getElementById('btn-continue');

        card.style.display = 'none';
        transition.style.display = '';

        const phaseNames = { 1: '第一阶段完成', 2: '第二阶段完成' };
        title.textContent = phaseNames[data.phase] || '阶段转换';
        desc.textContent = data.message || '即将进入下一阶段。';

        btnContinue.onclick = async () => {
            transition.style.display = 'none';
            card.style.display = '';
            this.currentAnswer = null;
            await this.loadQuestion();
        };
    }

    handleCompletion(data) {
        document.getElementById('question-card').style.display = 'none';
        document.getElementById('completion-message').style.display = '';

        // 跳转到报告页
        setTimeout(() => {
            window.location.href = data.redirect;
        }, 2000);
    }

    updateProgress(current, total) {
        const pct = total > 0 ? Math.round((current / total) * 100) : 0;
        document.getElementById('progress-fill').style.width = pct + '%';
        document.getElementById('progress-text').textContent = `${current} / ${total}`;

        const phaseLabels = { 1: '第一阶段：人格基础画像', 2: '第二阶段：深入评估', 3: '第三阶段：自述补充' };
        document.getElementById('phase-label').textContent = phaseLabels[this.phase] || '';
    }

    showError(msg) {
        const card = document.getElementById('question-card');
        card.innerHTML = `<div class="text-center text-danger" style="padding: 40px;"><p>${msg}</p></div>`;
    }

    get _currentQuestionId() {
        return this.currentQuestionId || '';
    }
}


// 页面加载时启动
document.addEventListener('DOMContentLoaded', () => {
    // 检查是否是评估页面
    if (document.getElementById('assessment-app')) {
        const controller = new AssessmentController();
        controller.init();
    }
});
