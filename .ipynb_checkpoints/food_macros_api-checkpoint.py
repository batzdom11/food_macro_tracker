from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Float, Integer, ForeignKey
from sqlalchemy.orm import sessionmaker, Session, declarative_base
import requests
import json
import re
from passlib.context import CryptContext
import os
import openai


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Load from environment
if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API Key. Set it in environment variables.")
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)


# Database setup (SQLite for local, change to PostgreSQL/MySQL for cloud hosting)
DATABASE_URL = "sqlite:///./food_macros.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

class Food(Base):
    __tablename__ = "foods"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    calories = Column(Float, nullable=False)
    protein = Column(Float, nullable=False)
    carbs = Column(Float, nullable=False)
    fats = Column(Float, nullable=False)

class Meal(Base):
    __tablename__ = "meals"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    meal_name = Column(String, nullable=False)
    food_name = Column(String, nullable=False)
    grams = Column(Float, nullable=False)
    protein = Column(Float, nullable=False)
    carbs = Column(Float, nullable=False)
    fats = Column(Float, nullable=False)

class TargetMacros(Base):
    __tablename__ = "target_macros"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    weight = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    body_fat = Column(Float, nullable=False)
    activity_level = Column(String, nullable=False)
    goal = Column(String, nullable=False)
    tdee = Column(Float, nullable=False)
    target_calories = Column(Float, nullable=False)
    protein = Column(Float, nullable=False)
    carbs = Column(Float, nullable=False)
    fats = Column(Float, nullable=False)

class DailyMacro(Base):
    __tablename__ = "daily_macros"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(String, nullable=False)  # or use a proper Date if you prefer
    protein = Column(Float, nullable=False)
    carbs = Column(Float, nullable=False)
    fats = Column(Float, nullable=False)
    calories = Column(Float, nullable=False)


# Create the new table
Base.metadata.create_all(bind=engine)

# FastAPI instance
app = FastAPI()

# Pydantic schema
class FoodCreate(BaseModel):
    name: str
    calories: float
    protein: float
    carbs: float
    fats: float

class MealCreate(BaseModel):
    meal_name: str
    food_name: str
    grams: float
    protein: float
    carbs: float
    fats: float
    
class TargetMacrosCreate(BaseModel):
    weight: float
    height: float
    body_fat: float
    activity_level: str
    goal: str
    tdee: float
    target_calories: float
    protein: float
    carbs: float
    fats: float

class DailyMacroCreate(BaseModel):
    date: str
    protein: float
    carbs: float
    fats: float
    calories: float


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    return {"message": "FastAPI is running"}

