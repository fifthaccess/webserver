from fastapi import FastAPI , Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2AuthorizationCodeBearer

from starlette.middleware.sessions import SessionMiddleware 

from pydantic import BaseModel
from gitlab import gitlab
import json
import uvicorn
from app_secrets import my_secret
from jose import jwt 
import requests

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=my_secret["middleware_secret"])

link = "https://gitserver.westeurope.cloudapp.azure.com/oauth/authorize?client_id=272bc9be7187170fc76cebf13f8c69e7d9f66113632b3f53a664e98c3ac31a1e&redirect_uri=http://appserver-fa.westeurope.cloudapp.azure.com:8080/redirect/&response_type=code&state=STATE&scope=api"

templates = Jinja2Templates(directory= "templates")

app.mount("/static", StaticFiles(directory="static"), name="static")


# oauth2_scheme = OAuth2AuthorizationCodeBearer(tokenUrl="/request_token",
                                            #   authorizationUrl="/login/gitlab")


class user(BaseModel):
    username: str
    id: int
    state: str
    locked: str
    admin: bool
    web_url: str

gitlab_dict = {   
    "client_id" : "272bc9be7187170fc76cebf13f8c69e7d9f66113632b3f53a664e98c3ac31a1e",
    "client_secret" : my_secret["secret"],
    "redirect_uri" : "http://appserver-fa.westeurope.cloudapp.azure.com:8080/auth/gitlab",
    "response_type" : "code",
    "state" : "STATE",
    "scope" : "api",
    "grant_type" : "authorization_code"
    }


@app.middleware("http")
async def some_middleware(request: Request, call_next):
    response = await call_next(request)
    session = request.cookies.get('session')
    if session:
        response.set_cookie(key='session', value=request.cookies.get('session'), httponly=True)
    return response




@app.get("/login/gitlab")
async def login_google():
    url = f"https://gitserver.westeurope.cloudapp.azure.com/oauth/authorize?client_id={gitlab_dict['client_id']}&redirect_uri={gitlab_dict['redirect_uri']}&response_type={gitlab_dict['response_type']}&state={gitlab_dict['state']}&scope={gitlab_dict['scope']}"
    return RedirectResponse(url=url)

@app.get("/auth/gitlab")
async def auth_google(code: str, request : Request):
    token_url = f"https://gitserver.westeurope.cloudapp.azure.com/oauth/token?client_id={gitlab_dict['client_id']}&client_secret={gitlab_dict['client_secret']}&code={code}&grant_type={gitlab_dict['grant_type']}&redirect_uri={gitlab_dict['redirect_uri']}"
    response = requests.post(token_url)
    access_token = json.loads(response.content.decode('utf-8'))["access_token"]
    user_info = requests.get("https://gitserver.westeurope.cloudapp.azure.com/api/v4/user", headers={"Authorization": f"Bearer {access_token}"})
    request.session["access_token"] = access_token
    return {"now logged in"} #{"access_token": access_token, "token_type": "bearer"}

@app.get("/request_token")
async def check_user(request : Request):
    access_token = request.session["access_token"]
    #user_info = requests.get("https://gitserver.westeurope.cloudapp.azure.com/api/v4/user", headers={"Authorization": f"Bearer {access_token}"})
    #if (user_info["id"] == 4):
    return {"access_token": access_token, "token_type": "bearer"}
    #raise HTTPException(status_code=400, detail="Incorrect Account")


@app.get("/check_session")
async def check_session(request : Request):
    return{"token": request.session["access_token"]}


@app.get("/token")
async def get_token(token: str = Depends(check_user)):
    return {"it worked finally": token}    

def outh(token):
    gl = gitlab.Gitlab('https://gitserver.westeurope.cloudapp.azure.com', oauth_token=token)
    gl.auth()

    projects = gl.projects.list(get_all=True)
    print(projects)
    return projects

if __name__ == '__main__':
    uvicorn.run(app, port=8080, host='0.0.0.0')