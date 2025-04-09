from __future__ import annotations

import enum
import os

from sqlalchemy import (
    Column,
    Enum,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


"""
   +-------+     +---+           +---------+
   |Company| --> |Car| ----+---> |Ownership|
   +-------+     +---+     |     +---------+
 +----------+     +-----+  |
 |CreditCard| --> |Human| -+
 +----------+     +-----+
"""

class CreditCard(Base):
    __tablename__ = "credit_card"

    card_id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(Text)
    bounded = Column(Integer)

    user = relationship("Human")


class Company(Base):
    __tablename__ = "company"

    company_id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(Text)
    location = Column(Text)


class CarType(str, enum.Enum):
    gasoline = "gasoline"
    electric = "electric"
    hybrid_electric = "hybrid_electric"


class Car(Base):
    __tablename__ = "car"

    car_id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(Text)
    drivetrain = Column(Enum(CarType))
    maker_id = Column(Integer, ForeignKey(Company.company_id))
    price = Column(Integer)


class Human(Base):
    __tablename__ = "human"

    id_number = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text)
    credit_card_id = Column(Integer, ForeignKey(CreditCard.card_id))


class Ownership(Base):
    __tablename__ = "ownership"

    human_id = Column(Integer, ForeignKey(Human.id_number))
    car_id = Column(Integer, ForeignKey(Car.car_id))
    register_num = Column(Text, unique=True)

    __table_args__ = (PrimaryKeyConstraint(human_id, car_id),)


def prepare_data():
    if os.path.exists("test.db"):
        os.remove("test.db")

    engine = create_engine(
        "sqlite:///db.sqlite3",
        echo=True,
    )

    session_obj = sessionmaker()
    sess = session_obj(bind=engine)

    try:
        Base.metadata.create_all(engine)

        cards = [
            CreditCard(provider="samsung", bounded=100000),
            CreditCard(provider="hyundai", bounded=20000),
            CreditCard(provider="shinhan", bounded=3000000),
            CreditCard(provider="kookmin", bounded=4000),
        ]
        sess.add_all(cards)
        sess.flush()

        companies = [
            Company(name="porsche", location="German"),
            Company(name="audi", location="German"),
            Company(name="bmw", location="German"),
            Company(name="jeep", location="USA"),
            Company(name="tesla", location="USA"),
            Company(name="ford", location="USA"),
            Company(name="Lamborghini", location="Italy"),
        ]
        sess.add_all(companies)
        sess.flush()

        cars = [
            Car(
                name="911",
                drivetrain=CarType.gasoline,
                maker_id=0,
                price=50000,
            ),
            Car(
                name="356",
                drivetrain=CarType.gasoline,
                maker_id=0,
                price=100000,
            ),
            Car(
                name="R8", drivetrain=CarType.gasoline, maker_id=1, price=45000
            ),
            Car(
                name="A4", drivetrain=CarType.gasoline, maker_id=1, price=32000
            ),
            Car(
                name="A6", drivetrain=CarType.gasoline, maker_id=1, price=38000
            ),
            Car(
                name="M5", drivetrain=CarType.gasoline, maker_id=2, price=35000
            ),
            Car(
                name="X3", drivetrain=CarType.gasoline, maker_id=2, price=35000
            ),
            Car(
                name="Cherokee",
                drivetrain=CarType.gasoline,
                maker_id=3,
                price=38000,
            ),
            Car(
                name="Model 3",
                drivetrain=CarType.gasoline,
                maker_id=4,
                price=48000,
            ),
            Car(
                name="Model S",
                drivetrain=CarType.gasoline,
                maker_id=4,
                price=48000,
            ),
            Car(
                name="Model Y",
                drivetrain=CarType.gasoline,
                maker_id=4,
                price=48000,
            ),
            Car(
                name="mustang",
                drivetrain=CarType.gasoline,
                maker_id=5,
                price=55000,
            ),
        ]
        sess.add_all(cars)
        sess.flush()

        humans = [
            Human(
                name="ella",
                credit_card_id=cards[0].card_id,
            ),
            Human(
                name="scarlet",
                credit_card_id=cards[1].card_id,
            ),
            Human(
                name="wanda",
                credit_card_id=cards[1].card_id,
            ),
            Human(
                name="sally",
                credit_card_id=cards[3].card_id,
            ),
            Human(
                name="anastasia",
                credit_card_id=cards[2].card_id,
            ),
            Human(
                name="sandra",
                credit_card_id=cards[2].card_id,
            ),
            Human(
                name="penny",
                credit_card_id=cards[3].card_id,
            ),
        ]
        sess.add_all(humans)
        sess.flush()

        owners = [
            Ownership(
                human_id=humans[0].id_number,
                car_id=cars[1].car_id,
                register_num="abc1",
            ),
            Ownership(
                human_id=humans[1].id_number,
                car_id=cars[1].car_id,
                register_num="abc2",
            ),
            Ownership(
                human_id=humans[1].id_number,
                car_id=cars[2].car_id,
                register_num="abc3",
            ),
            Ownership(
                human_id=humans[2].id_number,
                car_id=cars[5].car_id,
                register_num="abc4",
            ),
            Ownership(
                human_id=humans[3].id_number,
                car_id=cars[5].car_id,
                register_num="abc5",
            ),
        ]
        sess.add_all(owners)
        sess.flush()
    except Exception as e:
        print(str(e))
        sess.rollback()
    else:
        sess.commit()
