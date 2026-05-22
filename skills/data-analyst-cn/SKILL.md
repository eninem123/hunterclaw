---
name: data-analyst-cn
version: 1.0.23
description: 数据分析助手 - 数据清洗、统计分析、可视化建议。适合：数据分析师、产品经理、运营。
metadata:
  openclaw:
    emoji: "📊"
    requires:
      bins: ["python3"]
---

# 数据分析助手 Skill

快速进行数据清洗、统计分析和可视化。

## 核心功能

| 功能 | 描述 |
|------|------|
| 数据清洗 | 去重、填充、格式化 |
| 统计分析 | 描述统计、相关分析 |
| 可视化 | 图表建议、代码生成 |
| 报告生成 | 自动生成分析报告 |

## 使用方法

### 分析数据

```
分析这个 CSV 文件：sales.csv
```

### 数据清洗

```
清洗这个数据集，处理缺失值和异常值
```

### 生成图表

```
为这些数据生成折线图代码
```

## Python 数据分析模板

### 读取数据

```python
import pandas as pd

# CSV
df = pd.read_csv('data.csv')

# Excel
df = pd.read_excel('data.xlsx', sheet_name='Sheet1')

# JSON
df = pd.read_json('data.json')

# 数据库
import sqlite3
conn = sqlite3.connect('database.db')
df = pd.read_sql('SELECT * FROM table', conn)

# API
import requests
response = requests.get('https://api.example.com/data')
df = pd.DataFrame(response.json())
```

### 数据预览

```python
# 基本信息
print(df.shape)        # 行列数
print(df.columns)      # 列名
print(df.dtypes)       # 数据类型
print(df.info())       # 详细信息

# 查看数据
print(df.head())       # 前 5 行
print(df.tail())       # 后 5 行
print(df.sample(5))    # 随机 5 行

# 描述统计
print(df.describe())   # 数值列统计
print(df.describe(include='all'))  # 所有列
```

### 数据清洗

```python
# 处理缺失值
df.isnull().sum()                    # 统计缺失
df.dropna()                          # 删除缺失行
df.fillna(0)                         # 填充 0
df.fillna(df.mean())                 # 填充均值
df['col'].fillna(df['col'].mode()[0])  # 填充众数

# 处理重复
df.duplicated().sum()                # 统计重复
df.drop_duplicates()                 # 删除重复
df.drop_duplicates(subset=['col'])   # 按列去重

# 数据类型转换
df['date'] = pd.to_datetime(df['date'])
df['price'] = df['price'].astype(float)
df['category'] = df['category'].astype('category')

# 异常值处理
Q1 = df['col'].quantile(0.25)
Q3 = df['col'].quantile(0.75)
IQR = Q3 - Q1
df = df[(df['col'] >= Q1 - 1.5*IQR) & (df['col'] <= Q3 + 1.5*IQR)]

# 字符串处理
df['name'] = df['name'].str.strip()
df['name'] = df['name'].str.lower()
df['name'] = df['name'].str.replace('old', 'new')
```

### 统计分析

```python
# 集中趋势
df['col'].mean()      # 均值
df['col'].median()    # 中位数
df['col'].mode()      # 众数

# 离散程度
df['col'].std()       # 标准差
df['col'].var()       # 方差
df['col'].max() - df['col'].min()  # 极差

# 分布
df['col'].skew()      # 偏度
df['col'].kurt()      # 峰度
df['col'].quantile([0.25, 0.5, 0.75])  # 分位数

# 相关分析
df.corr()             # 相关矩阵
df.corr()['target']   # 与目标的相关性

# 分组统计
df.groupby('category').agg({
    'sales': ['sum', 'mean', 'count'],
    'profit': 'mean'
})

# 交叉表
pd.crosstab(df['col1'], df['col2'])
```

### 时间序列分析

