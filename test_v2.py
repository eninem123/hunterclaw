#!/usr/bin/env python3
"""
猎手系统v2.0功能测试脚本
"""

import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """测试模块导入"""
    print("=" * 55)
    print("测试模块导入...")
    print("=" * 55)
    
    try:
        import numpy as np
        print("✅ numpy 导入成功")
    except ImportError as e:
        print(f"❌ numpy 导入失败: {e}")
        return False
    
    try:
        import pandas as pd
        print("✅ pandas 导入成功")
    except ImportError as e:
        print(f"❌ pandas 导入失败: {e}")
        return False
    
    try:
        from data_analyzer import DataAnalyzer
        print("✅ data_analyzer 导入成功")
    except ImportError as e:
        print(f"❌ data_analyzer 导入失败: {e}")
        return False
    
    try:
        from hunter_closed_loop_v2 import HunterConfig, SimpleCache
        print("✅ hunter_closed_loop_v2 导入成功")
    except ImportError as e:
        print(f"❌ hunter_closed_loop_v2 导入失败: {e}")
        return False
    
    return True


def test_data_analyzer():
    """测试数据分析模块"""
    print("\n" + "=" * 55)
    print("测试数据分析模块...")
    print("=" * 55)
    
    try:
        from data_analyzer import DataAnalyzer
        import numpy as np
        
        analyzer = DataAnalyzer()
        
        # 测试MA计算
        prices = np.array([10.0, 11.0, 12.0, 13.0, 14.0])
        ma5 = analyzer.calculate_ma(prices, 5)
        if ma5 == 12.0:
            print("✅ MA计算正确")
        else:
            print(f"❌ MA计算错误: 期望12.0, 实际{ma5}")
            return False
        
        # 测试RSI计算
        prices = np.array([10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 
                          14.5, 14.0, 13.5, 13.0, 12.5, 12.0,
                          11.5, 11.0, 10.5])
        rsi = analyzer.calculate_rsi(prices)
        if rsi and 0 <= rsi <= 100:
            print(f"✅ RSI计算正确: {rsi:.2f}")
        else:
            print(f"❌ RSI计算错误: {rsi}")
            return False
        
        # 测试趋势识别（上升趋势：ma5 > ma10 > ma20 > ma60）
        trend = analyzer.identify_trend(14.5, 14.0, 13.5, 13.0)
        if trend.value == "上升":
            print("✅ 趋势识别正确")
        else:
            print(f"❌ 趋势识别错误: {trend.value}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 数据分析模块测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cache():
    """测试缓存功能"""
    print("\n" + "=" * 55)
    print("测试缓存功能...")
    print("=" * 55)
    
    try:
        from hunter_closed_loop_v2 import SimpleCache
        import time
        
        cache = SimpleCache(ttl=5)
        
        # 测试设置和获取
        cache.set("test_key", "test_value")
        value = cache.get("test_key")
        if value == "test_value":
            print("✅ 缓存设置和获取正确")
        else:
            print(f"❌ 缓存获取错误: 期望test_value, 实际{value}")
            return False
        
        # 测试过期
        time.sleep(6)
        value = cache.get("test_key")
        if value is None:
            print("✅ 缓存过期正确")
        else:
            print(f"❌ 缓存过期错误: 期望None, 实际{value}")
            return False
        
        # 测试清除
        cache.set("test_key2", "test_value2")
        cache.clear()
        value = cache.get("test_key2")
        if value is None:
            print("✅ 缓存清除正确")
        else:
            print(f"❌ 缓存清除错误: 期望None, 实际{value}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 缓存测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config():
    """测试配置"""
    print("\n" + "=" * 55)
    print("测试配置...")
    print("=" * 55)
    
    try:
        from hunter_closed_loop_v2 import HunterConfig
        
        # 测试默认配置
        config = HunterConfig()
        if config.timeout == 8 and config.max_retries == 3:
            print("✅ 默认配置正确")
        else:
            print(f"❌ 默认配置错误: timeout={config.timeout}, max_retries={config.max_retries}")
            return False
        
        # 测试自定义配置
        config = HunterConfig(timeout=10, max_retries=5)
        if config.timeout == 10 and config.max_retries == 5:
            print("✅ 自定义配置正确")
        else:
            print(f"❌ 自定义配置错误: timeout={config.timeout}, max_retries={config.max_retries}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_file_structure():
    """测试文件结构"""
    print("\n" + "=" * 55)
    print("测试文件结构...")
    print("=" * 55)
    
    base_path = Path("/root/.openclaw/workspace/猎手模拟交易")
    
    required_files = [
        "hunter_closed_loop_v2.py",
        "src/data_analyzer.py",
        "mcp-data-server/src/api_server_v2.py",
        "docs/开发者指南.md",
        "docs/优化总结_v2.md"
    ]
    
    all_exist = True
    for file in required_files:
        file_path = base_path / file
        if file_path.exists():
            print(f"✅ {file} 存在")
        else:
            print(f"❌ {file} 不存在")
            all_exist = False
    
    return all_exist


def main():
    """运行所有测试"""
    print("\n")
    print("🧪 猎手系统v2.0功能测试")
    print("=" * 55)
    
    results = {
        "模块导入": test_imports(),
        "数据分析模块": test_data_analyzer(),
        "缓存功能": test_cache(),
        "配置": test_config(),
        "文件结构": test_file_structure()
    }
    
    print("\n" + "=" * 55)
    print("测试结果汇总")
    print("=" * 55)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    print("\n" + "=" * 55)
    print(f"总计: {passed}/{total} 测试通过")
    print("=" * 55)
    
    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
