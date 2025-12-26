import sqlalchemy
from datetime import datetime


def main():
    meta = sqlalchemy.MetaData()

    engine = sqlalchemy.create_engine("sqlite://")

    table_1 = sqlalchemy.Table(
        "table_1",
        meta,
        sqlalchemy.Column(
            "col_11", sqlalchemy.Integer, primary_key=True, autoincrement=True
        ),
        sqlalchemy.Column("col_12", sqlalchemy.String),
        sqlalchemy.Column("col_13", sqlalchemy.DateTime, default=datetime.now),
    )

    table_2 = sqlalchemy.Table(
        "table_2",
        meta,
        sqlalchemy.Column(
            "col_21", sqlalchemy.Integer, primary_key=True, autoincrement=True
        ),
        sqlalchemy.Column("col_22", sqlalchemy.String),
    )

    meta.create_all(engine)

    conn = engine.connect()

    q = sqlalchemy.insert(table_1).values(col_12="value_1")
    conn.execute(q)
    q = sqlalchemy.insert(table_2).values(col_22="value_22")
    conn.execute(q)

    q = sqlalchemy.select([table_1, table_2])
    rows = conn.execute(q)

    for row in rows:
        print(row)


if __name__ == "__main__":
    main()
