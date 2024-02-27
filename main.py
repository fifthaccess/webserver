from fastapi import FastAPI, Request, Response , Depends
from fastapi.responses import RedirectResponse ,HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import Cookie
from gitlab import gitlab
 
import json
import uvicorn
import requests

from app_secrets import my_secret

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")



gitlab_dict = {
    "client_id": "272bc9be7187170fc76cebf13f8c69e7d9f66113632b3f53a664e98c3ac31a1e",
    "client_secret": my_secret["secret"],
    "redirect_uri": "http://appserver-fa.westeurope.cloudapp.azure.com:8080/auth/gitlab",
    "response_type": "code",
    "state": "STATE",
    "scope": "api",
    "grant_type": "authorization_code",
    "tokenLifeTime": 900 # 15 in Sekunden
}

class RequiresLoginException(Exception):
    pass

#____________________________________________________________________________________get Functions_____________________________________________________________________________________________________________________________________________________________________________________
def getLoginUrl():
    url = f"https://gitserver.westeurope.cloudapp.azure.com/oauth/authorize?client_id={gitlab_dict['client_id']}&redirect_uri={gitlab_dict['redirect_uri']}&response_type={gitlab_dict['response_type']}&state={gitlab_dict['state']}&scope={gitlab_dict['scope']}"
    return url

def getToken(request: Request): 
    token = request.cookies.get("token")
    if token:
        return token 
    else:
        raise RequiresLoginException
        #RedirectResponse(url=url)

def getProjects(token):
    gl = gitlab.Gitlab(
        "https://gitserver.westeurope.cloudapp.azure.com", oauth_token=token
    )
    gl.auth()
    user = gl.users.list(search='benedikt.erkner-sach')
    print(user)
    projects = gl.projects.list(get_all=True)
    print(projects)
    return projects

def getProfile(token):
    user_info = requests.get("https://gitserver.westeurope.cloudapp.azure.com/api/v4/user", headers={"Authorization": f"Bearer {token}"})
    return json.loads(user_info.content.decode("utf-8"))

    #raise HTTPException(status_code=400, detail="Incorrect Account")
    # gitignore = gl.gitignores.get('Python') für gitignore
    #print(gitignore.content)

#____________________________________________________________________________________App Exeptions Handler_____________________________________________________________________________________________________________________________________________________________________________________


@app.exception_handler(RequiresLoginException)
async def exception_handler(request: Request, exc: RequiresLoginException) -> Response:
    url = getLoginUrl()
    return RedirectResponse(url=url)

#____________________________________________________________________________________App Routs_____________________________________________________________________________________________________________________________________________________________________________________




@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    
        return templates.TemplateResponse(request=request, name="index.j2")


@app.get("/my_profile")
async def MyProfile(request: Request,token: str = Depends(getToken)):
        Profile = getProfile(token=token)
        print(Profile)
        return templates.TemplateResponse(request=request, name="myprofil.j2",context={"token": token,"user": Profile})

@app.get("/login/gitlab")
async def login_gitlab():
    url = getLoginUrl()
    return RedirectResponse(url=url)


@app.get("/auth/gitlab")
async def auth_gitlab(request: Request):
    code = request.query_params.get("code")
    token_url = f"https://gitserver.westeurope.cloudapp.azure.com/oauth/token?client_id={gitlab_dict['client_id']}&client_secret={gitlab_dict['client_secret']}&code={code}&grant_type={gitlab_dict['grant_type']}&redirect_uri={gitlab_dict['redirect_uri']}"
    response2 = requests.post(token_url)
    token = json.loads(response2.content.decode("utf-8"))["access_token"]

    # tempRes = templates.TemplateResponse(request=request, name="Projekts.j2",context={"token": token})
    # tempRes.set_cookie(key="token", value=token, expires=120)
    RedRes = RedirectResponse(url="/projects")
    RedRes.set_cookie(key="token", value=token, expires=gitlab_dict["tokenLifeTime"])
   
    return  RedRes  


@app.get("/projects")
async def index(request: Request, token: str = Depends(getToken)):  # token=Cookie(default=None)):

    projects = getProjects(token)
    return templates.TemplateResponse(request=request, name="Projekts.j2",context={"token": token,"projects": projects})





if __name__ == "__main__":
    uvicorn.run(app, port=8080, host="0.0.0.0")
