from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from budget_optimizer import BudgetOptimizer, Channel

app = FastAPI(title="广告预算智能分配系统")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChannelInput(BaseModel):
    name: str = Field(..., description="渠道名称")
    conversion_rate: float = Field(..., gt=0, le=1, description="历史转化率 (0-1之间)")
    click_cost: float = Field(..., gt=0, description="点击成本 (元/点击)")
    max_budget: float = Field(..., gt=0, description="最大预算上限 (元)")
    min_budget: float = Field(default=0, ge=0, description="最小预算 (元)")


class AllocationRequest(BaseModel):
    channels: List[ChannelInput] = Field(..., description="广告渠道列表")
    total_budget: float = Field(..., gt=0, description="总预算金额 (元)")


@app.get("/")
def read_root():
    return {"message": "广告预算智能分配系统 API 服务运行中"}


@app.post("/api/allocate")
def allocate_budget(request: AllocationRequest):
    optimizer = BudgetOptimizer()

    channels = []
    for ch in request.channels:
        if ch.min_budget > ch.max_budget:
            raise HTTPException(
                status_code=400,
                detail=f"渠道 '{ch.name}' 的最小预算({ch.min_budget})不能大于最大预算({ch.max_budget})"
            )
        channels.append(Channel(
            name=ch.name,
            conversion_rate=ch.conversion_rate,
            click_cost=ch.click_cost,
            max_budget=ch.max_budget,
            min_budget=ch.min_budget
        ))

    result = optimizer.optimize(channels, request.total_budget)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
