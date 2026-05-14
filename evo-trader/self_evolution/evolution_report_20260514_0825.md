# 自我进化报告 - 2026-05-14 08:25

## 市场数据
上证指数: 现价4242.57 | 涨跌0.67% | 量比0.99 | 最高4245.07 | 最低4192.31
沪深300: 现价4998.34 | 涨跌1.02% | 量比0.98 | 最高5001.12 | 最低4919.42

## 策略数据
{
  "trade_log": [
    {
      "date": "2026-04-29",
      "time": "13:25",
      "action": "BUY",
      "code": "600030",
      "name": "中信证券",
      "price": 27.18,
      "shares": 300,
      "cost": 8154.0,
      "stop_loss": 26.23,
      "take_profit": 29.35,
      "signal_source": "stock_picker_v2",
      "reason": "主力净流入5.21亿，缩量回踩MA5，区间44%中低位",
      "strategy_id": null,
      "market_temperature": 35,
      "entry_type": "试探"
    }
  ],
  "strategy_state": {
    "pool_size": 20,
    "strategies": [
      {
        "id": 5,
        "gene": {
          "ma_fast": 16,
          "ma_slow": 33,
          "ma_signal": 11,
          "rsi_period": 17,
          "rsi_overbought": 79,
          "rsi_oversold": 32,
          "volume_ma_period": 11,
          "volume_multiplier": 1.1283956903229813,
          "position_size": 0.490137798844865,
          "stop_loss_pct": 0.03080621299991032,
          "take_profit_pct": 0.12779997329820847,
          "max_hold_days": 5,
          "weight_ma_cross": 0.023798007837908423,
          "weight_rsi_signal": 0.0,
          "weight_volume": 0.5616703581256586,
          "weight_trend": 0.41453163403643295
        },
        "fitness": 134.66616805887136,
        "returns": 20.13309904,
        "sharpe": 6.423601464294925,
        "max_drawdown": -0.007988457009570458,
        "win_rate": 0.1898148148148148,
        "trade_count": 7.666666666666667
      },
      {
        "id": 11,
        "gene": {
          "ma_fast": 13,
          "ma_slow": 34,
          "ma_signal": 11,
          "rsi_period": 14,
          "rsi_overbought": 77,
          "rsi_oversold": 34,
          "volume_ma_period": 11,
          "volume_multiplier": 1.2147101206113726,
          "position_size": 0.490137798844865,
          "stop_loss_pct": 0.03080621299991032,
          "take_profit_pct": 0.12779997329820847,
          "max_hold_days": 5,
          "weight_ma_cross": 0.019441954373650594,
          "weight_rsi_signal": 0.0,
          "weight_volume": 0.45886065548379057,
          "weight_trend": 0.5216973901425589
        },
        "fitness": 133.60372821349824,
        "returns": 20.848169513333332,
        "sharpe": 6.215027052746227,
        "max_drawdown": -0.016078394355696714,
        "win_rate": 0.41111111111111115,
        "trade_count": 7.333333333333333
      },
      {
        "id": 16,
        "gene": {
          "ma_fast": 13,
          "ma_slow": 36,
          "ma_signal": 11,
          "rsi_period": 17,
          "rsi_overbought": 77,
          "rsi_oversold": 34,
          "volume_ma_period": 10,
          "volume_multiplier": 1.1283956903229813,
          "position_size": 0.490137798844865,
          "stop_loss_pct": 0.025829528912110076,
          "take_profit_pct": 0.12779997329820847,
          "max_hold_days": 5,
          "weight_ma_cross": 0.018724943099153957,
          "weight_rsi_signal": 0.036879588374530495,
          "weight_volume": 0.4419380633882811,
          "weight_trend": 0.5024574051380345
        },
        "fitness": 133.60372821349824,
        "returns": 20.848169513333332,
        "sharpe": 6.215027052746227,
        "max_drawdown": -0.016078394355696714,
        "win_rate": 0.41111111111111115,
        "trade_count": 7.333333333333333
      },
      {
        "id": 20,
        "gene": {
          "ma_fast": 10,
          "ma_slow": 50,
          "ma_signal": 9,
          "rsi_period": 9,
          "rsi_overbought": 75,
          "rsi_oversold": 28,
          "volume_ma_period": 8,
          "volume_multiplier": 1.63,
          "position_size": 0.53,
          "stop_loss_pct": 0.0459,
          "take_profit_pct": 0.1556,
          "max_hold_days": 10,
          "weight_ma_cross": 0.0349,
          "weight_rsi_signal": 0.1194,
          "weight_volume": 0.4619,
          "weight_trend": 0.3838
        },
        "fitness": 0.0,
        "returns": 0.0,
        "sharpe": 0.0,
        "max_drawdown": 0.0,
        "win_rate": 0.0,
        "trade_count": 0
      },
      {
        "id": 21,
        "gene": {
          "ma_fast": 8,
          "ma_slow": 33,
          "ma_signal": 9,
          "rsi_period": 6,
          "rsi_overbought": 80,
          "rsi_oversold": 30,
          "volume_ma_period": 11,
          "volume_multiplier": 1.97,
          "position_size": 0.55,
          "stop_loss_pct": 0.0442,
          "take_profit_pct": 0.1416,
          "max_hold_days": 3,
          "weight_ma_cross": 0.1465,
          "weight_rsi_signal": 0.1258,
          "weight_volume": 0.2842,
          "weight_trend": 0.4436
        },
        "fitness": 0.0,
        "returns": 0.0,
        "sharpe": 0.0,
        "max_drawdown": 0.0,
        "win_rate": 0.0,
        "trade_count": 0
      },
      {
        "id": 22,
        "gene": {
          "ma_fast": 10,
          "ma_slow": 50,
          "ma_signal": 14,
          "rsi_period": 6,
          "rsi_overbought": 80,
          "rsi_oversold": 28,
          "volume_ma_period": 8,
          "volume_multiplier": 1.6,
          "position_size": 0.53,
          "stop_loss_pct": 0.0214,
          "take_profit_pct": 0.0863,
          "max_hold_days": 3,
          "weight_ma_cross": 0.28,
          "weight_rsi_signal": 0.1758,
          "weight_volume": 0.2651,
          "weight_trend": 0.2791
        },
        "fitness": 0.0,
        "returns": 0.0,
        "sharpe": 0.0,
        "max_drawdown": 0.0,
        "win_rate": 0.0,
        "trade_count": 0
      },
      {
        "id": 23,
        "gene": {
          "ma_fast": 8,
          "ma_slow": 44,
          "ma_signal": 16,
          "rsi_period": 14,
          "rsi_overbought": 77,
          "rsi_oversold": 20,
          "volume_ma_period": 20,
          "volume_multiplier": 1.5,
          "position_size": 0.5,
          "stop_loss_pct": 0.0386,
          "take_profit_pct": 0.158,
          "max_hold_days": 5,
          "weight_ma_cross": 0.0595,
          "weight_rsi_signal": 0.0856,
          "weight_volume": 0.3235,
          "weight_trend": 0.5314
        },
        "fitness": 0.0,
        "returns": 0.0,
        "sharpe": 0.0,
        "max_drawdown": 0.0,
        "win_rate": 0.0,
        "trade_count": 0
      },
      {
        "id": 24,
        "gene": {
          "ma_fast": 5,
          "ma_slow": 36,
          "ma_signal": 9,
          "rsi_period": 6,
          "rsi_overbought": 80,
          "rsi_oversold": 30,
          "volume_ma_period": 20,
          "volume_multiplier": 1.09,
          "position_size": 0.39,
          "stop_loss_pct": 0.047,
          "take_profit_pct": 0.128,
          "max_hold_days": 3,
          "weight_ma_cross": 0.1209,
          "weight_rsi_signal": 0.2123,
          "weight_volume": 0.2118,
          "weight_trend": 0.455
        },
        "fitness": 0.0,
        "returns": 0.0,
        "sharpe": 0.0,
        "max_drawdown": 0.0,
        "win_rate": 0.0,
        "trade_count": 0
      },
      {
        "id": 25,
        "gene": {
          "ma_fast": 13,
          "ma_slow": 40,
          "ma_signal": 11,
          "rsi_period": 17,
          "rsi_overbought": 72,
          "rsi_oversold": 25,
          "volume_ma_period": 10,
          "volume_multiplier": 1.87,
          "position_size": 0.34,
          "stop_loss_pct": 0.0451,
          "take_profit_pct": 0.1103,
          "max_hold_days": 10,
          "weight_ma_cross": 0.1831,
          "weight_rsi_signal": 0.1836,
          "weight_volume": 0.3101,
          "weight_trend": 0.3232
        },
        "fitness": 0.0,
        "returns": 0.0,
        "sharpe": 0.0,
        "max_drawdown": 0.0,
        "win_rate": 0.0,
        "trade_count": 0
      },
      {
        "id": 26,
        "gene": {
          "ma_fast": 20,
          "ma_slow": 44,
          "ma_signal": 9,
          "rsi_period": 12,
          "rsi_overbought": 75,
          "rsi_oversold": 28,
          "volume_ma_period": 5,
          "volume_multiplier": 1.3,
          "position_size": 0.22,
          "stop_loss_pct": 0.0437,
          "take_profit_pct": 0.1204,
          "max_hold_days": 10,
          "weight_ma_cross": 0.0439,
          "weight_rsi_signal": 0.0543,
          "weight_volume": 0.4278,
          "weight_trend": 0.474
        },
        "fitness": 0.0,
        "returns": 0.0,
        "sharpe": 0.0,
        "max_drawdown": 0.0,
        "win_rate": 0.0,
        "trade_count": 0
      },
      {
        "id": 27,
        "gene": {
          "ma_fast": 20,
          "ma_slow": 50,
          "ma_signal": 5,
          "rsi_period": 6,
          "rsi_overbought": 70,
          "rsi_oversold": 20,
          "volume_ma_period": 10,
          "volume_multiplier": 1.92,
          "position_size": 0.52,
          "stop_loss_pct": 0.038,
          "take_profit_pct": 0.1351,
          "max_hold_days": 4,
          "weight_ma_cross": 0.143,
          "weight_rsi_signal": 0.2666,
          "weight_volume": 0.3411,
          "weight_trend": 0.2493
        },
        "fitness": 0.0,
        "returns": 0.0,
        "sharpe": 0.0,
        "max_drawdown": 0.0,
        "win_rate": 0.0,
        "trade_count": 0
      },
      {
        "id": 28,
        "gene": {
          "ma_fast": 20,
          "ma_slow": 44,
          "ma_signal": 11,
          "rsi_period": 12,
          "rsi_overbought": 85,
          "rsi_oversold": 32,
          "volume_ma_period": 20,
          "volume_multiplier": 1.18,
          "position_size": 0.21,
          "stop_loss_pct": 0.0315,
          "take_profit_pct": 0.1481,
          "max_hold_days": 4,
          "weight_ma_cross": 0.1359,
          "weight_rsi_signal": 0.1868,
          "weight_volume": 0.2915,
          "weight_trend": 0.3858
        },
        "fitness": 0.0,
        "returns": 0.0,
        "sharpe": 0.0,
        "max_drawdown": 0.0,
        "win_rate": 0.0,
        "trade_count": 0
      },
      {
        "id": 29,
        "gene": {
          "ma_fast": 20,
          "ma_slow": 36,
          "ma_signal": 7,
          "rsi_period": 9,
          "rsi_overbought": 77,
          "rsi_oversold": 32,
          "volume_ma_period": 20,
          "volume_multiplier": 1.46,
          "position_size": 0.36,
          "stop_loss_pct": 0.0409,
          "take_profit_pct": 0.1176,
          "max_hold_days": 5,
          "weight_ma_cross": 0.1605,
          "weight_rsi_signal": 0.2359,
          "weight_volume": 0.314,
          "weight_trend": 0.2896
        },
        "fitness": 0.0,
        "returns": 0.0,
        "sharpe": 0.0,
        "max_drawdown": 0.0,
        "win_rate": 0.0,
        "trade_count": 0
      },
      {
        "id": 30,
        "gene": {
          "ma_fast": 13,
          "ma_slow": 40,
          "ma_signal": 11,
          "rsi_period": 21,
          "rsi_overbought": 75,
          "rsi_oversold": 20,
          "volume_ma_period": 8,
          "volume_multiplier": 1.35,
          "position_size": 0.54,
          "stop_loss_pct": 0.0541,
          "take_profit_pct": 0.1692,
          "max_hold_days": 7,
          "weight_ma_cross": 0.066,
          "weight_rsi_signal": 0.1199,
          "weight_volume": 0.5183,
          "weight_trend": 0.2959
        },
        "fitness": 0.0,
        "returns": 0.0,
        "sharpe": 0.0,
        "max_drawdown": 0.0,
        "win_rate": 0.0,
        "trade_count": 0
      },
      {
        "id": 31,
        "gene": {
          "ma_fast": 10,
          "ma_slow": 44,
          "ma_signal": 14,
          "rsi_period": 12,
          "rsi_overbought": 75,
          "rsi_oversold": 20,
          "volume_ma_period": 15,
          "volume_multiplier": 1.92,
          "position_size": 0.32,
          "stop_loss_pct": 0.0441,
          "take_profit_pct": 0.1778,
          "max_hold_days": 4,
          "weight_ma_cross": 0.1821,
          "weight_rsi_signal": 0.0263,
          "weight_volume": 0.4101,
          "weight_trend": 0.3815
        },
        "fitness": 0.0,
        "returns": 0.0,
        "sharpe": 0.0,
        "max_drawdown": 0.0,
        "win_rate": 0.0,
        "trade_count": 0
      },
      {
        "id": 32,
        "gene": {
          "ma_fast": 20,
          "ma_slow": 30,
          "ma_signal": 7,
          "rsi_period": 9,
          "rsi_overbought": 80,
          "rsi_oversold": 30,
          "volume_ma_period": 10,
          "volume_multiplier": 1.43,
          "position_size": 0.53,
          "stop_loss_pct": 0.0245,
          "take_profit_pct": 0.1394,
          "max_hold_days": 4,
          "weight_ma_cross": 0.2189,
          "weight_rsi_signal": 0.084,
          "weight_volume": 0.3749,
          "weight_trend": 0.3221
        },
        "fitness": 0.0,
        "returns": 0.0,
        "sharpe": 0.0,
        "max_drawdown": 0.0,
        "win_rate": 0.0,
        "trade_count": 0
      },
      {
        "id": 33,
        "gene": {
          "ma_fast": 16,
          "ma_slow": 44,
          "ma_signal": 7,
          "rsi_period": 6,
          "rsi_overbought": 85,
          "rsi_oversold": 25,
          "volume_ma_period": 8,
          "volume_multiplier": 1.03,
          "position_size": 0.32,
          "stop_loss_pct": 0.0313,
          "take_profit_pct": 0.1709,
          "max_hold_days": 7,
          "weight_ma_cross": 0.1998,
          "weight_rsi_signal": 0.0741,
          "weight_volume": 0.3156,
          "weight_trend": 0.4104
        },
        "fitness": 0.0,
        "returns": 0.0,
        "sharpe": 0.0,
        "max_drawdown": 0.0,
        "win_rate": 0.0,
        "trade_count": 0
      },
      {
        "id": 34,
        "gene": {
          "ma_fast": 10,
          "ma_slow": 50,
          "ma_signal": 7,
          "rsi_period": 12,
          "rsi_overbought": 77,
          "rsi_oversold": 20,
          "volume_ma_period": 11,
          "volume_multiplier": 1.5,
          "position_size": 0.33,
          "stop_loss_pct": 0.0362,
          "take_profit_pct": 0.1653,
          "max_hold_days": 7,
          "weight_ma_cross": 0.1205,
          "weight_rsi_signal": 0.016,
          "weight_volume": 0.4711,
          "weight_trend": 0.3924
        },
        "fitness": 0.0,
        "returns": 0.0,
        "sharpe": 0.0,
        "max_drawdown": 0.0,
        "win_rate": 0.0,
        "trade_count": 0
      },
      {
        "id": 35,
        "gene": {
          "ma_fast": 13,
          "ma_slow": 40,
          "ma_signal": 14,
          "rsi_period": 9,
          "rsi_overbought": 85,
          "rsi_oversold": 20,
          "volume_ma_period": 15,
          "volume_multiplier": 1.95,
          "position_size": 0.58,
          "stop_loss_pct": 0.0337,
          "take_profit_pct": 0.1076,
          "max_hold_days": 4,
          "weight_ma_cross": 0.2107,
          "weight_rsi_signal": 0.14,
          "weight_volume": 0.4116,
          "weight_trend": 0.2377
        },
        "fitness": 0.0,
        "returns": 0.0,
        "sharpe": 0.0,
        "max_drawdown": 0.0,
        "win_rate": 0.0,
        "trade_count": 0
      },
      {
        "id": 36,
        "gene": {
          "ma_fast": 5,
          "ma_slow": 40,
          "ma_signal": 5,
          "rsi_period": 6,
          "rsi_overbought": 85,
          "rsi_oversold": 35,
          "volume_ma_period": 20,
          "volume_multiplier": 1.0,
          "position_size": 0.26,
          "stop_loss_pct": 0.0452,
          "take_profit_pct": 0.1205,
          "max_hold_days": 4,
          "weight_ma_cross": 0.0507,
          "weight_rsi_signal": 0.1692,
          "weight_volume": 0.5007,
          "weight_trend": 0.2794
        },
        "fitness": 0.0,
        "returns": 0.0,
        "sharpe": 0.0,
        "max_drawdown": 0.0,
        "win_rate": 0.0,
        "trade_count": 0
      }
    ]
  }
}

