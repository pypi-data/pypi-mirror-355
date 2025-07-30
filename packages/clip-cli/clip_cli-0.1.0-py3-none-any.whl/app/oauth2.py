from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status 
from jose import JWTError, jwt
from . import schemas, database, models
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .config import settings
import uuid

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

def create_access_token(data: dict):
    jti = str(uuid.uuid4())
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire,
                      "jti": jti})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, ALGORITHM)

    return encoded_jwt, jti

def verify_access_token(token: str ,credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, ALGORITHM)
        id: str = payload.get("user_id")
        jti = payload.get("jti")
        if not id or not jti:
            raise credentials_exception
        
        token_data = schemas.TokenData(id=id, jti=jti)

    except JWTError:
        raise credentials_exception
    
    return token_data

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                          detail="Could not validate credentials",
                                          headers={'WWW-Authenticate': "Bearer"})
    token = verify_access_token(token, credentials_exception)

    # blacklisted = db.query(models.TokenBlacklist).filter(models.TokenBlacklist.jti == token.jti).first()
    # if blacklisted:
    #     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")

    user = db.query(models.User).filter(models.User.id == token.id).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")
    return user

# def extract_jti_exp(token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, ALGORITHM)
#         jti = payload.get('jti')
#         exp = payload.get('exp')

#         if not jti or not exp:
#             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid Token')
        
#         return [jti, exp]
    
#     except JWTError:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")