```python
# 日期处理
df['date'] = pd.to_datetime(df['date'])
df = df.set_index('date')

# 时间重采样
df.resample('D').sum()      # 按天
df.resample('W').mean()     # 按周
df.resample('M').sum()      # 按月

# 滚动统计
df['rolling_mean'] = df['col'].rolling(window=7).mean()
df['rolling_std'] = df['col'].rolling(window=7).std()

# 时间差
df['diff'] = df['col'].diff()
df['pct_change'] = df['col'].pct_change()

# 季节分解
from statsmodels.tsa.seasonal import seasonal_decompose
result = seasonal_decompose(df['col'], model='additive', period=12)
result.plot()
```

## 可视化代码

### 基础图表

```python
import matplotlib.pyplot as plt
import seaborn as sns

# 设置中文
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 折线图
plt.figure(figsize=(10, 6))
plt.plot(df['date'], df['value'])
plt.title('趋势图')
plt.xlabel('日期')
plt.ylabel('数值')
plt.show()

# 柱状图
plt.bar(df['category'], df['value'])
plt.xticks(rotation=45)
plt.show()

# 散点图
plt.scatter(df['x'], df['y'], alpha=0.5)
plt.xlabel('X')
plt.ylabel('Y')
plt.show()

# 直方图
plt.hist(df['value'], bins=20, edgecolor='black')
plt.xlabel('数值')
plt.ylabel('频数')
plt.show()

# 箱线图
sns.boxplot(data=df, x='category', y='value')
plt.show()

# 热力图
sns.heatmap(df.corr(), annot=True, cmap='coolwarm', center=0)
plt.show()
```

### 高级图表

```python
# 分组柱状图
df_grouped = df.groupby(['category', 'type'])['value'].sum().unstack()
df_grouped.plot(kind='bar', figsize=(12, 6))
plt.legend(title='类型')
plt.show()

# 小提琴图
sns.violinplot(data=df, x='category', y='value')
plt.show()

# 配对图
sns.pairplot(df[['col1', 'col2', 'col3', 'category']], hue='category')
plt.show()

# 时间序列
fig, ax = plt.subplots(figsize=(14, 6))
ax.plot(df.index, df['value'], label='实际值')
ax.plot(df.index, df['rolling_mean'], label='7日均值', linestyle='--')
ax.fill_between(df.index, df['lower'], df['upper'], alpha=0.2)
ax.legend()
plt.show()
```

## 分析报告模板

```python
def generate_report(df):
    """生成数据分析报告"""
    report = f"""
# 数据分析报告

## 1. 数据概览
- 数据量：{len(df)} 行 × {len(df.columns)} 列
- 时间范围：{df['date'].min()} 至 {df['date'].max()}
- 缺失值：{df.isnull().sum().sum()} 个

## 2. 关键指标
- 总销售额：¥{df['sales'].sum():,.2f}
- 平均订单：¥{df['sales'].mean():,.2f}
- 最高订单：¥{df['sales'].max():,.2f}
- 最低订单：¥{df['sales'].min():,.2f}

## 3. 分布特征
- 偏度：{df['sales'].skew():.2f}
- 峰度：{df['sales'].kurt():.2f}
- 标准差：{df['sales'].std():,.2f}

## 4. Top 5 类别
{df.groupby('category')['sales'].sum().sort_values(ascending=False).head().to_markdown()}

## 5. 趋势分析
- 环比增长：{df['sales'].pct_change().mean()*100:.2f}%
- 月均销售额：¥{df.resample('M', on='date')['sales'].sum().mean():,.2f}

## 6. 建议
1. 重点推广 Top 3 类别
2. 优化低转化品类
3. 关注季节性波动
"""
    return report
```

## 注意事项

- 大数据集注意内存使用
- 处理前备份数据
- 结果需要业务验证
- 可视化要简洁清晰

---

创建：2026-03-12
版本：1.0

## A股数据分析扩展

> 本节提供A股-specific数据获取、技术指标、财务分析和统计建模模板。依赖akshare开源库，无需注册即可获取大部分数据。

---

### A股数据获取模板

#### 实时行情（东方财富）

```python
import akshare as ak

# 全市场实时行情（涨停、跌停、炸板一览）
spot_df = ak.stock_zh_a_spot_em()
print(spot_df[['代码','名称','最新价','涨跌幅','成交量','成交额']].head(10))

# 实时涨跌榜
up_df  = ak.stock_zh_a_up_em()     # 涨停股
down_df = ak.stock_zh_a_down_em()  # 跌停股
```

