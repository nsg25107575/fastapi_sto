from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database.engine import get_session
from models.review import ReviewModel
from validations.review import ReviewCreateSchema, ReviewResponseSchema

router = APIRouter(
    prefix="/reviews",
    tags=["Reviews"],
)


@router.post(
    "/",
    response_model=ReviewResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_review(
        payload: ReviewCreateSchema,
        session: Session = Depends(get_session),
):
    review = ReviewModel.create_review(
        session=session,
        order_id=payload.order_id,
        rating=payload.rating,
        comment=payload.comment,
    )

    session.commit()

    return review
