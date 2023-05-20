from typing import Optional,List,Union
from fastapi import FastAPI,HTTPException
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
    id: str
    type: str = "articles"
    attributes: dict

class ArticleAuthor(BaseModel):
    id: str
    type: str = "people"
    links: dict

class ArticleComment(BaseModel):
    id: str
    type: str = "comments"

class ArticleData(BaseModel):
    id: str
    type: str = "articles"
    attributes: dict
    relationships: dict
    links: dict

class ArticleResponse(BaseModel):
    links: dict
    data: List[ArticleData]
    included: List[Union[ArticleAuthor, ArticleComment]]

@app.get("/List_Of_Books")
async def get_books():
    try:
        books = list(collection.find())
        count = len(books)
        for book in books:
            book["_id"] = str(book["_id"])  # Convert ObjectId to string
        serialized_books = [
            Book(id=str(book["_id"]), attributes={"title": book["title"]}).dict()
            for book in books
        ]
        response_data = {"count":count, "data": serialized_books}
        return JSONResponse(content=response_data)
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
            Book(id=str(book["_id"]), attributes={"title": book["title"]}).dict()
            for book in books
        ]

        response_data = {"data": serialized_books}
        return JSONResponse(content=response_data)
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/Find_Book")
def get_book_find(book_id: str):
    try:
        book = collection.find_one({"_id": ObjectId(book_id)})
        if book:
            book_attributes = {"title": book["title"], "author": book["author"], "year": book["year"]}
            author_id = str(book["_id"])
            author_links = {
                "self": f"http://Raja_Kannan_example.com/articles/1/relationships/author",
                "related": f"http://Skill_Rackexample.com/articles/1/author"
            }
            author = ArticleAuthor(id=author_id, links=author_links)
            comments = [
                ArticleComment(id=str(comment["_id"]))
                for comment in collection.find({"book_id": ObjectId(book_id)})
            ]
            article_data = ArticleData(
                id=str(book["_id"]),
                attributes=book_attributes,
                relationships={"author": {"data": author}, "comments": {"data": comments}},
                links={"self": f"http://samplebyRkexample.com/articles/{book_id}"},
            )
            included_data = [author] + comments
            response_data = ArticleResponse(
                links={
                    "self": "http://example.com/articles",
                    "next": "http://example.com/articles?page[offset]=2",
                    "last": "http://example.com/articles?page[offset]=10"
                },
                data=[article_data],
                included=included_data
            )
            return JSONResponse(content=response_data.dict())
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
        book = Book(id=book_id, attributes={"title": title, "author": author, "year": year})
        count =collection.count_documents({})
        response_data = {"count":count,"data": book.dict()}
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
