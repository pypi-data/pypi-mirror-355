from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from .. import schemas, database, models, utils, oauth2
from sqlalchemy.orm import Session

router = APIRouter(tags=['AUTHENTICATION'])

@router.post('/login', response_model=schemas.Token)
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == user_credentials.username).first()

    if not user or not utils.verify(user_credentials.password, user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")
    
    access_token, jti = oauth2.create_access_token(data={"user_id": user.id})
    return {'access_token': access_token, 
            'token_type': 'Bearer',
            'jti': jti}

# @router.post('/logout')
# def logout(data: list = Depends(oauth2.extract_jti_exp), db: Session = Depends(database.get_db)):
#     jti, exp = data
#     exp_datetime = datetime.utcfromtimestamp(exp)

#     blacklisted_token = models.TokenBlacklist(jti=jti, expires_at = exp_datetime)
#     db.add(blacklisted_token)
#     db.commit()

#     return {"msg": "successfully logged out"}

