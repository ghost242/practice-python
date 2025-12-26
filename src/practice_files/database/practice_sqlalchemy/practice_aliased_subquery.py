from operator import concat

from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import (
    Query,
    aliased,
    column_property,
    sessionmaker,
    subqueryload,
)

from .model import (
    Base,
    Company,
    CreditCard,
    Car,
    Human,
    Ownership,
    prepare_data,
)


def practice_annotation_(sess):
    """annotation은 django 프레임워크의 ORM 쿼리함수인데, SQLAlchemy로 어떻게 번역해야 하는지에 대한 테스트를 수행"""
    inspection = inspect(Car)

    car_list_q = (
        Query(concat(inspection.columns, [Human.name.label("owner")]))
        .join(Car, Car.car_id == Ownership.car_id)
        .subquery()
    )

    print(
        list(
            getattr(type("TempModel", tuple(), dict(t._asdict())), "owner")
            for t in sess.query(car_list_q).all()
        )
    )
    print([t._asdict() for t in sess.query(car_list_q).all()])
    print(sess.query(Car).all())
    stmt = sess.query(Human.name).label("owner")

    print(
        list(
            map(
                lambda c: c._asdict(),
                sess.query(*inspection.columns, stmt).all(),
            )
        )
    )


def practice_prefetch_(sess):
    humans = sess.query(Human).filter(Human.name == "wanda").subquery()
    ownership = (
        sess.query(Ownership)
        .join(humans, humans.c.id_number == Ownership.human_id)
        .subquery()
    )
    used_car = (
        sess.query(Car)
        .join(ownership, ownership.c.car_id == Car.car_id)
        .subquery()
    )
    # makers = sess.query(Company).subquery()
    car_list = sess.query(Company).join(used_car).first()

    print(car_list)


def main():
    engine = create_engine("sqlite:///db.sqlite3", echo=True)

    session_obj = sessionmaker(engine)

    sess = session_obj()
    practice_prefetch_(sess)


if __name__ == "__main__":
    # prepare_data()
    main()
