#!/usr/bin/env python3

import os
import sys
import requests
import xml.etree.ElementTree as ET
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

key = os.getenv("GOODREADS_API_KEY")

# Get all existing book isbns from database that don't have an image
NoCoverBooks= db.execute("SELECT isbn from books WHERE cover_img IS NULL").fetchall()
#print(NoCoverBooks, file=sys.stderr)

# call GoodReads API for each isbn
for isbn in NoCoverBooks:
	print(f"ISBN: {isbn[0]}", file=sys.stderr)
	GetBookbyIsbn = requests.get("https://www.goodreads.com/search/index.xml?key=" + key + "&q=" + isbn[0])

	if GetBookbyIsbn.status_code == 200:
		root = ET.fromstring(GetBookbyIsbn.text)

		for search in root.findall('search'):
			for results in search.findall('results'):
				for works in results.findall('work'):
					for best_book in works.findall("best_book"):
						for image_url in best_book.findall("image_url"):
							cover_img = image_url.text
							#TODO skip the GoodReads placeholder image
							NewBookCoverImage = db.execute("UPDATE books SET cover_img= :cover_img WHERE isbn= :isbn",
								{"cover_img": cover_img, "isbn": isbn[0]})
							db.commit()
	else:
		print("Not Sucessfull", file=sys.stderr)
print("--END--", file=sys.stderr)