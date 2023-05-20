from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from bson import ObjectId
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from pydantic import BaseModel

app = FastAPI()
client = MongoClient("mongodb://localhost:27017/")
db = client["mydatabase"]
collection = db["books"]

class Book(BaseModel):
    title: str
    author: str
    year: int

@app.get("/List_Of_Books")
async def get_books():
    collection = db["books"]
    try:
        books = list(collection.find())
        for book in books:
            book["_id"] = str(book["_id"])  # Convert ObjectId to string
        return {"data": books}
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/Sort_books")
async def get_books_sort(sort: Optional[str] = None, filter: Optional[str] = None):
    try:
        # Sorting
        sort_query = {}
        if sort:
            sort_fields = sort.split(",")
            for field in sort_fields:
                if field.startswith("-"):
                    sort_query[field[1:]] = -1
                else:
                    sort_query[field] = 1

        # Filtering
        filter_query = {}
        if filter:
            filter_fields = filter.split(",")
            for field in filter_fields:
                key, value = field.split("*")
                filter_query[key] = value

        # Fetch books from MongoDB
        books = collection.find(filter_query).sort(list(sort_query.items()))

        # Serialize books
        serialized_books = [
            Book(title=book["title"], author=book["author"], year=book["year"])
            for book in books
        ]

        response_data = {"data": [book.dict() for book in serialized_books]}
        return JSONResponse(content=response_data)
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/Find_Book")
def get_book_find(book_id: str):
    try:
        book = collection.find_one({"_id": ObjectId(book_id)})
        if book:
            book_data = {
                "title": book["title"],
                "author": book["author"],
                "year": book["year"],
            }
            response_data = {"data": book_data}
            return JSONResponse(content=response_data)
        else:
            raise HTTPException(status_code=404, detail="Book not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/Create_Book")
def create_book(title: str, author: str, year: int):
    try:
        book_data = {"title": title, "author": author, "year": year}
        inserted_book = collection.insert_one(book_data)
        book_id = str(inserted_book.inserted_id)
        book = Book(title=title, author=author, year=year)
        response_data = {"data": book.dict()}
        return JSONResponse(content=response_data, status_code=201)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/Update_Book")
def update_book(book_id: str, title: str = None, author: str = None, year: int = None):
    try:
        book = collection.find_one({"_id": ObjectId(book_id)})
        if book:
            updated_fields = {}
            if title is not None:
                updated_fields["title"] = title
            if author is not None:
                updated_fields["author"] = author
            if year is not None:
                updated_fields["year"] = year
            if updated_fields:
                collection.update_one(
                    {"_id": ObjectId(book_id)}, {"$set": updated_fields}
                )
                updated_book = collection.find_one({"_id": ObjectId(book_id)})
                updated_book_data = {
                    "title": updated_book["title"],
                    "author": updated_book["author"],
                    "year": updated_book["year"],
                }
                response_data = {"data": updated_book_data}
                return JSONResponse(content=response_data)
            else:
                raise HTTPException(status_code=400, detail="No fields to update")
        else:
            raise HTTPException(status_code=404, detail="Book not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/Delete_Book")
def delete_book(book_id: str):
    try:
        result = collection.delete_one({"_id": ObjectId(book_id)})
        if result.deleted_count > 0:
            response_data = {"message": "Book deleted"}
            return JSONResponse(content=response_data)
        else:
            raise HTTPException(status_code=404, detail="Book not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))