from fastapi import APIRouter, Request, status
from fastapi.responses import RedirectResponse
from fastapi.exceptions import HTTPException
from fastapi.templating import Jinja2Templates
from db.database import direct_get_conn
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

# router 생성
router = APIRouter(prefix="/gpt", tags=["gpt"])

# jinja2 template 엔진 생성
templates = Jinja2Templates(directory="templates")

@router.get("/")
async def get_all_gpt(request: Request):
  return {"message": "gpt router 입니다."}