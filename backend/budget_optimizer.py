from typing import List, Dict, Optional
from dataclasses import dataclass

try:
    from ortools.linear_solver import pywraplp
    HAS_ORTOOLS = True
except ImportError:
    HAS_ORTOOLS = False
    print("警告: OR-Tools 未安装，将使用备用的贪心算法")


@dataclass
class Channel:
    name: str
    conversion_rate: float
    click_cost: float
    max_budget: float
    min_budget: float = 0.0


@dataclass
class AllocationResult:
    channel_name: str
    allocated_budget: float
    expected_clicks: float
    expected_conversions: float
    budget_utilization: float


class BudgetOptimizer:
    def __init__(self):
        pass

    def _calculate_efficiency(self, channel: Channel) -> float:
        if channel.click_cost > 0:
            return channel.conversion_rate / channel.click_cost
        return channel.conversion_rate

    def _optimize_greedy(self, channels: List[Channel], total_budget: float) -> Dict:
        total_min_budget = sum(ch.min_budget for ch in channels)
        total_max_budget = sum(ch.max_budget for ch in channels)

        if total_budget < total_min_budget:
            return {
                "success": False,
                "message": f"总预算({total_budget:.2f})不能小于所有渠道最小预算之和({total_min_budget:.2f})"
            }

        allocations = {ch.name: ch.min_budget for ch in channels}
        remaining_budget = total_budget - total_min_budget

        channels_by_efficiency = sorted(
            channels,
            key=self._calculate_efficiency,
            reverse=True
        )

        for channel in channels_by_efficiency:
            if remaining_budget <= 0:
                break

            additional_budget_needed = channel.max_budget - allocations[channel.name]
            if additional_budget_needed <= 0:
                continue

            if remaining_budget >= additional_budget_needed:
                allocations[channel.name] = channel.max_budget
                remaining_budget -= additional_budget_needed
            else:
                allocations[channel.name] += remaining_budget
                remaining_budget = 0

        results = []
        total_allocated = 0.0
        total_expected_conversions = 0.0
        total_expected_clicks = 0.0

        for channel in channels:
            allocated = round(allocations[channel.name], 2)
            total_allocated += allocated

            if channel.click_cost > 0:
                expected_clicks = allocated / channel.click_cost
            else:
                expected_clicks = 0

            expected_conversions = expected_clicks * channel.conversion_rate
            total_expected_conversions += expected_conversions
            total_expected_clicks += expected_clicks

            if channel.max_budget > 0:
                utilization = (allocated / channel.max_budget) * 100
            else:
                utilization = 0

            results.append(AllocationResult(
                channel_name=channel.name,
                allocated_budget=round(allocated, 2),
                expected_clicks=round(expected_clicks, 2),
                expected_conversions=round(expected_conversions, 2),
                budget_utilization=round(utilization, 2)
            ))

        remaining_budget = total_budget - total_allocated

        return {
            "success": True,
            "algorithm_used": "greedy",
            "total_budget": round(total_budget, 2),
            "total_allocated": round(total_allocated, 2),
            "remaining_budget": round(remaining_budget, 2),
            "total_expected_clicks": round(total_expected_clicks, 2),
            "total_expected_conversions": round(total_expected_conversions, 2),
            "allocations": [
                {
                    "channel_name": r.channel_name,
                    "allocated_budget": round(r.allocated_budget, 2),
                    "expected_clicks": round(r.expected_clicks, 2),
                    "expected_conversions": round(r.expected_conversions, 2),
                    "budget_utilization": round(r.budget_utilization, 2)
                }
                for r in results
            ]
        }

    def _optimize_ortools(self, channels: List[Channel], total_budget: float) -> Dict:
        if not channels:
            return {"success": False, "message": "请至少添加一个广告渠道"}

        if total_budget <= 0:
            return {"success": False, "message": "总预算必须大于0"}

        total_max_budget = sum(ch.max_budget for ch in channels)
        total_min_budget = sum(ch.min_budget for ch in channels)

        if total_budget < total_min_budget:
            return {
                "success": False,
                "message": f"总预算({total_budget:.2f})不能小于所有渠道最小预算之和({total_min_budget:.2f})"
            }

        solver = pywraplp.Solver.CreateSolver('SCIP')
        if not solver:
            return {"success": False, "message": "求解器初始化失败"}

        budget_vars = {}
        for channel in channels:
            var_name = f"budget_{channel.name}"
            budget_vars[channel.name] = solver.NumVar(
                channel.min_budget,
                channel.max_budget,
                var_name
            )

        total_allocation = solver.Sum(
            budget_vars[ch.name] for ch in channels
        )
        solver.Add(total_allocation <= total_budget)
        solver.Add(total_allocation >= total_min_budget)

        objective_terms = []
        for channel in channels:
            if channel.click_cost > 0 and channel.conversion_rate > 0:
                coefficient = channel.conversion_rate / channel.click_cost
                objective_terms.append(coefficient * budget_vars[channel.name])
            elif channel.conversion_rate > 0:
                objective_terms.append(channel.conversion_rate * budget_vars[channel.name])

        if not objective_terms:
            return {"success": False, "message": "所有渠道的转化率和点击成本配置无效"}

        solver.Maximize(solver.Sum(objective_terms))

        status = solver.Solve()

        if status not in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
            return {"success": False, "message": "无法找到最优解，请检查输入参数"}

        results = []
        total_allocated = 0.0
        total_expected_conversions = 0.0
        total_expected_clicks = 0.0

        for channel in channels:
            allocated = budget_vars[channel.name].solution_value()
            total_allocated += allocated

            if channel.click_cost > 0:
                expected_clicks = allocated / channel.click_cost
            else:
                expected_clicks = 0

            expected_conversions = expected_clicks * channel.conversion_rate
            total_expected_conversions += expected_conversions
            total_expected_clicks += expected_clicks

            if channel.max_budget > 0:
                utilization = (allocated / channel.max_budget) * 100
            else:
                utilization = 0

            results.append(AllocationResult(
                channel_name=channel.name,
                allocated_budget=round(allocated, 2),
                expected_clicks=round(expected_clicks, 2),
                expected_conversions=round(expected_conversions, 2),
                budget_utilization=round(utilization, 2)
            ))

        remaining_budget = total_budget - total_allocated

        return {
            "success": True,
            "algorithm_used": "linear_programming",
            "total_budget": round(total_budget, 2),
            "total_allocated": round(total_allocated, 2),
            "remaining_budget": round(remaining_budget, 2),
            "total_expected_clicks": round(total_expected_clicks, 2),
            "total_expected_conversions": round(total_expected_conversions, 2),
            "allocations": [
                {
                    "channel_name": r.channel_name,
                    "allocated_budget": round(r.allocated_budget, 2),
                    "expected_clicks": round(r.expected_clicks, 2),
                    "expected_conversions": round(r.expected_conversions, 2),
                    "budget_utilization": round(r.budget_utilization, 2)
                }
                for r in results
            ]
        }

    def optimize(self, channels: List[Channel], total_budget: float) -> Dict:
        if HAS_ORTOOLS:
            return self._optimize_ortools(channels, total_budget)
        else:
            return self._optimize_greedy(channels, total_budget)