#### 历史K线

```python
# 日线（支持复权）
df = ak.stock_zh_a_hist(
    symbol="000001",      # 深交所股票加前缀"000001.SZ"或直接传"000001"
    period="daily",
    start_date="20230101",
    end_date="20260101",
    adjust="qfq"           # qfq=前复权 hfq=后复权 None=不复权
)
print(df[['日期','开盘','收盘','最高','最低','成交量','成交额','涨跌幅']].head())

# 周线/月线
wk_df = ak.stock_zh_a_hist(symbol="000001", period="weekly", start_date="20230101", end_date="20260101")
```

#### 分钟级数据

```python
# 分时数据（可用于5min/15min/30min/60min）
min_df = ak.stock_zh_a_minute(symbol="000001", period="5", adjust="qfq")
print(min_df[['datetime","open","close","high","low","volume']].head())
```

#### 财务与情绪指标

```python
# 指数实时行情
index_df = ak.stock_zh_index_spot_em()
print(index_df[index_df['代码'].isin(['000001','399001','399006'])])

# 北向资金（沪深港通）
north_df = ak.stock_em_hsgt_north_net_flow_in()
print(north_df[['日期','沪股通','深股通','北向合计']].tail(10))

#融资融券
margin_df = ak.stock_margin_detail_sz(date="20250107")  # 融资融券明细
short_df  = ak.stock_short_sse(date="20250107")          # 融券余额
```

---

### A股技术指标计算

> 所有指标均基于Pandas+NumPy实现，不依赖talib（方便在无C编译环境的沙盒中运行）。

```python
import pandas as pd
import numpy as np

def calc_ma(df, windows=[5, 10, 20, 60]):
    """移动平均线"""
    for w in windows:
        df[f'ma{w}'] = df['收盘'].rolling(window=w).mean()
    return df

def calc_macd(df, fast=12, slow=26, signal=9):
    """MACD：快线/慢线/信号线"""
    ema_fast = df['收盘'].ewm(span=fast).mean()
    ema_slow = df['收盘'].ewm(span=slow).mean()
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal).mean()
    bar = 2 * (dif - dea)
    df['macd_dif'] = dif
    df['macd_dea'] = dea
    df['macd_bar'] = bar
    return df

def calc_kdj(high, low, close, n=9, m1=3, m2=3):
    """KDJ随机指标"""
    lowest_low = low.rolling(window=n).min()
    highest_high = high.rolling(window=n).max()
    rsv = (close - lowest_low) / (highest_high - lowest_low + 1e-9) * 100
    K = rsv.ewm(com=m1-1).mean()
    D = K.ewm(com=m2-1).mean()
    J = 3*K - 2*D
    return K, D, J

def calc_rsi(close, window=14):
    """RSI相对强弱指标"""
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1/window).mean()
    avg_loss = loss.ewm(alpha=1/window).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    rsi = 100 - 100/(1 + rs)
    return rsi

def calc_bollinger(close, window=20, nbdev=2):
    """布林带"""
    mid = close.rolling(window=window).mean()
    std = close.rolling(window=window).std()
    upper = mid + nbdev * std
    lower = mid - nbdev * std
    return upper, mid, lower

def calc_volume_ratio(df, window=5):
    """量比 = 当前成交量 / 过去N日平均成交量"""
    df['vol_ma'] = df['成交量'].rolling(window=window).mean()
    df['vol_ratio'] = df['成交量'] / df['vol_ma']
    return df

# 使用示例
df = ak.stock_zh_a_hist(symbol="000001", period="daily", 
                          start_date="20240101", end_date="20260101", adjust="qfq")
df = calc_ma(df)
df = calc_macd(df)
df['kdj_K'], df['kdj_D'], df['kdj_J'] = calc_kdj(df['最高'], df['最低'], df['收盘'])
df['rsi'] = calc_rsi(df['收盘'])
df['bb_upper'], df['bb_mid'], df['bb_lower'] = calc_bollinger(df['收盘'])
df = calc_volume_ratio(df)
print(df[['日期','收盘','ma5','ma20','macd_dif','macd_dea','kdj_K','rsi','vol_ratio']].tail(10))
```

