from fastapi import APIRouter, Request, status
from fastapi.responses import RedirectResponse
from fastapi.exceptions import HTTPException
from fastapi.templating import Jinja2Templates
from db.database import direct_get_conn
from schemas.blog_schema import Blog
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

# router 생성
router = APIRouter(prefix="/blogs", tags=["blogs"])

# jinja2 template 엔진 생성
templates = Jinja2Templates(directory="templates")

@router.get("/")
async def get_all_blogs(request: Request):
    conn=None
    try:
        conn = direct_get_conn()
        query = """
            SELECT id, title, author, content, image_loc, modified_dt FROM blog
        """
        result = conn.execute(text(query))
        # rows = result.fetchall()
        all_blogs = [Blog(
            id=row.id,               # id=row[0]
            title=row.title,
            author=row.author,
            content=row.content,
            image_loc=row.image_loc,
            modified_dt=row.modified_dt) for row in result]
        
        result.close()
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"all_blogs": all_blogs}
        )
    except SQLAlchemyError as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="요청 서비스가 내부적인 문제로 잠시 제공할 수 없습니다.")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="알수없는 이유로 서비스 오류가 발생했습니다.")
    finally:
        if conn:
            conn.close()




