import os
import logging
from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from dotenv import load_dotenv
from bson.json_util import dumps
from fastapi.responses import JSONResponse
from fastapi import Query
from fastapi import Path
from bson import ObjectId

app = FastAPI()
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Retrieve MongoDB connection URL from environment variable
url = os.environ.get("url")
if not url:
    raise EnvironmentError("MongoDB connection URL not found in environment variables")

client = MongoClient(url)
db = client["CosmoCloud"]
collection = db["Student"]


@app.get("/")
def greetUser():
    return {"message":"CosmoCloud Backend asssignment"}
    

#api call to get the students based on the age and the country parameter
@app.get("/students/")
async def get_students(age: int = Query(None, description="age", gt=0), 
                       country: str = Query(None, description="Country")):
    try:
        logger.info(f"Filtering students with min_age={age} and country={country}")
        
        filter_query = {}
        if age is not None and country:
            filter_query = {"$and": [{"age": {"$gte": age}}, {"address.country": country}]}
        elif age is not None:
            filter_query = {"age": {"$gte": age}}
        elif country:
            filter_query = {"address.country": country}
    
        projection = {"_id": 0, "name": 1, "age": 1}
        logger.info(f"Filter query: {filter_query}")
        students_cursor = collection.find(filter_query, projection)

        students = [{"name": student["name"], "age": student["age"]} for student in students_cursor]

        return JSONResponse(content={"data": students}, status_code=200)
    except Exception as e:
        logger.error(f"Failed to fetch students: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch students from the database")

#aPI CALL for get/Students/{id}
@app.get("/students/{id}")
async def get_student_by_id(id: str = Path(..., description="Student ID")):
    try:

        logger.info(f"Retrieving student with ID: {id}")
        student_id_object = ObjectId(id)
        student = collection.find_one({"_id": student_id_object})

        if student is not None:
            
            student.pop("_id", None)
            logger.info(f"Found student: {student}")
            return JSONResponse(content={"student": student}, status_code=200)
        
        else:

            logger.warning(f"No student found with ID: {id}")
            raise HTTPException(status_code=404, detail="Student not found")
    except Exception as e:
        logger.error(f"Failed to fetch student: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch student from the database")


@app.post("/students/")
async def create_student(student_data: dict):
    try:
        logger.info("Creating a new student")
        
        # Insert the new student into the database
        result = collection.insert_one(student_data)

        if result.inserted_id:
            logger.info(f"Student created successfully with ID: {result.inserted_id}")
            # Return the ID of the newly created student with status code 201
            return JSONResponse(content={"id": str(result.inserted_id)}, status_code=201)
        else:
            logger.warning("Failed to create student")
            raise HTTPException(status_code=500, detail="Failed to create student")
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to create student: {e}")
        raise HTTPException(status_code=500, detail="Failed to create student")


#api call for deleting the student by id
@app.delete("/students/{id}")
async def delete_student_by_id(id: str = Path(..., description="Student ID")):
    try:
        logger.info(f"Deleting student with ID: {id}")
        student_id_object = ObjectId(id)

        # Check if the student exists
        student = collection.find_one({"_id": student_id_object})
        if student is None:
            logger.warning(f"No student found with ID: {id}")
            raise HTTPException(status_code=404, detail="Student not found")

        # Delete the student
        result = collection.delete_one({"_id": student_id_object})
        if result.deleted_count == 1:
            logger.info(f"Student deleted successfully: {id}")
            # Return an empty JSON response with status code 200
            return JSONResponse(content={}, status_code=200)
        else:
            logger.warning(f"Failed to delete student: {id}")
            raise HTTPException(status_code=500, detail="Failed to delete student")
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to delete student: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete student")


#patch request for updating 
@app.patch("/students/{id}")
async def update_student(id: str, student_data: dict):
    try:

        logger.info(f"Updating student with ID: {id}")
        student_id_object = ObjectId(id)
        
        existing_student = collection.find_one({"_id": student_id_object})
        if existing_student is None:
            logger.warning(f"No student found with ID: {id}")
            raise HTTPException(status_code=404, detail="Student not found")

        
        update_result = collection.update_one({"_id": student_id_object}, {"$set": student_data})
        
        if update_result.modified_count > 0:
            logger.info(f"Student updated successfully: {id}")
            return JSONResponse(content={}, status_code=204)
        else:
            logger.warning("Failed to update student")
            raise HTTPException(status_code=500, detail="Failed to update student")
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to update student: {e}")
        raise HTTPException(status_code=500, detail="Failed to update student")