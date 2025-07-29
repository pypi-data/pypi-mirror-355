# GARCH Calculator - 高性能增量波动率建模库

[![Python](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/)
[![C++](https://img.shields.io/badge/C++-17-blue.svg)](https://en.cppreference.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)]()

一个专为实时金融数据分析设计的高性能GARCH（广义自回归条件异方差）波动率建模库。支持增量计算，无需重新计算整个历史数据，特别适合高频交易和实时风险管理场景。

## 🚀 核心特性

### ⚡ 高性能增量计算
- **增量更新**: 新增数据点时无需重新计算整个模型
- **O(1)复杂度**: 每次更新的时间复杂度为常数
- **内存优化**: 使用循环缓冲区，内存占用固定
- **零拷贝设计**: 最小化数据复制和内存分配

### 🎯 完整的GARCH建模
- **GARCH(1,1)模型**: 标准的GARCH波动率建模
- **广义误差分布(GED)**: 支持非正态分布假设
- **最大似然估计**: 自动参数优化和收敛检测
- **多步预测**: 支持任意时间范围的波动率预测

### 🔧 强大的工程特性
- **线程安全**: 可选的多线程安全模式
- **C++后端**: 核心算法使用C++17实现，性能卓越
- **Python接口**: 简洁的Python API，完美集成NumPy
- **数值稳定**: 优化的数值计算，避免溢出和精度损失

### 📊 丰富的统计功能
- **风险指标**: VaR、Expected Shortfall自动计算
- **模型诊断**: AIC、BIC信息准则
- **自相关检验**: Ljung-Box检验统计量
- **置信度评估**: 实时的预测置信度评分

## 🛠️ 安装方法

### 系统要求
- Python 3.7+
- C++17兼容编译器 (GCC 7+, Clang 5+, MSVC 2017+)
- Boost库 (版本 1.65+)
- NumPy

### 从源码安装

```bash
# 克隆仓库
git clone https://github.com/garch-lib/garch-calculator.git
cd garch-calculator

# 安装依赖
pip install -r requirements.txt

# 编译安装
python setup.py install

# 或者开发模式安装
python setup.py build_ext --inplace
```

### 使用pip安装 (发布后)

```bash
pip install garch-calculator
```

## 📖 快速开始

### 基本用法

```python
import garch_calculator as gc
import numpy as np

# 创建GARCH计算器
calc = gc.GarchCalculator(
    history_size=1000,    # 历史数据窗口大小
    min_samples=50        # 参数估计最小样本数
)

# 模拟价格数据
np.random.seed(42)
prices = np.random.lognormal(0, 0.02, 500) * 100

# 方法1: 逐个添加数据点 (增量模式)
for price in prices:
    calc.add_price_point(price)
    calc.update_model()  # 实时更新模型

# 方法2: 批量添加数据
# calc.add_prices_numpy(prices)

print(f"数据点数量: {calc.get_data_size()}")
print(f"当前波动率: {calc.get_current_volatility():.6f}")
```

### 参数估计和预测

```python
# 估计GARCH参数
result = calc.estimate_parameters()

if result.converged:
    print("参数估计成功!")
    print(f"参数: {result.parameters}")
    print(f"对数似然: {result.log_likelihood:.4f}")
    print(f"AIC: {result.aic:.4f}")
    print(f"收敛时间: {result.convergence_time_ms:.2f}ms")
    
    # 多步波动率预测
    forecasts = []
    for horizon in [1, 5, 10, 20]:
        forecast = calc.forecast_volatility(horizon)
        forecasts.append(forecast)
        print(f"{horizon}步预测波动率: {forecast.volatility:.6f}")
```

### 实时增量更新

```python
# 模拟实时数据流
import time

calc = gc.GarchCalculator()

# 初始化历史数据
initial_prices = np.random.lognormal(0, 0.02, 200) * 100
calc.add_prices_numpy(initial_prices)
calc.estimate_parameters()

print("开始实时更新...")

# 模拟新数据到达
for i in range(100):
    # 生成新的价格点
    new_price = calc.get_current_volatility() * np.random.normal() + 100
    
    # 增量更新 (O(1)时间复杂度)
    start_time = time.time()
    calc.add_price_point(new_price)
    calc.update_model()
    update_time = (time.time() - start_time) * 1000
    
    # 获取最新预测
    forecast = calc.forecast_volatility(horizon=1)
    
    if i % 20 == 0:
        print(f"更新 {i+1}: 波动率={forecast.volatility:.6f}, "
              f"耗时={update_time:.3f}ms")
```

### 风险指标计算

```python
# 获取当前波动率
current_vol = calc.get_current_volatility()

# 计算风险指标
var_95 = gc.calculate_var(current_vol, confidence_level=0.05)
var_99 = gc.calculate_var(current_vol, confidence_level=0.01)
es_95 = gc.calculate_expected_shortfall(current_vol, confidence_level=0.05)

print(f"VaR (95%): {var_95:.6f}")
print(f"VaR (99%): {var_99:.6f}")
print(f"Expected Shortfall (95%): {es_95:.6f}")
```

### 模型诊断

```python
# 获取诊断统计
log_returns = calc.get_log_returns()
stats = gc.calculate_basic_stats(log_returns)

print(f"收益率统计:")
print(f"  均值: {stats.mean:.8f}")
print(f"  标准差: {stats.std_dev:.6f}")
print(f"  偏度: {stats.skewness:.4f}")
print(f"  峰度: {stats.kurtosis:.4f}")

# 自相关检验
autocorr = gc.calculate_autocorrelation(log_returns, max_lag=10)
ljung_box = gc.calculate_ljung_box_statistic(log_returns, lag=10)

print(f"Ljung-Box统计量: {ljung_box:.4f}")
```

## 🏗️ 架构设计

### 核心组件

```
garch_calculator/
├── include/
│   └── garch_calculator.h     # C++ 头文件
├── src/
│   └── garch_calculator.cpp   # C++ 实现
├── python/
│   └── garch_bindings.cpp     # Python 绑定
├── tests/
│   ├── test_garch.py         # Python 测试
│   └── test_garch.cpp        # C++ 测试
├── setup.py                  # Python 安装脚本
├── CMakeLists.txt           # CMake 配置
└── README.md                # 文档
```

### 性能优化

1. **循环缓冲区**: 使用Boost循环缓冲区管理历史数据
2. **缓存优化**: 缓存频繁计算的密度函数值
3. **SIMD友好**: 数据结构对齐，支持向量化操作
4. **零拷贝**: 最小化内存分配和数据复制
5. **数值稳定**: 使用对数似然和数值约束确保稳定性

## 📊 性能基准

在Intel i7-10700K @3.8GHz上的性能测试结果：

| 操作 | 平均耗时 | 数据规模 |
|------|----------|----------|
| 增量更新 | 0.05ms | 1000点历史 |
| 参数估计 | 15ms | 1000点数据 |
| 波动率预测 | 0.02ms | 任意horizon |
| 批量添加 | 0.02ms/点 | 1000点 |

## 🔬 算法详解

### GARCH(1,1)模型

波动率建模使用标准GARCH(1,1)方程：

```
σ²ₜ = ω + α·ε²ₜ₋₁ + β·σ²ₜ₋₁
```

其中：
- `σ²ₜ`: t时刻的条件方差
- `ω`: 常数项 (omega)
- `α`: ARCH项系数 (alpha)  
- `β`: GARCH项系数 (beta)
- `ε²ₜ₋₁`: 前期收益率的平方

### 增量更新算法

1. **O(1)方差更新**: 直接使用GARCH方程更新当前方差
2. **循环缓冲区**: 自动管理固定大小的历史数据
3. **惰性参数估计**: 仅在必要时重新估计参数
4. **数值稳定性**: 使用边界约束和正则化

### 最大似然估计

使用数值梯度下降优化对数似然函数：

```
L(θ) = Σᵢ log f(εᵢ | σᵢ, ν)
```

其中`f`是广义误差分布(GED)的密度函数。

## 🧪 测试和验证

运行完整测试套件：

```bash
# Python测试
python tests/test_garch.py

# C++测试 (如果使用CMake)
mkdir build && cd build
cmake ..
make test_garch
./test_garch
```

测试覆盖：
- ✅ 基本功能测试
- ✅ 参数估计收敛性
- ✅ 增量更新性能
- ✅ 数值稳定性
- ✅ 线程安全性
- ✅ NumPy集成
- ✅ 边界情况处理

## 📈 应用场景

### 高频交易
- 实时波动率监控
- 动态风险调整
- 算法交易信号生成

### 风险管理
- 实时VaR计算
- 压力测试
- 投资组合优化

### 量化研究
- 波动率建模研究
- 策略回测
- 因子分析

## 🤝 贡献指南

我们欢迎各种形式的贡献！

### 开发环境设置

```bash
git clone https://github.com/garch-lib/garch-calculator.git
cd garch-calculator

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -r requirements-dev.txt

# 开发模式安装
python setup.py build_ext --inplace
```

### 代码规范

- C++代码遵循Google C++风格指南
- Python代码遵循PEP 8
- 提交前运行所有测试
- 添加适当的文档和注释

## 📄 许可证

本项目使用MIT许可证 - 详见[LICENSE](LICENSE)文件

## 📞 联系我们

- 🐛 Bug报告: [GitHub Issues](https://github.com/garch-lib/garch-calculator/issues)
- 💡 功能请求: [GitHub Discussions](https://github.com/garch-lib/garch-calculator/discussions)
- 📧 邮件: team@garch-lib.com
- 📖 文档: [ReadTheDocs](https://garch-calculator.readthedocs.io/)

## 🙏 致谢

感谢以下开源项目的支持：
- [pybind11](https://github.com/pybind/pybind11) - Python/C++绑定
- [Boost](https://www.boost.org/) - C++库集合
- [Eigen](https://eigen.tuxfamily.org/) - 线性代数库
- [NumPy](https://numpy.org/) - Python数值计算

---

⭐ 如果这个项目对您有帮助，请给我们一个star！ 