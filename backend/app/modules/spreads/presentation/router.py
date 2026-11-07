from fastapi import APIRouter, Depends

from app.modules.auth.presentation.dependencies import get_current_user
from app.modules.spreads.application.use_cases.get_spread import GetSpread
from app.modules.spreads.application.use_cases.list_spreads import ListSpreads
from app.modules.spreads.presentation.dependencies import get_get_spread, get_list_spreads
from app.modules.spreads.presentation.schemas import SpreadResponse

# Phải đăng nhập mới xem được danh sách kiểu trải bài
router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[SpreadResponse])
def list_spreads(use_case: ListSpreads = Depends(get_list_spreads)) -> list[SpreadResponse]:
    return [SpreadResponse.from_entity(s) for s in use_case.execute()]


@router.get("/{spread_id}", response_model=SpreadResponse)
def get_spread(spread_id: int, use_case: GetSpread = Depends(get_get_spread)) -> SpreadResponse:
    return SpreadResponse.from_entity(use_case.execute(spread_id))
