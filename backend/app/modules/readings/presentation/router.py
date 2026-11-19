from fastapi import APIRouter, Depends, Query, Response

from app.modules.auth.domain.user import Role, User
from app.modules.auth.presentation.dependencies import get_current_user, require_admin
from app.modules.quota.application.use_cases.get_quota import GetQuota
from app.modules.readings.application.use_cases.delete_reading import DeleteReading
from app.modules.readings.application.use_cases.draw_reading import DrawReading
from app.modules.readings.application.use_cases.get_accuracy_stats import GetAccuracyStats
from app.modules.readings.application.use_cases.get_reading import GetReading
from app.modules.readings.application.use_cases.interpret_reading import InterpretReading
from app.modules.readings.application.use_cases.list_readings import ListReadings
from app.modules.readings.application.use_cases.rate_reading import RateReading
from app.modules.readings.presentation.dependencies import (
    get_accuracy_stats,
    get_delete_reading,
    get_draw_reading,
    get_get_quota,
    get_get_reading,
    get_interpret_reading,
    get_list_readings,
    get_rate_reading,
)
from app.modules.readings.presentation.schemas import (
    AccuracyStatsResponse,
    DrawReadingRequest,
    QuotaResponse,
    RateReadingRequest,
    ReadingResponse,
)

router = APIRouter()      # gắn vào /readings
me_router = APIRouter()   # gắn vào /me  (GET /me/quota)
stats_router = APIRouter(dependencies=[Depends(require_admin)])  # gắn vào /admin/stats, chỉ admin


def _is_admin(user: User) -> bool:
    return user.role is Role.ADMIN


@router.post("", response_model=ReadingResponse, status_code=201)
def draw_reading(
    body: DrawReadingRequest,
    interpret: bool = Query(True, description="false: trả lá ngay (ai_status pending), gọi /interpret sau"),
    user: User = Depends(get_current_user),
    use_case: DrawReading = Depends(get_draw_reading),
) -> ReadingResponse:
    """Bốc bài. AI lỗi vẫn trả 201: bài đã lưu, `ai_status` = "failed", dùng /interpret để giải lại."""
    details = use_case.execute(user.id, body.spread_id, body.question, unlimited=_is_admin(user), interpret=interpret)
    return ReadingResponse.from_details(details)


@router.post("/{reading_id}/interpret", response_model=ReadingResponse)
def interpret_reading(
    reading_id: int,
    user: User = Depends(get_current_user),
    use_case: InterpretReading = Depends(get_interpret_reading),
) -> ReadingResponse:
    """Diễn giải một reading: lần đầu (sau khi bốc với interpret=false) hoặc giải lại khi AI lỗi.
    Không bốc lại bài, không tính thêm lượt."""
    return ReadingResponse.from_details(use_case.execute(reading_id, user.id))


@router.put("/{reading_id}/rating", response_model=ReadingResponse)
def rate_reading(
    reading_id: int,
    body: RateReadingRequest,
    user: User = Depends(get_current_user),
    use_case: RateReading = Depends(get_rate_reading),
) -> ReadingResponse:
    """Người dùng chấm lời giải đúng bao nhiêu % (0-100). Chấm lại thì ghi đè."""
    return ReadingResponse.from_details(use_case.execute(reading_id, user.id, body.accuracy))


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


@stats_router.get("/accuracy", response_model=AccuracyStatsResponse)
def accuracy_stats(
    days: int = Query(30, ge=7, le=180),
    use_case: GetAccuracyStats = Depends(get_accuracy_stats),
) -> AccuracyStatsResponse:
    """Độ đúng người dùng tự chấm cho lời giải, gom theo kiểu trải, chủ đề, đối tượng và theo ngày."""
    return AccuracyStatsResponse.from_stats(use_case.execute(days))
