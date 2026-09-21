from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from ..auth.dependencies import get_current_user
from ..connection import get_session
from ..models import (
    BookOwnership,
    ExchangeRequest,
    ExchangeRequestDefault,
    ExchangeStatus,
    User,
)


router = APIRouter(prefix="/exchanges", tags=["exchanges"])


class ExchangeRead(ExchangeRequestDefault):
    id: int
    requester_id: int
    owner_id: int
    status: ExchangeStatus
    created_at: datetime
    updated_at: datetime


class ExchangeDetailed(ExchangeRead):
    offered: Optional[BookOwnership] = None
    requested: Optional[BookOwnership] = None


class ExchangeCreate(ExchangeRequestDefault):
    pass


@router.post(
    "/",
    response_model=ExchangeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Отправить запрос на обмен",
)
def create_exchange(
    payload: ExchangeCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ExchangeRequest:
    offered = session.get(BookOwnership, payload.offered_ownership_id)
    requested = session.get(BookOwnership, payload.requested_ownership_id)
    if offered is None or requested is None:
        raise HTTPException(status_code=404, detail="Ownership record not found")
    if offered.owner_id != current_user.id:
        raise HTTPException(
            status_code=400, detail="Offered book does not belong to you"
        )
    if requested.owner_id == current_user.id:
        raise HTTPException(
            status_code=400, detail="Requested book belongs to you already"
        )
    if not offered.is_available or not requested.is_available:
        raise HTTPException(
            status_code=400, detail="One of the books is not available for exchange"
        )
    exchange = ExchangeRequest(
        offered_ownership_id=payload.offered_ownership_id,
        requested_ownership_id=payload.requested_ownership_id,
        message=payload.message,
        requester_id=current_user.id,
        owner_id=requested.owner_id,
    )
    session.add(exchange)
    session.commit()
    session.refresh(exchange)
    return exchange


@router.get("/incoming", response_model=List[ExchangeDetailed])
def list_incoming(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    status_filter: Optional[ExchangeStatus] = None,
) -> List[ExchangeDetailed]:
    query = select(ExchangeRequest).where(ExchangeRequest.owner_id == current_user.id)
    if status_filter is not None:
        query = query.where(ExchangeRequest.status == status_filter)
    return [_hydrate(session, ex) for ex in session.exec(query).all()]


@router.get("/outgoing", response_model=List[ExchangeDetailed])
def list_outgoing(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    status_filter: Optional[ExchangeStatus] = None,
) -> List[ExchangeDetailed]:
    query = select(ExchangeRequest).where(
        ExchangeRequest.requester_id == current_user.id
    )
    if status_filter is not None:
        query = query.where(ExchangeRequest.status == status_filter)
    return [_hydrate(session, ex) for ex in session.exec(query).all()]


@router.get("/{exchange_id}", response_model=ExchangeDetailed)
def get_exchange(
    exchange_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ExchangeDetailed:
    ex = session.get(ExchangeRequest, exchange_id)
    if ex is None:
        raise HTTPException(status_code=404, detail="Exchange not found")
    if current_user.id not in (ex.requester_id, ex.owner_id):
        raise HTTPException(status_code=403, detail="Not a participant")
    return _hydrate(session, ex)


@router.post("/{exchange_id}/accept", response_model=ExchangeRead)
def accept_exchange(
    exchange_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ExchangeRequest:
    ex = _get_owned(session, exchange_id, current_user, participant="owner")
    if ex.status != ExchangeStatus.pending:
        raise HTTPException(status_code=400, detail="Exchange is not pending")
    ex.status = ExchangeStatus.accepted
    ex.updated_at = datetime.utcnow()
    # Помечаем оба экземпляра как временно недоступные.
    for oid in (ex.offered_ownership_id, ex.requested_ownership_id):
        ownership = session.get(BookOwnership, oid)
        if ownership is not None:
            ownership.is_available = False
            session.add(ownership)
    session.add(ex)
    session.commit()
    session.refresh(ex)
    return ex


@router.post("/{exchange_id}/decline", response_model=ExchangeRead)
def decline_exchange(
    exchange_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ExchangeRequest:
    ex = _get_owned(session, exchange_id, current_user, participant="owner")
    if ex.status != ExchangeStatus.pending:
        raise HTTPException(status_code=400, detail="Exchange is not pending")
    ex.status = ExchangeStatus.declined
    ex.updated_at = datetime.utcnow()
    session.add(ex)
    session.commit()
    session.refresh(ex)
    return ex


@router.post("/{exchange_id}/cancel", response_model=ExchangeRead)
def cancel_exchange(
    exchange_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ExchangeRequest:
    ex = _get_owned(session, exchange_id, current_user, participant="requester")
    if ex.status not in (ExchangeStatus.pending, ExchangeStatus.accepted):
        raise HTTPException(status_code=400, detail="Cannot cancel finalized exchange")
    ex.status = ExchangeStatus.cancelled
    ex.updated_at = datetime.utcnow()
    session.add(ex)
    session.commit()
    session.refresh(ex)
    return ex


@router.post("/{exchange_id}/complete", response_model=ExchangeRead)
def complete_exchange(
    exchange_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ExchangeRequest:
    ex = session.get(ExchangeRequest, exchange_id)
    if ex is None:
        raise HTTPException(status_code=404, detail="Exchange not found")
    if current_user.id not in (ex.requester_id, ex.owner_id):
        raise HTTPException(status_code=403, detail="Not a participant")
    if ex.status != ExchangeStatus.accepted:
        raise HTTPException(status_code=400, detail="Exchange is not accepted yet")
    ex.status = ExchangeStatus.completed
    ex.updated_at = datetime.utcnow()
    session.add(ex)
    session.commit()
    session.refresh(ex)
    return ex


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _get_owned(
    session: Session,
    exchange_id: int,
    user: User,
    participant: str,
) -> ExchangeRequest:
    ex = session.get(ExchangeRequest, exchange_id)
    if ex is None:
        raise HTTPException(status_code=404, detail="Exchange not found")
    expected_id = ex.owner_id if participant == "owner" else ex.requester_id
    if expected_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed for this participant")
    return ex


def _hydrate(session: Session, ex: ExchangeRequest) -> ExchangeDetailed:
    return ExchangeDetailed(
        **ex.model_dump(),
        offered=session.get(BookOwnership, ex.offered_ownership_id),
        requested=session.get(BookOwnership, ex.requested_ownership_id),
    )
