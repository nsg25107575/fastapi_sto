from datetime import datetime
from typing import Self

from sqlalchemy import DateTime, ForeignKey, Integer, Text, text, Float, select, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session

from database.engine import Base
from exceptions import order_not_found_exception
from exceptions.exceptions import rating_value_out_of_range_exception, review_already_exists_exception, \
    review_not_found_exception
from models import OrderModel


class ReviewModel(Base):
    """
    Review model representing a review for an order at a station by a customer.
    """
    __tablename__ = "reviews"

    order_id: Mapped[int] = mapped_column(
        Integer(),
        ForeignKey("orders.id"),
        nullable=False,
    )

    station_id: Mapped[int] = mapped_column(
        Integer(),
        ForeignKey("stations.id"),
        nullable=False,
    )

    customer_id: Mapped[int] = mapped_column(
        Integer(),
        ForeignKey("customers.id"),
        nullable=False,
    )

    rating: Mapped[float] = mapped_column(
        Float(),
        nullable=False,
    )

    comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    order = relationship("OrderModel")
    station = relationship("StationModel")
    customer = relationship("CustomerModel")

    __table_args__ = (
        PrimaryKeyConstraint(
            "order_id", "station_id", "customer_id",
            name="uq_order_station_customer_review"
        ),
    )

    @classmethod
    def get_review(cls,
                   session: Session,
                   order_id: int,
                   station_id: int,
                   customer_id: int
                   ) -> Self | None:
        """
        Get a review by order_id, station_id, and customer_id.
        :param session: SQLAlchemy session
        :param order_id: Order ID
        :param station_id: Station ID
        :param customer_id: Customer ID
        :return: ReviewModel instance or None if not found
        """
        return session.scalar(
            select(cls).where(
                cls.order_id == order_id,
                cls.station_id == station_id,
                cls.customer_id == customer_id
            )
        )

    @classmethod
    def create_review(cls,
                      session: Session,
                      order_id: int,
                      station_id: int,
                      customer_id: int,
                      rating: float,
                      comment: str | None = None,
                      ) -> Self:
        """
        Add a new review for the given order_id, station_id, and customer_id.
        :param session: SQLAlchemy session
        :param order_id: Order ID
        :param station_id: Station ID
        :param customer_id: Customer ID
        :param rating: Rating value
        :param comment: Comment (optional)
        :return: ReviewModel instance
        """
        if not cls._check_order_exists(session, order_id, station_id, customer_id):
            raise order_not_found_exception()

        # Check rating value is within the valid range
        if not cls._check_rating_value(rating):
            raise rating_value_out_of_range_exception()

        # Check if a review already exists for the given order, station, and customer combination
        if cls._check_review_exists(session, order_id, station_id, customer_id):
            raise review_already_exists_exception()

        review = cls(
            order_id=order_id,
            station_id=station_id,
            customer_id=customer_id,
            rating=rating,
            comment=comment,
        )

        # Add the review to the session and flush to generate the primary key
        session.add(review)
        # Commit the session to persist the changes to the database
        session.commit()
        # Flush the session to ensure the review is written to the database
        session.flush()

        return review

    @classmethod
    def update_review(cls,
                      session: Session,
                      order_id: int,
                      station_id: int,
                      customer_id: int,
                      rating: float,
                      comment: str | None = None,
                      ) -> Self:
        """
        Update an existing review for the given order_id, station_id, and customer_id.
        :param session: SQLAlchemy session
        :param order_id: Order ID
        :param station_id: Station ID
        :param customer_id: Customer ID
        :param rating: New rating value
        :param comment: New comment (optional)
        :return: Updated ReviewModel instance
        """
        # check if a review exists for the given order, station, and customer combination
        review = cls.get_review(session, order_id, station_id, customer_id)
        if not review:
            raise review_not_found_exception()

        # Check rating value is within the valid range
        if not cls._check_rating_value(rating):
            raise rating_value_out_of_range_exception()

        # Update the review's rating and comment
        review.rating = rating
        review.comment = comment  # (optional) Update the comment if provided

        # Commit the session to persist the changes to the database
        session.commit()
        # Flush the session to ensure the review is written to the database
        session.flush()

        return review

    @classmethod
    def _check_review_exists(cls,
                             session: Session,
                             order_id: int,
                             station_id: int,
                             customer_id: int) -> bool:
        """
        Check if a review exists for the given order_id, station_id, and customer_id.
        :param session: SQLAlchemy session
        :param order_id: Order ID
        :param station_id: Station ID
        :param customer_id: Customer ID
        :return: True if the review exists, False otherwise
        """
        review = session.scalar(
            select(cls).where(
                cls.order_id == order_id,
                cls.station_id == station_id,
                cls.customer_id == customer_id
            )
        )
        return review is not None

    @classmethod
    def delete_review(cls,
                      session: Session,
                      order_id: int,
                      station_id: int,
                      customer_id: int) -> bool:
        """
        Delete a review for the given order_id, station_id, and customer_id.
        :param session: SQLAlchemy session
        :param order_id: Order ID
        :param station_id: Station ID
        :param customer_id: Customer ID
        """
        review = cls.get_review(session, order_id, station_id, customer_id)
        if not review:
            raise review_not_found_exception()

        # Delete the review from the session and commit the changes
        session.delete(review)
        # Commit the session to persist the changes to the database
        session.commit()

        return True

    @classmethod
    def _check_order_exists(cls,
                            session: Session,
                            order_id: int,
                            station_id: int,
                            customer_id: int) -> bool:
        """
        Check if an order exists for the given order_id, station_id, and customer_id.
        :param session: SQLAlchemy session
        :param order_id: Order ID
        :param station_id: Station ID
        :param customer_id: Customer ID
        :return: True if the order exists, False otherwise
        """
        order = session.scalar(
            select(OrderModel).where(
                OrderModel.id == order_id,
                OrderModel.station_id == station_id,
                OrderModel.customer_id == customer_id
            )
        )
        return order is not None

    @classmethod
    def _check_rating_value(cls, rating: float) -> bool:
        """
        Check if the rating value is within the valid range (1 to 5).
        :param rating: Rating value to check
        :return: True if valid, False otherwise
        """
        return 1 <= rating <= 5
