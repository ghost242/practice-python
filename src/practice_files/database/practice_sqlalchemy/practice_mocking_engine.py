from __future__ import annotations

from contextlib import contextmanager
import enum
import os
import logging

from sqlalchemy import (
    Column,
    Enum,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    Text,
)
from sqlalchemy.engine import create_engine
from sqlalchemy.engine.mock import create_mock_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

import factory

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


def dump(sql, *multiparams, **params):
    print(sql.compile(dialect=engine.dialect))


engine = create_mock_engine(
    "mysql+mysqlconnector://",
    executor=dump,
)
Base.metadata.create_all(engine, checkfirst=False)

maker = sessionmaker(bind=engine)
session = maker()


class FactoryCreditCard(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = CreditCard
        sqlalchemy_session = session

    provider = "Samsung"
    bounded = 500000


class FactoryCompany(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Company
        sqlalchemy_session = session

    name = "Volkswagen"
    location = "Germany"


class FactoryCar(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Car
        sqlalchemy_session = session

    name = "Beetle"
    drivetrain = "FWD"
    maker_id = factory.RelatedFactory(
        FactoryCompany, factory_related_name="company_id"
    )
    price = 250000


class FactoryHuman(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Human
        sqlalchemy_session = session

    name = "Dick"
    credit_card_id = factory.RelatedFactory(
        FactoryCreditCard, factory_related_name="card_id"
    )


class FactoryOwnership(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Ownership
        sqlalchemy_session = session

    human_id = factory.RelatedFactory(
        FactoryHuman, factory_related_name="id_number"
    )
    car_id = factory.RelatedFactory(FactoryCar, factory_related_name="car_id")


def main():
    logging.getLogger().setLevel(logging.DEBUG)

    FactoryCompany()
    FactoryCar()

    print(session.query(Car).all())
    # print(session.query(CreditCard).all())
    # for m in dir(session):
    #     if m.startswith('_'):
    #         continue
    #     print(m, callable(getattr(session, m)))

    # print(dir(session.connection()))
    # print(session.connection())

    # with get_test_session() as test_session:

    #     print(test_session)
    #     print(dir(test_session))


if __name__ == "__main__":
    main()
