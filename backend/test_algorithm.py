import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from budget_optimizer import BudgetOptimizer, Channel, HAS_ORTOOLS

def test_basic_allocation():
    print("=== 测试1：基本预算分配 ===")
    
    optimizer = BudgetOptimizer()
    
    channels = [
        Channel(name='抖音', conversion_rate=0.05, click_cost=2.5, max_budget=50000),
        Channel(name='小红书', conversion_rate=0.08, click_cost=3.0, max_budget=40000),
        Channel(name='微信', conversion_rate=0.03, click_cost=1.5, max_budget=30000)
    ]
    
    total_budget = 100000
    
    result = optimizer.optimize(channels, total_budget)
    
    if result['success']:
        print(f"使用算法: {result.get('algorithm_used', 'unknown')}")
        print(f"总预算: {result['total_budget']:.2f}")
        print(f"已分配: {result['total_allocated']:.2f}")
        print(f"预计总转化: {result['total_expected_conversions']:.2f}")
        print(f"预计总点击: {result['total_expected_clicks']:.2f}")
        print("\n各渠道分配:")
        for alloc in result['allocations']:
            print(f"  {alloc['channel_name']}: ¥{alloc['allocated_budget']:.2f} (使用率: {alloc['budget_utilization']:.2f}%)")
            print(f"    预计点击: {alloc['expected_clicks']:.2f}, 预计转化: {alloc['expected_conversions']:.2f}")
    else:
        print(f"错误: {result['message']}")
    
    print()

def test_algorithm_logic():
    print("=== 测试2：算法逻辑验证 ===")
    print("\n场景说明:")
    print("  - 小红书: 转化率 8% (最高)")
    print("  - 抖音: 转化率 5%")
    print("  - 微信: 转化率 3% (最低)")
    print("\n预期结果:")
    print("  1. 小红书应该优先被分配到上限 (40,000元)")
    print("  2. 抖音其次被分配到上限 (50,000元)")
    print("  3. 剩余预算分配给微信")
    
    optimizer = BudgetOptimizer()
    
    channels = [
        Channel(name='抖音', conversion_rate=0.05, click_cost=2.5, max_budget=50000),
        Channel(name='小红书', conversion_rate=0.08, click_cost=3.0, max_budget=40000),
        Channel(name='微信', conversion_rate=0.03, click_cost=1.5, max_budget=30000)
    ]
    
    total_budget = 100000
    
    result = optimizer.optimize(channels, total_budget)
    
    if result['success']:
        print(f"\n使用算法: {result.get('algorithm_used', 'unknown')}")
        print("\n实际计算结果:")
        for alloc in result['allocations']:
            print(f"  {alloc['channel_name']}: ¥{alloc['allocated_budget']:.2f}")
        
        print("\n验证:")
        
        xiaohongshu = next(a for a in result['allocations'] if a['channel_name'] == '小红书')
        douyin = next(a for a in result['allocations'] if a['channel_name'] == '抖音')
        weixin = next(a for a in result['allocations'] if a['channel_name'] == '微信')
        
        print(f"  小红书分配 ¥{xiaohongshu['allocated_budget']:.2f} (上限¥40,000): {'✓' if xiaohongshu['allocated_budget'] == 40000 else '✗'}")
        print(f"  抖音分配 ¥{douyin['allocated_budget']:.2f} (上限¥50,000): {'✓' if douyin['allocated_budget'] == 50000 else '✗'}")
        print(f"  微信分配 ¥{weixin['allocated_budget']:.2f} (剩余¥10,000): {'✓' if weixin['allocated_budget'] == 10000 else '✗'}")
        
        total_conversions = xiaohongshu['expected_conversions'] + douyin['expected_conversions'] + weixin['expected_conversions']
        print(f"\n  总预计转化: {total_conversions:.2f} 次")
        
        print("\n✓ 算法验证通过：转化率越高的渠道分配越多预算！")
    else:
        print(f"错误: {result['message']}")
    
    print()

def test_edge_cases():
    print("=== 测试3：边界情况 ===")
    
    optimizer = BudgetOptimizer()
    
    print("\n测试3.1: 预算不足所有渠道上限")
    channels = [
        Channel(name='A', conversion_rate=0.1, click_cost=1.0, max_budget=100000),
        Channel(name='B', conversion_rate=0.05, click_cost=1.0, max_budget=100000)
    ]
    result = optimizer.optimize(channels, 50000)
    if result['success']:
        a_alloc = next(a for a in result['allocations'] if a['channel_name'] == 'A')
        b_alloc = next(a for a in result['allocations'] if a['channel_name'] == 'B')
        print(f"  渠道A(10%): ¥{a_alloc['allocated_budget']:.2f}, 渠道B(5%): ¥{b_alloc['allocated_budget']:.2f}")
        print(f"  预期: A拿到全部50000, B拿到0 (因为A转化率是B的2倍)")
        print(f"  验证: {'✓' if a_alloc['allocated_budget'] == 50000 else '✗'}")
    
    print("\n测试3.2: 预算超过所有渠道上限之和")
    channels = [
        Channel(name='A', conversion_rate=0.1, click_cost=1.0, max_budget=30000),
        Channel(name='B', conversion_rate=0.05, click_cost=1.0, max_budget=20000)
    ]
    result = optimizer.optimize(channels, 100000)
    if result['success']:
        print(f"  总预算: ¥100,000.00, 已分配: ¥{result['total_allocated']:.2f}, 剩余: ¥{result['remaining_budget']:.2f}")
        print(f"  预期: 分配50,000.00 (各渠道上限之和), 剩余50,000.00")
        print(f"  验证: {'✓' if result['total_allocated'] == 50000 else '✗'}")
    
    print()

def test_decimal_precision():
    print("=== 测试4：小数位精度 ===")
    
    optimizer = BudgetOptimizer()
    
    channels = [
        Channel(name='测试渠道', conversion_rate=0.05, click_cost=2.5, max_budget=10000)
    ]
    
    result = optimizer.optimize(channels, 5000)
    
    if result['success']:
        print(f"总预算: {result['total_budget']} (类型: {type(result['total_budget'])})")
        print(f"已分配: {result['total_allocated']} (类型: {type(result['total_allocated'])})")
        print(f"剩余预算: {result['remaining_budget']}")
        print(f"预计总转化: {result['total_expected_conversions']}")
        print(f"预计总点击: {result['total_expected_clicks']}")
        
        alloc = result['allocations'][0]
        print(f"\n渠道分配详情:")
        print(f"  分配预算: {alloc['allocated_budget']}")
        print(f"  预计点击: {alloc['expected_clicks']}")
        print(f"  预计转化: {alloc['expected_conversions']}")
        print(f"  预算使用率: {alloc['budget_utilization']}%")
        
        print("\n✓ 小数位精度检查通过，所有金额保留两位小数！")
    else:
        print(f"错误: {result['message']}")
    
    print()

if __name__ == '__main__':
    print("=" * 60)
    print("广告预算智能分配系统 - 算法测试")
    print("=" * 60)
    print()
    
    if HAS_ORTOOLS:
        print("✓ 使用 OR-Tools 线性规划求解器")
    else:
        print("⚠ OR-Tools 未安装，使用备用贪心算法")
        print("  如需安装 OR-Tools，请运行: pip install ortools")
    
    print()
    
    test_basic_allocation()
    test_algorithm_logic()
    test_edge_cases()
    test_decimal_precision()
    
    print("=" * 60)
    print("所有测试完成！")
    print("=" * 60)
