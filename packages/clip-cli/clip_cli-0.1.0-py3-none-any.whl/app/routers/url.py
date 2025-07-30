from fastapi import APIRouter, Request, Depends, Response, status, HTTPException
from fastapi.responses import RedirectResponse
from .. import schemas, database, models, oauth2, utils
from sqlalchemy.orm import Session

router = APIRouter(prefix = '/url', tags = ['URL'])

@router.post('/shorten', response_model= schemas.UrlOut)
def shorten_url(url_data: schemas.UrlCreate, 
                request: Request, 
                db: Session = Depends(database.get_db), 
                current_user: models.User = Depends(oauth2.get_current_user)):
    
    url_already_exists = db.query(models.Url).filter(models.Url.original == str(url_data.original) , models.Url.owner_id == current_user.id).first()

    if url_already_exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Url already shortened")

    short_code = utils.generate_short_code()
    while db.query(models.Url).filter(models.Url.short_code == short_code).first():
        short_code = utils.generate_short_code()

    new_url = models.Url(
        original = str(url_data.original),
        short_code = short_code,
        owner_id = current_user.id
        )

    db.add(new_url)
    current_user.urls_created += 1

    db.commit()
    db.refresh(new_url)

    short_url = str(request.base_url) + short_code
    return {
        'id': new_url.id,
        'original': new_url.original,
        'short_code': new_url.short_code,
        'clicks': new_url.clicks,
        'created_at': new_url.created_at,
        'short_url': short_url
    }

@router.get("/by-id/{id}", response_model=schemas.UrlOut)
def get_one_url(id: int,request: Request, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    url = db.query(models.Url).filter(models.Url.id == id, models.Url.owner_id == current_user.id).first()

    if not url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Invalid id")
    
    short_url = str(request.base_url) + url.short_code
    return {
        'id': url.id,
        'original': url.original,
        'short_code': url.short_code,
        'clicks': url.clicks,
        'created_at': url.created_at,
        'short_url': short_url
    }

@router.get("/{short_code}", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
def redirect_to_original(short_code: str, db: Session = Depends(database.get_db), request: Request = None):
    url_entry = db.query(models.Url).filter(models.Url.short_code == short_code).first()

    if not url_entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Short Url not found")
    
    ip = request.client.host

    click = models.Click(url_id = url_entry.id, ip_address = ip)
    db.add(click)

    url_entry.clicks += 1

    db.commit()

    return RedirectResponse(url_entry.original)

@router.put('/{id}', response_model=schemas.UrlOut)
def update_short_code(updated_short_code: schemas.UrlUpdate, 
                      id: int, 
                      request: Request,
                      db: Session = Depends(database.get_db), 
                      current_user: models.User = Depends(oauth2.get_current_user)):
    
    url_query = db.query(models.Url).filter(models.Url.id == id)
    url = url_query.first()

    if not url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Url with id {id} not found")
    
    if url.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to perform this action")
    
    same_short_code = db.query(models.Url).filter(models.Url.short_code == updated_short_code.short_code).first()

    if same_short_code:
        raise HTTPException(status_code=status.HTTP_306_RESERVED, detail="Short code not available")
    
    url_query.update(updated_short_code.model_dump(), synchronize_session = False)
    db.commit()

    short_url = str(request.base_url) +'/'+ url.short_code

    return {
        'id': url.id,
        'original': url.original,
        'short_code': url.short_code,
        'clicks': url.clicks,
        'created_at': url.created_at,
        'short_url': short_url
    }
    
@router.delete('/{id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_url(id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    url_query = db.query(models.Url).filter(models.Url.id == id)
    url = url_query.first()

    if not url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Url doesn't exist")
    
    if url.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to perform this action")
    
    url_query.delete(synchronize_session=False)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/analytics/{url_id}", response_model=schemas.Analytics)
def get_analytics(url_id: int, 
                  request: Request,
                  db: Session = Depends(database.get_db), 
                  current_user: models.User = Depends(oauth2.get_current_user)):
    
    url = db.query(models.Url).filter(models.Url.id == url_id, models.Url.owner_id == current_user.id).first()

    if not url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Url not found")
    
    clicks = db.query(models.Click).filter(models.Click.url_id == url_id).all()
    short_url = str(request.base_url) +'/'+ url.short_code

    return {
        'url_id': url_id,
        'original': url.original,
        'short_url': short_url,
        'total_clicks': url.clicks,
        'click_details': clicks
    }