## 大模型分析
```json
{
  "市场环境": {
    "温度评估": "暖意",
    "风险点": [
      "量比接近1，成交未有效放大，上涨动力可能不足",
      "短期涨幅已较大（上证从近期低点反弹约10%~15%），存在回调需求",
      "沪深300逼近5000点心理关口，突破需要增量资金配合"
    ],
    "建议仓位": "30%~40%",
    "说明": "今日指数温和上涨，量能持平，市场情绪偏暖但未过热。策略池20个策略中多数未发出信号，表明系统性机会有限。从量价结构看，市场处于震荡上行通道，但量能不足暗示短期可能震荡整理。建议保持灵活仓位，以试探性仓位为主，等待明确放量突破信号。"
  },
  "策略优化": {
    "止损优化": {
      "建议值": "26.80（当前成本价27.18）或-1.4%",
      "理由": "原止损26.23（-3.5%）已过去两周，若股价未明显上涨，建议上移止损至成本价附近以保护本金。参考近期最低价（4月29日至今未知，但可假设未创新低），若股价低于26.80则可能趋势转弱，执行保护性止损。"
    },
    "止盈优化": {
      "建议值": "28.80（+6%）或采用动态跟踪止盈（如移动均线MA10）",
      "理由": "原止盈29.35（+8%）较固定，可调低至28.80（+6%），因当前市场环境非强势单边，适度锁定利润。同时可设置移动止盈：若股价创新高后回撤3%则出场。"
    },
    "仓位优化": {
      "建议值": "当前试探仓300股（约占总资金1%），可加仓至600股（2%）",
      "理由": "中信证券作为券商龙头，若大盘持续回暖，券商弹性较大。当前试探仓盈利空间有限，可在股价站稳27.50上方且量能配合时加仓同等仓位，降低均价。若跌破27.00则不加仓，维持原仓。"
    }
  },
  "选股规则优化": {
    "规则调整": "将\"缩量回踩MA5\"改为\"缩量回踩MA10且MACD零轴上方金叉\"，避免过早介入弱势调整；将\"区间44%中低位\"明确量化，调整为\"股价处于过去60日区间的30%~60%\"。",
    "新增条件": [
      "大盘强度过滤：上证指数或沪深300当日涨幅>0.5%且量比>1.0时信号才生效，防止逆势买盘",
      "板块内个股一致性：同板块内至少3只个股出现类似信号（如主力净流入），增强板块效应",
      "止损距离动态化：根据ATR（14）设置止损，初始止损为买入价 - 1.5倍ATR"
    ],
    "删除条件": [
      "删除\"区间44%中低位\"中的固定数值44%，改为根据历史波动率动态调整",
      "删除单一的主力净流入绝对值条件（如5.21亿），改为净流入占比（净流入/成交额比例）>5%"
    ]
  },
  "下一步行动": {
    "关注标的": [
      "600030 中信证券（持仓跟踪，观察能否突破28元整数关口）",
      "601318 中国平安（保险龙头，与券商联动，当前量价配合良好）",
      "000002 万科A（地产有政策宽松预期，近期底部放量）",
      "510050 上证50ETF（作为指数增强工具，若突破可加仓）"
    ],
    "注意事项": [
      "注意本周后续交易日是否出现放量滞涨，防止诱多",
      "若中信证券盘中跌破27.00且放量，需警惕短期调整，考虑减仓或止损",
      "关注5月15日公布的宏观经济数据（如工业增加值、社零），可能影响市场方向"
    ],
    "是否加仓": "观望",
    "具体说明": "当前市场情绪不确定，暂不加仓。建议观察中信证券能否在27.50附近企稳并放量突破28.00。若日内量比>1.2且上证指数站稳4250，可考虑加仓至600股。否则保持原有试探仓位，等待更明确的右侧信号。"
  }
}
```