# User registration and login
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@app.post("/register/")
def register(credentials: dict, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == credentials["username"]).first()
    if user:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    hashed_password = pwd_context.hash(credentials["password"])
    new_user = User(username=credentials["username"], hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully!"}

@app.post("/login/")
def login(credentials: dict, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == credentials["username"]).first()
    if not user or not pwd_context.verify(credentials["password"], user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return {"id": user.id, "username": user.username}

@app.post("/foods/{user_id}", response_model=FoodCreate)
def add_food(user_id: int, food: FoodCreate, db: Session = Depends(get_db)):
    new_food = Food(user_id=user_id, **food.dict())
    db.add(new_food)
    db.commit()
    db.refresh(new_food)
    return new_food

@app.get("/foods/{user_id}")
def get_foods(user_id: int, db: Session = Depends(get_db)):
    return db.query(Food).filter(Food.user_id == user_id).all()

@app.delete("/foods/{user_id}/{name}")
def delete_food(user_id: int, name: str, db: Session = Depends(get_db)):
    food = db.query(Food).filter(Food.user_id == user_id, Food.name == name).first()
    if not food:
        raise HTTPException(status_code=404, detail="Food not found")
    db.delete(food)
    db.commit()
    return {"message": "Food deleted successfully"}

@app.post("/save_meal/{user_id}")
def save_meal(user_id: int, meal_entries: list[MealCreate], db: Session = Depends(get_db)):
    """
    Saves a full meal (list of foods) to the database under a user-defined name,
    preventing duplicate meal names for that user.
    """

    if not meal_entries:
        raise HTTPException(status_code=400, detail="No meal data provided.")

    # We'll assume all entries in meal_entries share the same meal_name.
    meal_name = meal_entries[0].meal_name

    # Check if the user already has a meal with this name
    existing_meals = db.query(Meal).filter(
        Meal.user_id == user_id,
        Meal.meal_name == meal_name
    ).first()

    if existing_meals:
        raise HTTPException(
            status_code=400,
            detail=f"Meal name '{meal_name}' already exists for this user. Please choose a different name."
        )

    # If no duplicates, proceed to store
    for meal in meal_entries:
        new_meal = Meal(user_id=user_id, **meal.dict())
        db.add(new_meal)

    db.commit()

    return {"message": "Meal saved successfully!"}


@app.get("/meals/names/{user_id}")
def get_meal_names(user_id: int, db: Session = Depends(get_db)):
    names = db.query(Meal.meal_name).filter(Meal.user_id == user_id).distinct().all()
    return [name[0] for name in names]

@app.get("/meals/{user_id}/{meal_name}")
def get_meal_by_name(user_id: int, meal_name: str, db: Session = Depends(get_db)):
    meals = db.query(Meal).filter(Meal.user_id == user_id, Meal.meal_name == meal_name).all()
    if not meals:
        raise HTTPException(status_code=404, detail="Meal not found")
    return meals



import logging

@app.post("/generate_meal/")
def generate_meal(data: dict, db: Session = Depends(get_db)):
    try:
        logging.info("Received meal generation request")
        prompt = data.get("prompt", "")
        use_food_list = data.get("use_food_list", True)

        logging.info(f"Use food list: {use_food_list}")

        if use_food_list:
            foods = db.query(Food).all()
            if not foods:
                raise HTTPException(status_code=404, detail="No foods found in database.")

            food_list = "\n".join([
                f"{f.name}: {f.calories} kcal, {f.protein}g protein, {f.carbs}g carbs, {f.fats}g fats"
                for f in foods
            ])
            food_prompt = f"Use ONLY these foods:\n{food_list}\n"
        else:
            food_prompt = "You can freely suggest any nutritious ingredients suitable for balanced meals."

        final_prompt = f"""
        You are a professional nutritionist and chef.

        {food_prompt}

        {prompt}
        """.strip()

        logging.info(f"Final prompt sent to OpenAI: {final_prompt}")

        # OpenAI API Call
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {"role": "system", "content": "You are a nutrition assistant. Always respond in valid JSON format."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}  # Forces OpenAI to return JSON
        )
    
        meal_plan = response.choices[0].message
        logging.info(f"Full OpenAI Response: {response.model_dump_json(indent=2)}")
        return {"meal_plan": meal_plan}

    except Exception as e:
        logging.error(f"Error in meal generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))




@app.get("/get_food_macros/{food_name}")
def get_food_macros(food_name: str):
    """
    Use OpenAI to estimate calories & macros per 100g for a given food.
    """
    prompt = f"""
    Provide the estimated nutritional values per 100g for {food_name} in valid JSON format:
    {{
      "calories": <float>,
      "protein": <float>,
      "carbs": <float>,
      "fats": <float>
    }}
    """

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {"role": "system", "content": "You are a nutrition assistant. Always respond in valid JSON format."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"} 
        )

        # Extract JSON data
        food_macros = response.choices[0].message.content
        return {
            "calories": float(food_macros.get("calories", 0.0)),
            "protein": float(food_macros.get("protein", 0.0)),
            "carbs": float(food_macros.get("carbs", 0.0)),
            "fats": float(food_macros.get("fats", 0.0)),
        }

    except Exception as e:
        logging.error(f"Error retrieving food macros for {food_name}: {str(e)}")
        return {
            "error": f"Could not retrieve macros for {food_name}. Please try again later.",
            "details": str(e)
        }


### Save entries on the Target Macros Page so the user doesn't have to start it over and over
@app.post("/target_macros/{user_id}")
def save_target_macros(user_id: int, data: TargetMacrosCreate, db: Session = Depends(get_db)):
    """
    Save or update the user's target macros.
    If row exists for user_id, update it; otherwise create a new row.
    """
    existing = db.query(TargetMacros).filter(TargetMacros.user_id == user_id).first()
    if existing:
        # Update row
        existing.weight = data.weight
        existing.height = data.height
        existing.body_fat = data.body_fat
        existing.activity_level = data.activity_level
        existing.goal = data.goal
        existing.tdee = data.tdee
        existing.target_calories = data.target_calories
        existing.protein = data.protein
        existing.carbs = data.carbs
        existing.fats = data.fats
    else:
        # Create new row
        new_tm = TargetMacros(user_id=user_id, **data.dict())
        db.add(new_tm)

    db.commit()
    return {"message": "Target macros saved/updated successfully!"}

@app.get("/target_macros/{user_id}")
def get_target_macros(user_id: int, db: Session = Depends(get_db)):
    """Retrieve the user’s saved target macros."""
    tm = db.query(TargetMacros).filter(TargetMacros.user_id == user_id).first()
    if not tm:
        raise HTTPException(status_code=404, detail="No target macros found for this user.")
    return {
        "weight": tm.weight,
        "height": tm.height,
        "body_fat": tm.body_fat,
        "activity_level": tm.activity_level,
        "goal": tm.goal,
        "tdee": tm.tdee,
        "target_calories": tm.target_calories,
        "protein": tm.protein,
        "carbs": tm.carbs,
        "fats": tm.fats
    }

@app.post("/user_daily_macros/{user_id}")
def save_user_daily_macros(
    user_id: int, data: DailyMacroCreate, db: Session = Depends(get_db)
):
    new_day = DailyMacro(
        user_id=user_id,
        date=data.date,
        protein=data.protein,
        carbs=data.carbs,
        fats=data.fats,
        calories=data.calories
    )
    db.add(new_day)
    db.commit()
    db.refresh(new_day)
    return {"message": f"Day macros for {data.date} saved successfully!"}

@app.get("/user_daily_macros/{user_id}")
def list_user_days(user_id: int, db: Session = Depends(get_db)):
    rows = db.query(DailyMacro).filter(DailyMacro.user_id == user_id).all()
    return rows




# Run the API
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