---

### A股财务分析模板

```python
# 获取个股财务指标（东方财富）
fin_df = ak.stock_financial_analysis_indicator(symbol="000001", start_date="20230101", end_date="20260101")
# 关键列：摊薄每股收益(摊薄EPS)、净资产收益率(ROE)、销售毛利率、资产负债率
print(fin_df[['报告日期','摊薄每股收益','净资产收益率(%)','销售毛利率(%)','资产负债率(%)']].tail())

# 个股基本信息
info = ak.stock_individual_info_em(symbol="000001")
print(info[info['item'].isin(['总市值','流通市值','市盈率','市净率','市销率'])])# 市盈率动态/静态
pe_df = ak.stock_a_indicator_lg(symbol="000001")
print(pe_df[['日期','动态市盈率','静态市盈率','市净率']].tail())

# 盈利预测（东方财富个股盈利预测）
profit_df = ak.stock_profit_forecast_by_report_em(symbol="000001")
print(profit_df[['年度','预测每股收益','预测净利润同比增长']].head(5))

# 财务评分模板
def financial_score(symbol):
    """综合财务评分（0-100）"""
    info = ak.stock_individual_info_em(symbol=symbol)
    fin  = ak.stock_financial_analysis_indicator(symbol=symbol, 
                                                   start_date="20230101", end_date="20260101")
    latest = fin.iloc[-1]
    
    roe = float(latest.get('净资产收益率(%)', 0) or 0)
    pe  = float(info[info['item']=='市盈率'].iloc[0]['日期'].replace(',',''))  # 此处需优化获取方式
    
    # 简化评分：ROE>15给高分，PE<30给加分
    score = 0
    if roe > 20: score += 40
    elif roe > 15: score += 30
    elif roe > 10: score += 20
    else: score += 5
    
    # PE调整（周期股用PB更准确）
    pb_info = info[info['item']=='市净率']
    if not pb_info.empty:
        pb = float(pb_info.iloc[0]['日期'].replace(',',''))
        if pb < 3: score += 20
        elif pb < 5: score += 10
    
    return min(score, 100)

print(f"综合财务评分: {financial_score('000001')}")
```

---

### 改进统计分析

#### 线性回归与趋势预测

```python
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
import numpy as np

# 一元线性回归：预测下一个交易日收盘价
df['days'] = np.arange(len(df))
X = df[['days']].tail(60)   # 最近60天
y = df['收盘'].tail(60)

model = LinearRegression()
model.fit(X, y)

# 预测明天（day=61）和后天（day=62）
next_days = pd.DataFrame({'days': [61, 62]})
pred = model.predict(next_days)
print(f"明天预测价: {pred[0]:.2f}, 后天预测价: {pred[1]:.2f}")
print(f"趋势系数: {model.coef_[0]:.4f} (正=上涨趋势)")

# R² 拟合优度
r2 = model.score(X, y)
print(f"R² = {r2:.4f}")
```

#### 相关性热力图

```python
import seaborn as sns
import matplotlib.pyplot as plt

# 选取技术指标列做相关性分析
cols = ['收盘','成交量','成交额','涨跌幅','macd_dif','rsi','ma5','ma20']
if all(c in df.columns for c in cols):
    corr = df[cols].corr()
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap='RdYlBu_r', center=0,
                xticklabels=cols, yticklabels=cols)
    plt.title('技术指标相关性热力图')
    plt.tight_layout()
    plt.show()
else:
    print("缺少列，跳过热力图")
```

#### 面板数据分析模板

