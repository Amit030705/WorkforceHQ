from datetime import UTC, date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.leave_request import LeaveRequest
from app.schemas.leave_request import LeaveCreate, LeaveReview
from app.services.errors import Conflict, InvalidOperation, RecordNotFound


def leave_query():
    return select(LeaveRequest).options(
        joinedload(LeaveRequest.employee),
        joinedload(LeaveRequest.reviewer),
    )


def submit_leave(db: Session, employee_id: int, payload: LeaveCreate) -> LeaveRequest:
    if payload.start_date < date.today():
        raise InvalidOperation("Leave cannot start in the past.")
    if payload.end_date < payload.start_date:
        raise InvalidOperation("end_date must be on or after start_date.")

    db.execute(select(func.pg_advisory_xact_lock(employee_id)))
    overlap = db.scalar(
        select(LeaveRequest.id).where(
            LeaveRequest.employee_id == employee_id,
            LeaveRequest.status.in_(("pending", "approved")),
            LeaveRequest.start_date <= payload.end_date,
            LeaveRequest.end_date >= payload.start_date,
        )
    )
    if overlap is not None:
        db.rollback()
        raise Conflict("The dates overlap an existing pending or approved request.")
    item = LeaveRequest(employee_id=employee_id, **payload.model_dump())
    db.add(item)
    db.commit()
    return db.scalar(leave_query().where(LeaveRequest.id == item.id))


def review_leave(
    db: Session,
    request_id: int,
    payload: LeaveReview,
    reviewer_id: int,
) -> LeaveRequest:
    item = db.scalar(
        leave_query()
        .where(LeaveRequest.id == request_id)
        .with_for_update(of=LeaveRequest)
    )
    if item is None:
        raise RecordNotFound("Leave request not found.")
    if item.status != "pending":
        raise Conflict("Only pending requests can be reviewed.")
    if payload.status == "approved":
        db.execute(select(func.pg_advisory_xact_lock(item.employee_id)))
        overlapping = db.scalar(
            select(LeaveRequest.id).where(
                LeaveRequest.employee_id == item.employee_id,
                LeaveRequest.id != item.id,
                LeaveRequest.status == "approved",
                LeaveRequest.start_date <= item.end_date,
                LeaveRequest.end_date >= item.start_date,
            )
        )
        if overlapping is not None:
            raise Conflict("Another approved leave request overlaps these dates.")
    item.status = payload.status
    item.reviewer_id = reviewer_id
    item.reviewed_at = datetime.now(UTC)
    item.reviewer_comment = payload.reviewer_comment
    db.commit()
    return db.scalar(leave_query().where(LeaveRequest.id == request_id))

