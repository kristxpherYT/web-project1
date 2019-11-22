from sqlalchemy import create_engine, cast, Integer
from sqlalchemy.orm import scoped_session, sessionmaker
import csv
import os
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')  # Path to .env file
load_dotenv(dotenv_path)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    file = open("books.csv")
    reader = csv.reader(file)
    next(reader, None)
    for isbn, title, author, year in reader:
        db.execute("INSERT INTO books(isbn, title, author, publication_year) VALUES (:isbn, :title, :author, :year)",
            {"isbn": isbn, "title": title, "author": author, "year": year})
        print(f"Book {title} from {author} ({year}) added.")
    db.commit()
    print("Import Successful")

if __name__ == "__main__":
    main()