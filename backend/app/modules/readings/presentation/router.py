from fastapi import APIRouter, Depends, Query, Response

from app.modules.auth.domain.user import Role, User
from app.modules.auth.presentation.dependencies import get_current_user
from app.modules.quota.application.use_cases.get_quota import GetQuota
from app.modules.readings.application.use_cases.delete_reading import DeleteReading
from app.modules.readings.application.use_cases.draw_reading import DrawReading
from app.modules.readings.application.use_cases.get_reading import GetReading
from app.modules.readings.application.use_cases.interpret_reading import InterpretReading
from app.modules.readings.application.use_cases.list_readings import ListReadings
from app.modules.readings.presentation.dependencies import (
    get_delete_reading,
    get_draw_reading,
    get_get_quota,
    get_get_reading,
    get_interpret_reading,
    get_list_readings,
)
from app.modules.readings.presentation.schemas import DrawReadingRequest, QuotaResponse, ReadingResponse

router = APIRouter()      # gắn vào /readings
me_router = APIRouter()   # gắn vào /me  (GET /me/quota)


def _is_admin(user: User) -> bool:
    return user.role is Role.ADMIN


@router.post("", response_model=ReadingResponse, status_code=201)
def draw_reading(
    body: DrawReadingRequest,
    user: User = Depends(get_current_user),
    use_case: DrawReading = Depends(get_draw_reading),
) -> ReadingResponse:
    """Bốc bài. AI lỗi vẫn trả 201: bài đã lưu, `ai_status` = "failed", dùng /interpret để giải lại."""
    details = use_case.execute(user.id, body.spread_id, body.question, unlimited=_is_admin(user))
    return ReadingResponse.from_details(details)


@router.post("/{reading_id}/interpret", response_model=ReadingResponse)
def interpret_reading(
    reading_id: int,
    user: User = Depends(get_current_user),
    use_case: InterpretReading = Depends(get_interpret_reading),
) -> ReadingResponse:
    """Giải lại khi lần trước AI lỗi. Không bốc lại bài, không tính thêm lượt."""
    return ReadingResponse.from_details(use_case.execute(reading_id, user.id))


@router.get("", response_model=list[ReadingResponse])
def list_readings(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    use_case: ListReadings = Depends(get_list_readings),
) -> list[ReadingResponse]:
    return [ReadingResponse.from_details(d) for d in use_case.execute(user.id, limit, offset)]


@router.get("/{reading_id}", response_model=ReadingResponse)
def get_reading(
    reading_id: int,
    user: User = Depends(get_current_user),
    use_case: GetReading = Depends(get_get_reading),
) -> ReadingResponse:
    return ReadingResponse.from_details(use_case.execute(reading_id, user.id))


@router.delete("/{reading_id}", status_code=204)
def delete_reading(
    reading_id: int,
    user: User = Depends(get_current_user),
    use_case: DeleteReading = Depends(get_delete_reading),
) -> Response:
    use_case.execute(reading_id, user.id)
    return Response(status_code=204)


@me_router.get("/quota", response_model=QuotaResponse)
def my_quota(
    user: User = Depends(get_current_user),
    use_case: GetQuota = Depends(get_get_quota),
) -> QuotaResponse:
    return QuotaResponse.from_status(use_case.execute(user.id, unlimited=_is_admin(user)))
