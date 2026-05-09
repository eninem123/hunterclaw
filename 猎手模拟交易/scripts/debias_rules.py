"""
猎手系统v3.96+ 认知偏差自检规则
基于教程《AI Agent认知偏差与交易决策纠偏》第9章
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class BiasCheckResult:
    """偏差检查结果"""
    bias_type: str
    severity: str  # "low" | "medium" | "high"
    risk_detected: bool
    message: str
    recommendation: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DebiasingResult:
    """纠偏结果"""
    original_decision: Dict[str, Any]
    bias_checks: Dict[str, BiasCheckResult]
    warnings: List[Dict[str, Any]]
    confidence_adjustment: float
    debiased_decision: Optional[Dict[str, Any]] = None


class ConfirmationBiasRules:
    """确认偏差自检规则"""

    def check(self, decision_context: Dict[str, Any]) -> BiasCheckResult:
        """检查确认偏差"""
        # CB-001: 用户假设验证
        if decision_context.get('user_assumption'):
            user_assumption = decision_context['user_assumption']
            return BiasCheckResult(
                bias_type="confirmation_bias",
                severity="medium",
                risk_detected=True,
                message=f"检测到用户假设：{user_assumption.get('content', '未知')}",
                recommendation="独立验证该假设，搜索公开信息",
                details={
                    "user_confidence": user_assumption.get('confidence'),
                    "timestamp": user_assumption.get('timestamp')
                }
            )

        # CB-002: 反面证据搜索
        if decision_context.get('direction'):
            direction = decision_context['direction']
            if not decision_context.get('contrary_evidence', []):
                return BiasCheckResult(
                    bias_type="confirmation_bias",
                    severity="high",
                    risk_detected=True,
                    message=f"形成{direction}判断但未搜索反面证据",
                    recommendation="强制搜索至少2条反对该判断的证据",
                    details={"direction": direction}
                )

        # CB-003: 置信度分离
        if decision_context.get('user_confidence') and decision_context.get('system_confidence'):
            user_conf = decision_context['user_confidence']
            system_conf = decision_context['system_confidence']
            diff = abs(user_conf - system_conf)

            if diff > 0.2:  # 差异超过20%
                return BiasCheckResult(
                    bias_type="confirmation_bias",
                    severity="high",
                    risk_detected=True,
                    message=f"用户置信度({user_conf})与系统评估({system_conf})差异显著",
                    recommendation="说明差异原因，输出系统独立评估",
                    details={"difference": diff}
                )

        return BiasCheckResult(
            bias_type="confirmation_bias",
            severity="low",
            risk_detected=False,
            message="确认偏差风险较低",
            recommendation="保持当前决策",
            details={}
        )


class AnchoringRules:
    """锚定效应自检规则"""

    def check(self, decision_context: Dict[str, Any]) -> BiasCheckResult:
        """检查锚定效应"""
        # AN-001: 锚点识别
        if decision_context.get('anchor_point'):
            anchor = decision_context['anchor_point']
            return BiasCheckResult(
                bias_type="anchoring",
                severity="high",
                risk_detected=True,
                message=f"检测到锚点：{anchor.get('value', '未知')}",
                recommendation="进行锚点脱钩，独立评估",
                details={
                    "anchor_type": anchor.get('type', 'unknown'),
                    "anchor_source": anchor.get('source', 'unknown')
                }
            )

        # AN-002: 锚点脱钩
        if decision_context.get('decision_based_on_anchor'):
            return BiasCheckResult(
                bias_type="anchoring",
                severity="high",
                risk_detected=True,
                message="决策依赖初始锚点而非客观分析",
                recommendation="执行锚点脱钩，基于当前信息重新评估",
                details={"anchor_value": decision_context.get('anchor_value')}
            )

        # AN-003: 成本价隔离
        if decision_context.get('involves_position') and decision_context.get('cost_price_in_decision'):
            cost_price = decision_context.get('cost_price')
            return BiasCheckResult(
                bias_type="anchoring",
                severity="high",
                risk_detected=True,
                message=f"决策涉及成本价{cost_price}，可能受沉没成本影响",
                recommendation="成本价已隔离，决策基于未来预期而非历史成本",
                details={"cost_price": cost_price}
            )

        # AN-004: 数字建议质疑
        if decision_context.get('user_numeric_suggestion'):
            suggestion = decision_context['user_numeric_suggestion']
            return BiasCheckResult(
                bias_type="anchoring",
                severity="medium",
                risk_detected=True,
                message=f"用户建议具体数值：{suggestion.get('value', '未知')}",
                recommendation="询问依据，评估合理性后决策",
                details={"suggestion_type": suggestion.get('type')}
            )

        return BiasCheckResult(
            bias_type="anchoring",
            severity="low",
            risk_detected=False,
            message="锚定效应风险较低",
            recommendation="保持当前决策",
            details={}
        )


class SunkCostRules:
    """沉没成本自检规则"""

    def check(self, decision_context: Dict[str, Any]) -> BiasCheckResult:
        """检查沉没成本"""
        # SK-001: 成本价影响检测
        cost_price_keywords = ['成本价', '买入价', '已经亏了', '等回本', '不舍得卖', '已经持有很久']
        if decision_context.get('decision_reason'):
            reason = decision_context['decision_reason']
            if any(keyword in reason for keyword in cost_price_keywords):
                return BiasCheckResult(
                    bias_type="sunk_cost",
                    severity="high",
                    risk_detected=True,
                    message=f"决策理由包含沉没成本关键词：{reason}",
                    recommendation="触发零基准评估，基于当前信息重新判断",
                    details={"reason": reason}
                )

        # SK-002: 零基准评估
        if decision_context.get('involves_position') and decision_context.get('holding_days'):
            holding_days = decision_context['holding_days']
            if holding_days > 30:  # 持仓超过30天
                return BiasCheckResult(
                    bias_type="sunk_cost",
                    severity="high",
                    risk_detected=True,
                    message=f"持仓{holding_days}天，可能存在沉没成本影响",
                    recommendation="执行零基准评估：如果今天重新建仓，是否买入？",
                    details={"holding_days": holding_days}
                )

        # SK-003: 回本逻辑检测
        if decision_context.get('decision_reason') and '回本' in decision_context['decision_reason']:
            return BiasCheckResult(
                bias_type="sunk_cost",
                severity="high",
                risk_detected=True,
                message="决策理由包含回本逻辑，这是沉没成本谬误",
                recommendation="回本逻辑应被拒绝，决策基于未来收益而非历史成本",
                details={"reason": decision_context['decision_reason']}
            )

        # SK-004: 持仓时长隔离
        if decision_context.get('involves_position') and decision_context.get('holding_time_in_decision'):
            return BiasCheckResult(
                bias_type="sunk_cost",
                severity="medium",
                risk_detected=True,
                message="决策理由包含持仓时长，持仓时长不应影响决策",
                recommendation="持仓时长已隔离，决策基于当前市场条件",
                details={"holding_time": decision_context['holding_time_in_decision']}
            )

        return BiasCheckResult(
            bias_type="sunk_cost",
            severity="low",
            risk_detected=False,
            message="沉没成本风险较低",
            recommendation="保持当前决策",
            details={}
        )


class OverconfidenceRules:
    """过度自信自检规则"""

    def check(self, decision_context: Dict[str, Any]) -> BiasCheckResult:
        """检查过度自信"""
        # OC-001: 置信度上限
        confidence = decision_context.get('confidence', 0)
        if confidence > 0.85:
            return BiasCheckResult(
                bias_type="overconfidence",
                severity="high",
                risk_detected=True,
                message=f"置信度{confidence}超过建议上限85%",
                recommendation="说明高置信度的依据，否则降低置信度",
                details={"confidence": confidence}
            )

        # OC-002: 单源限制
        if decision_context.get('single_source_only'):
            return BiasCheckResult(
                bias_type="overconfidence",
                severity="medium",
                risk_detected=True,
                message="仅基于单一信息源决策",
                recommendation="要求多源验证，降低置信度",
                details={"source": decision_context.get('source')}
            )

        # OC-003: 样本外验证
        if decision_context.get('new_strategy') and not decision_context.get('out_of_sample_validated'):
            return BiasCheckResult(
                bias_type="overconfidence",
                severity="high",
                risk_detected=True,
                message="新策略未通过样本外验证",
                recommendation="要求样本外验证通过后再使用",
                details={"new_strategy": True}
            )

        # OC-004: 策略衰减监控
        if decision_context.get('strategy_performance') and decision_context.get('performance_below_average'):
            return BiasCheckResult(
                bias_type="overconfidence",
                severity="medium",
                risk_detected=True,
                message=f"策略表现低于历史平均，可能存在衰减",
                recommendation="监控策略衰减，考虑重新评估",
                details={
                    "current_performance": decision_context.get('performance'),
                    "average_performance": decision_context.get('average_performance')
                }
            )

        return BiasCheckResult(
            bias_type="overconfidence",
            severity="low",
            risk_detected=False,
            message="过度自信风险较低",
            recommendation="保持当前决策",
            details={}
        )


class SelectiveAttentionRules:
    """选择性注意自检规则"""

    def check(self, decision_context: Dict[str, Any]) -> BiasCheckResult:
        """检查选择性注意"""
        # SA-001: 信息平衡搜索
        if decision_context.get('important_decision') and decision_context.get('info_balance'):
            positive_ratio = decision_context['info_balance'].get('positive', 0)
            negative_ratio = decision_context['info_balance'].get('negative', 0)

            if positive_ratio > 0 and negative_ratio == 0:
                return BiasCheckResult(
                    bias_type="selective_attention",
                    severity="high",
                    risk_detected=True,
                    message="仅搜索到正面信息，未搜索负面信息",
                    recommendation="强制搜索等量负面信息",
                    details={"positive_ratio": positive_ratio, "negative_ratio": negative_ratio}
                )

            if positive_ratio / negative_ratio > 2:  # 正面:负面 > 2:1
                return BiasCheckResult(
                    bias_type="selective_attention",
                    severity="medium",
                    risk_detected=True,
                    message=f"信息不平衡，正面信息占比过高",
                    recommendation="重新搜索负面信息，降低置信度",
                    details={"ratio": positive_ratio / negative_ratio}
                )

        # SA-002: 反向假设测试
        if decision_context.get('decision_made') and not decision_context.get('reverse_hypothesis_tested'):
            return BiasCheckResult(
                bias_type="selective_attention",
                severity="medium",
                risk_detected=True,
                message="已形成判断但未进行反向假设测试",
                recommendation="假设判断错误，寻找反面证据",
                details={"decision": decision_context.get('decision')}
            )

        # SA-003: 来源多样性
        if decision_context.get('single_source'):
            return BiasCheckResult(
                bias_type="selective_attention",
                severity="high",
                risk_detected=True,
                message="信息来源单一",
                recommendation="要求多源验证，降低置信度",
                details={"source": decision_context.get('source')}
            )

        # SA-004: AI叙事识别
        if decision_context.get('ai_generated_explanation') and not decision_context.get('data_verified'):
            return BiasCheckResult(
                bias_type="selective_attention",
                severity="medium",
                risk_detected=True,
                message="AI生成解释但未验证数据",
                recommendation="标记为AI解释而非事实，要求数据验证",
                details={"explanation_type": decision_context.get('explanation_type')}
            )

        return BiasCheckResult(
            bias_type="selective_attention",
            severity="low",
            risk_detected=False,
            message="选择性注意风险较低",
            recommendation="保持当前决策",
            details={}
        )


class HunterDebiasSystem:
    """猎手系统认知偏差自检系统v3.96+"""

    def __init__(self):
        self.confirmation_rules = ConfirmationBiasRules()
        self.anchoring_rules = AnchoringRules()
        self.sunk_cost_rules = SunkCostRules()
        self.overconfidence_rules = OverconfidenceRules()
        self.selective_attention_rules = SelectiveAttentionRules()

    def check_all(self, decision_context: Dict[str, Any]) -> DebiasingResult:
        """
        检查所有类型的认知偏差

        Args:
            decision_context: 决策上下文

        Returns:
            DebiasingResult: 纠偏结果
        """
        results = {
            'original_decision': decision_context,
            'bias_checks': {},
            'warnings': [],
            'confidence_adjustment': 0.0,
            'debiased_decision': None
        }

        # 执行各类偏差检查
        results['bias_checks']['confirmation'] = self.confirmation_rules.check(decision_context)
        results['bias_checks']['anchoring'] = self.anchoring_rules.check(decision_context)
        results['bias_checks']['sunk_cost'] = self.sunk_cost_rules.check(decision_context)
        results['bias_checks']['overconfidence'] = self.overconfidence_rules.check(decision_context)
        results['bias_checks']['selective_attention'] = self.selective_attention_rules.check(decision_context)

        # 生成警告
        for bias_type, check_result in results['bias_checks'].items():
            if check_result.risk_detected:
                results['warnings'].append({
                    'type': bias_type,
                    'severity': check_result.severity,
                    'message': check_result.message,
                    'recommendation': check_result.recommendation,
                    'details': check_result.details
                })
                # 累加置信度调整（严重程度越高，调整越大）
                severity_map = {'low': 0, 'medium': 0.1, 'high': 0.2}
                severity_score = severity_map.get(check_result.severity, 0)
                results['confidence_adjustment'] -= severity_score

        # 应用纠偏（简化版：记录纠偏建议但不自动修改决策）
        if results['warnings']:
            results['debiased_decision'] = self._apply_debiasing_simplified(decision_context, results['warnings'])

        return DebiasingResult(
            original_decision=decision_context,
            bias_checks=results['bias_checks'],
            warnings=results['warnings'],
            confidence_adjustment=results['confidence_adjustment'],
            debiased_decision=results['debiased_decision']
        )

    def _apply_debiasing_simplified(self, decision_context: Dict[str, Any], warnings: List[Dict]) -> Dict[str, Any]:
        """
        简化的纠偏应用（不自动修改决策，仅生成纠偏后的决策建议）

        Args:
            decision_context: 原始决策
            warnings: 警告列表

        Returns:
            纠偏后的决策建议
        """
        debiased = decision_context.copy()
        debiased['bias_warnings'] = warnings
        severity_map = {'low': 0, 'medium': 0.1, 'high': 0.2}
        debiased['confidence_adjusted'] = decision_context.get('confidence', 1.0) + sum(severity_map.get(w.get('severity', 'low'), 0) for w in warnings)

        # 根据警告类型添加纠偏建议
        for warning in warnings:
            if warning['type'] == 'confirmation_bias':
                debiased['debiasing_actions'] = debiased.get('debiasing_actions', [])
                debiased['debiasing_actions'].append('强制反面证据搜索')
            elif warning['type'] == 'anchoring':
                debiased['debiasing_actions'] = debiased.get('debiasing_actions', [])
                debiased['debiasing_actions'].append('锚点脱钩+独立评估')
            elif warning['type'] == 'sunk_cost':
                debiased['debiasing_actions'] = debiased.get('debiasing_actions', [])
                debiased['debiasing_actions'].append('零基准评估')
            elif warning['type'] == 'overconfidence':
                debiased['debiasing_actions'] = debiased.get('debiasing_actions', [])
                debiased['debiasing_actions'].append('说明置信度依据')
            elif warning['type'] == 'selective_attention':
                debiased['debiasing_actions'] = debiased.get('debiasing_actions', [])
                debiased['debiasing_actions'].append('信息平衡搜索')

        return debiased


# 测试代码
if __name__ == '__main__':
    # 创建测试场景
    system = HunterDebiasSystem()

    # 测试场景1：确认偏差 - 用户假设未验证
    decision_context_1 = {
        'user_assumption': {
            'content': "洲明被收购概率85%",
            'confidence': 0.85,
            'timestamp': '2026-05-01'
        },
        'direction': '买入',
        'user_confidence': 0.85,
        'system_confidence': 0.4
    }

    result_1 = system.check_all(decision_context_1)
    print("=" * 60)
    print("测试场景1：确认偏差 - 用户假设未验证")
    print("=" * 60)
    print(f"原始置信度: {decision_context_1.get('confidence', 1.0)}")
    print(f"置信度调整: {result_1.confidence_adjustment}")
    print(f"检测到偏差: {len(result_1.warnings)} 个")
    for warning in result_1.warnings:
        print(f"\n  [{warning['severity'].upper()}] {warning['type']}")
        print(f"  消息: {warning['message']}")
        print(f"  建议: {warning['recommendation']}")
    print(f"\n纠偏建议: {result_1.debiased_decision.get('debiasing_actions', [])}")
    print()

    # 测试场景2：锚定效应 - 成本价影响
    decision_context_2 = {
        'involves_position': True,
        'cost_price_in_decision': True,
        'cost_price': 25.54,
        'current_price': 25.21,
        'decision_reason': "等回本再卖，已经亏了1.29%"
    }

    result_2 = system.check_all(decision_context_2)
    print("=" * 60)
    print("测试场景2：锚定效应 - 成本价影响")
    print("=" * 60)
    print(f"检测到偏差: {len(result_2.warnings)} 个")
    for warning in result_2.warnings:
        print(f"\n  [{warning['severity'].upper()}] {warning['type']}")
        print(f"  消息: {warning['message']}")
        print(f"  建议: {warning['recommendation']}")
    print(f"\n纠偏建议: {result_2.debiased_decision.get('debiasing_actions', [])}")
    print()

    # 测试场景3：沉没成本 - 回本逻辑
    decision_context_3 = {
        'involves_position': True,
        'holding_days': 45,
        'decision_reason': "再拿拿，等回本"
    }

    result_3 = system.check_all(decision_context_3)
    print("=" * 60)
    print("测试场景3：沉没成本 - 回本逻辑")
    print("=" * 60)
    print(f"检测到偏差: {len(result_3.warnings)} 个")
    for warning in result_3.warnings:
        print(f"\n  [{warning['severity'].upper()}] {warning['type']}")
        print(f"  消息: {warning['message']}")
        print(f"  建议: {warning['recommendation']}")
    print(f"\n纠偏建议: {result_3.debiased_decision.get('debiasing_actions', [])}")
    print()

    # 测试场景4：过度自信 - 置信度超限
    decision_context_4 = {
        'confidence': 0.92,
        'single_source_only': True,
        'source': '某机构研报'
    }

    result_4 = system.check_all(decision_context_4)
    print("=" * 60)
    print("测试场景4：过度自信 - 置信度超限")
    print("=" * 60)
    print(f"原始置信度: {decision_context_4.get('confidence', 1.0)}")
    print(f"置信度调整: {result_4.confidence_adjustment}")
    print(f"检测到偏差: {len(result_4.warnings)} 个")
    for warning in result_4.warnings:
        print(f"\n  [{warning['severity'].upper()}] {warning['type']}")
        print(f"  消息: {warning['message']}")
        print(f"  建议: {warning['recommendation']}")
    print(f"\n纠偏建议: {result_4.debiased_decision.get('debiasing_actions', [])}")
    print()

    # 测试场景5：选择性注意 - 信息不平衡
    decision_context_5 = {
        'important_decision': True,
        'info_balance': {
            'positive': 10,
            'negative': 0
        },
        'decision': '买入'
    }

    result_5 = system.check_all(decision_context_5)
    print("=" * 60)
    print("测试场景5：选择性注意 - 信息不平衡")
    print("=" * 60)
    print(f"检测到偏差: {len(result_5.warnings)} 个")
    for warning in result_5.warnings:
        print(f"\n  [{warning['severity'].upper()}] {warning['type']}")
        print(f"  消息: {warning['message']}")
        print(f"  建议: {warning['recommendation']}")
    print(f"\n纠偏建议: {result_5.debiased_decision.get('debiasing_actions', [])}")
