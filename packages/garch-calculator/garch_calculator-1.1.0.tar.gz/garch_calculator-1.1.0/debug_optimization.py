import garch_lib as gc
import pandas as pd
import numpy as np
from arch import arch_model

# 读取数据
df = pd.read_csv('brett.csv')
returns = df['c_scaled'].values
window_data = returns[200:300]  # 100个数据点

print("🔍 深入调试优化算法问题")
print("=" * 60)

# 使用arch库获取参考
arch_model_obj = arch_model(window_data, vol='Garch', p=1, q=1, dist='ged', rescale=False)
arch_result = arch_model_obj.fit(disp='off', show_warning=False)

print(f"arch库参数:")
mu = arch_result.params['mu']
omega = arch_result.params['omega']
alpha = arch_result.params['alpha[1]']
beta = arch_result.params['beta[1]']
nu = arch_result.params['nu']

print(f"  mu: {mu:.6f}")
print(f"  omega: {omega:.6f}")
print(f"  alpha: {alpha:.6f}")
print(f"  beta: {beta:.6f}")
print(f"  nu: {nu:.6f}")
print(f"  似然值: {arch_result.loglikelihood:.6f}")

# 使用去均值数据
residuals = window_data - mu

# 测试1: 检查garch_lib的默认参数
print(f"\n📊 测试1: 检查garch_lib的默认参数")
calc1 = gc.GarchCalculator(history_size=len(residuals) + 10)
calc1.add_returns(residuals.tolist())

# 获取默认参数
default_params = calc1.get_parameters()
print(f"  默认参数: omega={default_params.omega:.6f}, alpha={default_params.alpha:.6f}")
print(f"            beta={default_params.beta:.6f}, nu={default_params.nu:.6f}")

# 计算默认参数的似然值
default_ll = calc1.calculate_log_likelihood()
print(f"  默认参数似然值: {default_ll:.6f}")

# 测试2: 尝试参数估计
print(f"\n📊 测试2: 参数估计过程")
result = calc1.estimate_parameters()
print(f"  估计收敛: {result.converged}")
print(f"  迭代次数: {result.iterations}")
print(f"  估计似然值: {result.log_likelihood:.6f}")
print(f"  估计参数: omega={result.parameters.omega:.6f}, alpha={result.parameters.alpha:.6f}")
print(f"            beta={result.parameters.beta:.6f}, nu={result.parameters.nu:.6f}")

# 检查参数是否真的改变了
estimated_params = calc1.get_parameters()
print(f"  当前参数: omega={estimated_params.omega:.6f}, alpha={estimated_params.alpha:.6f}")
print(f"            beta={estimated_params.beta:.6f}, nu={estimated_params.nu:.6f}")

# 测试3: 手动设置arch库参数并计算似然值
print(f"\n📊 测试3: 手动设置arch库参数")
calc2 = gc.GarchCalculator(history_size=len(residuals) + 10)
calc2.add_returns(residuals.tolist())

arch_params = gc.GarchParameters()
arch_params.omega = omega
arch_params.alpha = alpha
arch_params.beta = beta
arch_params.nu = nu
calc2.set_parameters(arch_params)

arch_ll_garch = calc2.calculate_log_likelihood()
print(f"  arch参数在garch_lib中的似然值: {arch_ll_garch:.6f}")
print(f"  与arch库的差异: {arch_ll_garch - arch_result.loglikelihood:.6f}")

# 测试4: 检查预测值
print(f"\n📊 测试4: 预测值对比")
forecast_default = calc1.forecast_volatility(1)
forecast_arch = calc2.forecast_volatility(1)

print(f"  默认参数预测: {forecast_default.volatility:.6f}")
print(f"  arch参数预测: {forecast_arch.volatility:.6f}")

# arch库预测
arch_forecast = arch_result.forecast(horizon=1, reindex=False)
arch_vol = np.sqrt(arch_forecast.variance.values[-1, 0])
print(f"  arch库预测: {arch_vol:.6f}")

# 测试5: 检查是否是参数估计根本不工作
print(f"\n📊 测试5: 多次参数估计")
for i in range(3):
    calc_test = gc.GarchCalculator(history_size=len(residuals) + 10)
    calc_test.add_returns(residuals.tolist())
    result_test = calc_test.estimate_parameters()
    print(f"  第{i+1}次估计:")
    print(f"    收敛: {result_test.converged}, 迭代: {result_test.iterations}")
    print(f"    似然值: {result_test.log_likelihood:.6f}")
    print(f"    参数: ω={result_test.parameters.omega:.6f}, α={result_test.parameters.alpha:.6f}, β={result_test.parameters.beta:.6f}, ν={result_test.parameters.nu:.6f}")

# 测试6: 检查数据是否正确传递
print(f"\n📊 测试6: 数据检查")
calc3 = gc.GarchCalculator(history_size=len(residuals) + 10)
calc3.add_returns(residuals.tolist())

log_returns = calc3.get_log_returns()
print(f"  数据点数: {len(log_returns)}")
print(f"  前5个数据点: {log_returns[:5]}")
print(f"  后5个数据点: {log_returns[-5:]}")
print(f"  与输入数据一致: {np.allclose(log_returns, residuals.tolist())}")

print(f"\n🔍 结论分析:")
print(f"  1. 默认参数似然值: {default_ll:.2f}")
print(f"  2. arch参数似然值: {arch_ll_garch:.2f}")
print(f"  3. arch库似然值: {arch_result.loglikelihood:.2f}")
print(f"  4. 参数估计是否改变参数: {not (estimated_params.omega == default_params.omega and estimated_params.alpha == default_params.alpha)}")
print(f"  5. 似然值差异: garch_lib与arch库差异 {arch_ll_garch - arch_result.loglikelihood:.2f}") 