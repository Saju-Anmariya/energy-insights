import pandas as pd

from app.database import Base, engine, SessionLocal
from app.models import Consumption

CSV_PATH = "data/raw/consumption.csv"
TIME_COL = "Datum von"
VALUE_COL = "Netzlast [MWh] Berechnete Auflösungen"


def main():
    df = pd.read_csv(CSV_PATH, sep=";", decimal=",", thousands=".")
    df = df[[TIME_COL, VALUE_COL]].dropna()
    df[TIME_COL] = pd.to_datetime(df[TIME_COL], dayfirst=True)
    df = df.drop_duplicates(subset=TIME_COL)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.query(Consumption).delete()
        db.bulk_save_objects(
            [
                Consumption(timestamp=t.to_pydatetime(), mwh=float(v))
                for t, v in zip(df[TIME_COL], df[VALUE_COL])
            ]
        )
        db.commit()
        print(f"Loaded {len(df)} rows")
    finally:
        db.close()


if __name__ == "__main__":
    main()