```python
# 多股票、多时间维度的面板回归示例
# 目的：检验北向资金净流入对股价的影响

# 数据准备：每只股票每日的因子+收益率
panel_data = []
for symbol in ['000001.SZ', '600519.SH', '000002.SZ']:
    daily = ak.stock_zh_a_hist(symbol=symbol, period="daily", 
                               start_date="20240101", end_date="20260101", adjust="qfq")
    daily['symbol'] = symbol
    north = ak.stock_em_hsgt_north_net_flow_in()  # 北向日流入
    daily = daily.merge(north[['日期','北向合计']], on='日期', how='left')
    panel_data.append(daily)

panel_df = pd.concat(panel_data, ignore_index=True)

# 固定效应回归（简化版：用分组均值回归）
# OLS: Return = α + β1 * NorthFlow + β2 * VolumeRatio + ε
import statsmodels.api as sm

X_cols = ['北向合计', '成交量']
X = panel_df[X_cols].fillna(0)
X = sm.add_constant(X)
y = panel_df['涨跌幅'].astype(float)

model = sm.OLS(y, X).fit()
print(model.summary())
```

#### 时间序列预测（ARIMA示例）

```python
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller

# 平稳性检验
result = adfuller(df['收盘'].dropna())
print(f"ADF统计量: {result[0]:.4f}, p值: {result[1]:.4f}")

# 一阶差分后再检验
result2 = adfuller(df['收盘'].diff().dropna())
print(f"差分后ADF p值: {result2[1]:.4f}")

# ARIMA(5,1,2) 模型
model = ARIMA(df['收盘'], order=(5, 1, 2))
arima_result = model.fit()
print(arima_result.summary())

# 预测未来5个交易日
forecast = arima_result.forecast(steps=5)
print("未来5日收盘价预测:")
for i, f in enumerate(forecast, 1):
    print(f"  第{i}天: {f:.2f}")
```

---

### 可视化增强 - A股专用图表

#### K线图+技术指标叠加

```python
import mplfinance as mpf

# 准备数据（mplfinance要求列名为小写+DateTimeIndex）
ohlc = df[['日期','开盘','收盘','最高','最低','成交量']].copy()
ohlc.columns = ['Date','Open','High','Low','Close','Volume']
ohlc['Date'] = pd.to_datetime(ohlc['Date'])
ohlc = ohlc.set_index('Date')

# 自定义均线+MACD叠加
add_plots = [
    mpf.make_addplot(df['ma5'].values,  color='blue',  linestyle='--', width=0.8, panel=0),
    mpf.make_addplot(df['ma20'].values, color='orange', linestyle='--', width=0.8, panel=0),
    mpf.make_addplot(df['macd_dif'].values, color='red',   panel=1, ylabel='MACD'),
    mpf.make_addplot(df['macd_dea'].values, color='green', panel=1),
    mpf.make_addplot(df['macd_bar'].values, type='bar', panel=1),
]

mpf.plot(ohlc, type='candle', style='charles',
         title='000001 日K线 + MA + MACD',
         addplot=add_plots,
         volume=True,
         figsize=(14, 10),
         savefig='kline_with_indicators.png')
```

#### 持仓收益追踪图

```python
# 假设有持仓记录：date, symbol, shares, cost
portfolio = pd.DataFrame({
    'date': pd.date_range('2024-01-01', periods=60, freq='B'),
    'symbol': ['000001'] * 60,
    'shares': [1000] * 60,
    'cost': [10.5] * 60
})

# 对接每日收盘价（需用akshare获取）
cost_history = portfolio.groupby('date').apply(
    lambda x: (x['shares'] * x['cost']).sum()
)

# 累计收益曲线
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
ax1.plot(cost_history.index, cost_history.values, label='持仓成本', color='gray', linestyle='--')
ax2.fill_between(cost_history.index, 0, cost_history.values, alpha=0.3)
ax2.set_ylabel('累计投入金额（元）')
ax1.set_ylabel('持仓成本（元）')
ax1.legend()
ax2.set_title('定投累计成本曲线')
plt.tight_layout()
plt.show()
```

---

### 注意事项

- akshare数据源来自东方财富/同花顺等平台，**不保证数据完整性**，实盘决策前请交叉核对
- 分时数据有节流限制，批量获取时加`time.sleep(0.5)`或使用缓存
- 财务指标中的空值/异常值（如同比异常高）需结合业务逻辑过滤
- K线复权方式影响技术指标精度，**前复权(qfq)最适合技术分析**
