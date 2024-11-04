from fastapi import APIRouter, Request, status, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.exceptions import HTTPException
from fastapi.templating import Jinja2Templates
from db.database import direct_get_conn, context_get_conn
from schemas.blog_schema import Blog
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text, Connection
from utils import util
from utils.util import truncate_text

# router 생성
router = APIRouter(prefix="/blogs", tags=["blogs"])

# jinja2 template 엔진 생성
templates = Jinja2Templates(directory="templates/blogs")

@router.get("/")
async def get_all_blogs(request: Request):
  conn=None
  try:
      # direct_get_conn() 함수를 이용하여 DB 연결
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
          content=truncate_text(row.content),
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

@router.get("/show/{id}")
def get_blog_by_id(request: Request, id: int,
                   conn: Connection = Depends(context_get_conn)):
  try:
      query = """
          SELECT id, title, author, content, image_loc, modified_dt FROM blog 
          WHERE id = :id
      """
      stmt = text(query)
      bind_stmt = stmt.bindparams(id=id)
      result = conn.execute(bind_stmt)
      
      # 검색 결과 있는지 확인, 없을 경우 404 에러 발생
      if result.rowcount == 0:
          raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                              detail="해당 블로그 정보(ID)가 없습니다.")
      
      row = result.fetchone()
      blog = Blog(id=row[0],
                  title=row[1],
                  author=row[2],
                  content=util.newline_to_br(row[3]),
                  image_loc=row[4],
                  modified_dt=row[5])
      result.close()

      return templates.TemplateResponse(
          request=request,
          name="show_blog.html",
          context={"blog": blog})

  except SQLAlchemyError as e:
      print(e)
      raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                          detail="요청 서비스가 내부적인 문제로 잠시 제공할 수 없습니다.")
  except Exception as e:
      print(e)
      raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                          detail="알수없는 이유로 서비스 오류가 발생했습니다.")


@router.get("/modify/{id}")
def update_blog_ui(request: Request, id: int,
                   conn: Connection = Depends(context_get_conn)):
  try:
      query = """
          SELECT id, title, author, content, image_loc, modified_dt FROM blog 
          WHERE id = :id
      """
      stmt = text(query)
      bind_stmt = stmt.bindparams(id=id)
      result = conn.execute(bind_stmt)
      
      # 검색 결과 있는지 확인, 없을 경우 404 에러 발생
      if result.rowcount == 0:
          raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                              detail="해당 블로그 정보(ID)가 없습니다.")
      
      row = result.fetchone()
      result.close()

      return templates.TemplateResponse(
          request=request,
          name="modify_blog.html",
          context={"id": row.id, "title": row.title, "author": row.author, 
                    "content": row.content})

  except SQLAlchemyError as e:
      print(e)
      raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                          detail="요청 서비스가 내부적인 문제로 잠시 제공할 수 없습니다.")
  except Exception as e:
      print(e)
      raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                          detail="알수없는 이유로 서비스 오류가 발생했습니다.")
    

@router.post("/modify/{id}")
def update_blog(request: Request, id: int,
                title: str = Form(min_length=2, max_length=200),
                author: str = Form(max_length=100),
                content: str = Form(min_length=2, max_length=4000),
                conn: Connection = Depends(context_get_conn)):
  
  try: 
    sql = f"""
      UPDATE blog
      SET title = :title, author = :author, content = :content  
      where id = :id
    """
    bind_stmt = text(sql).bindparams(id=id, title=title, 
                                          author=author, content=content)
    result = conn.execute(bind_stmt)

    # 수정된 레코드 수가 0이면 404 에러 발생 => 수정할 레코드가 없음
    if result.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="수정할 블로그 정보(ID)가 없습니다.")
    
    conn.commit() # 변경사항 저장
    return RedirectResponse(url=f"/blogs/show/{id}", 
                            status_code=status.HTTP_303_SEE_OTHER)

  except SQLAlchemyError as e:
      print(e)
      conn.rollback()  # 변경사항 롤백(보류중인 모든 데이터 변경 사항 취소, 트랜잭션 종료)
      raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                          detail="요청 서비스가 내부적인 문제로 잠시 제공할 수 없습니다.")
  

@router.post("/delete/{id}")
def delete_blog(request: Request, id: int,
                conn: Connection = Depends(context_get_conn)):   

  try:
    sql = f"""
      DELETE FROM blog 
      where id = :id
    """
    bind_stmt = text(sql).bindparams(id=id)
    result = conn.execute(bind_stmt)

    # 삭제할 레코드가 없음
    if result.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"해당 id({id})가(은) 존재하지 않습니다.")
    
    conn.commit() # 변경사항 저장
    return RedirectResponse(url=f"/blogs", 
                            status_code=status.HTTP_303_SEE_OTHER)
  except SQLAlchemyError as e:
      print(e)
      conn.rollback()
      raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                          detail="요청 서비스가 내부적인 문제로 잠시 제공할 수 없습니다.")  
    
@router.get("/new")
def create_blog_ui(request: Request):
  return templates.TemplateResponse(
      request=request,
      name="create_blog.html",
      context={})

@router.post("/new")
def create_blog(request: Request,
                title: str = Form(min_length=2, max_length=200),
                author: str = Form(max_length=100),
                content: str = Form(min_length=2, max_length=4000),
                conn: Connection = Depends(context_get_conn)
                ):
  try:
     sql = f"""
      INSERT INTO blog (title, author, content, modified_dt)
      values ('{title}', '{author}', '{content}', now())
      """
     print(sql)
     
     conn.execute(text(sql))
     conn.commit()
     return RedirectResponse(url="/blogs", status_code=status.HTTP_303_SEE_OTHER)
  
  except SQLAlchemyError as e:
      print(e)
      conn.rollback()
      raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                          detail="요청 서비스가 내부적인 문제로 잠시 제공할 수 없습니다.")

