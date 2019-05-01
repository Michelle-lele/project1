#!/usr/bin/env python3

import os
import csv
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

#TO DO error handling 

meta = MetaData()

books = Table(
	'books', meta,
	Column('isbn',String, primary_key=True, nullable=False, unique=True),
	Column('title',String, nullable=False),
	Column('author',String, nullable=False),
	Column('year', String, nullable=False)
	)
meta.create_all(engine)
#books.drop(engine)?

f = open("books.csv")
reader = csv.reader(f)
for isbn, title, author, year in reader:#TO DO also imports csv header titles
	db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)", 
	{"isbn": isbn,"title": title,"author": author, "year": year})
	print(f"Added {title} by {author}, {year} ({isbn})")
db.commit()
print("---END---")
