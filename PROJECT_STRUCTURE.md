# InVesta - 个人财务与投资组合管理系统

一个基于 Streamlit 的全功能个人财务和投资组合管理应用。

## 📋 项目结构

```
InVesta/
├── config.py           # 常量和配置
├── database.py         # 数据库管理类 (DatabaseManager)
├── portfolio.py        # 投资组合分析类 (PortfolioAnalyzer)
├── ui.py              # UI 工具函数
├── app.py             # Streamlit 主应用
├── main.py            # 应用入口
├── check_setup.py     # 设置验证脚本
├── finance.db         # SQLite 数据库
└── README.md          # 项目文档
```

## 🏗️ 架构概述

### 模块化设计

1. **config.py** - 集中管理所有常量和配置
   - 数据库路径和表名
   - 交易类型、收入类别
   - UI 配置和精度设置

2. **database.py** - DatabaseManager 类
   - 统一处理所有数据库操作
   - 提供高级接口（insert_transaction、fetch_investments 等）
   - 自动初始化数据库表

3. **portfolio.py** - PortfolioAnalyzer 类
   - 投资组合聚合和计算
   - 财务指标计算（总资产、现金余额等）
   - 从 yfinance 获取实时股票价格（带缓存）

4. **ui.py** - UI 工具函数
   - 指标卡片显示
   - 空状态显示
   - 确认消息显示

5. **app.py** - Streamlit 应用主体
   - 使用上述模块构建主应用
   - 四个标签页：收入/支出、投资、标签设置、历史管理

6. **main.py** - 应用入口
   - 启动 Streamlit 服务器
   - 处理应用生命周期

## 🚀 运行应用

### 方式 1: 使用 Python
```bash
python main.py
```

### 方式 2: 使用 UV
```bash
uv run main.py
```

### 方式 3: 直接运行 Streamlit
```bash
streamlit run app.py
```

## ✅ 验证设置

运行验证脚本检查所有组件是否正确配置：

```bash
# 使用 Python
python check_setup.py

# 使用 UV
uv run check_setup.py
```

验证脚本检查以下内容：
- ✅ 所有必需文件是否存在
- ✅ 依赖包是否已安装
- ✅ 模块是否可以导入
- ✅ 配置常量是否完整
- ✅ 类和函数是否正确定义
- ✅ 类型提示是否使用

## 📦 依赖包

```
streamlit>=1.0.0
pandas>=1.3.0
plotly>=5.0.0
yfinance>=0.1.0
```

安装所有依赖：
```bash
pip install streamlit pandas plotly yfinance
```

## 💾 数据库

应用使用 SQLite 数据库，包含三个表：

1. **transactions** - 收入/支出记录
   - 日期、类型、金额、分类、标签、备注

2. **investments** - 投资交易记录
   - 日期、股票代码、交易类型、股数、价格、备注

3. **tags** - 支出标签
   - 标签名称

所有表都自动初始化，无需手动设置。

## 🎯 主要功能

### 💰 收入/支出管理
- 记录收入（工资、被动收入等）
- 记录支出（按标签分类）
- 查看交易历史

### 📈 投资管理
- 记录买卖交易
- 实时查看投资组合
- 计算未实现收益（P&L）
- 显示投资组合分配饼图

### 📊 财务指标
- 总资产
- 现金余额
- 当前投资值
- 总未实现收益

### ⚙️ 标签管理
- 创建自定义支出标签
- 查看所有标签
- 按标签分类支出

### 📝 历史管理
- 查看所有交易和投资记录
- 删除错误的记录

## 🔧 代码特点

### 类型注解
所有函数都使用完整的类型注解，提高代码可读性和 IDE 支持。

### 错误处理
- 数据库操作包含异常处理
- yfinance 获取失败时自动使用平均成本作为后备
- 用户操作的验证和反馈

### 性能优化
- Streamlit 缓存用于 yfinance 数据（5 分钟）
- DatabaseManager 连接复用
- 高效的数据库查询

### 模块化设计
- 清晰的关注点分离
- 易于测试和维护
- 易于扩展新功能

## 📝 使用示例

### 添加收入
1. 转到"💰 收入/支出"标签页
2. 在左侧填写收入信息
3. 点击"Add Income"

### 记录投资
1. 转到"📈 Investment"标签页
2. 选择交易类型（Buy/Sell）
3. 输入股票代码、股数、价格
4. 点击"Record Trade"

### 管理标签
1. 转到"⚙️ Tag Settings"标签页
2. 输入新标签名
3. 点击"Add Tag"
4. 点击"Add Expense"时选择标签

## 🐛 故障排除

### 导入错误
- 确保所有依赖包已安装：`pip install streamlit pandas plotly yfinance`
- 检查 Python 版本 >= 3.8

### 数据库错误
- 删除 `finance.db` 文件重新初始化
- 检查文件系统权限

### 股票价格获取失败
- 应用会自动使用平均成本作为备选价格
- 检查网络连接

## 📚 进一步改进建议

1. 添加更多财务指标（ROI、年化收益率等）
2. 数据导出功能（CSV、PDF）
3. 投资目标设置和跟踪
4. 添加支出预算功能
5. 国际化支持（多语言）
6. 黑暗模式主题
7. 移动应用适配

---

**享受使用 InVesta 管理您的个人财务吧！** 💰📈
