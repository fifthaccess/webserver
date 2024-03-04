from fastapi import FastAPI, Request, Response , Depends
from fastapi.responses import RedirectResponse ,HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import Cookie
from gitlab import gitlab

import time
import random
import json
import uvicorn
import requests

from app_secrets import my_secret

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

sessions = {}


gitlab_dict = {
    "gitlab_server_url": "https://gitserver.westeurope.cloudapp.azure.com",
    "client_id": "272bc9be7187170fc76cebf13f8c69e7d9f66113632b3f53a664e98c3ac31a1e",
    "client_secret": my_secret["secret"],
    "redirect_uri": "http://appserver-fa.westeurope.cloudapp.azure.com:8080/auth/gitlab",
    "response_type": "code",
    "state": "STATE",
    "scope": "api",
    "grant_type": "authorization_code",
    "SessionLifeTime": 21600 # 6 Stunden 
}

class RequiresLoginException(Exception):
    pass



#____________________________________________________________________________________get Functions_____________________________________________________________________________________________________________________________________________________________________________________
def getLoginUrl():
    url = f"{gitlab_dict['gitlab_server_url']}/oauth/authorize?client_id={gitlab_dict['client_id']}&redirect_uri={gitlab_dict['redirect_uri']}&response_type={gitlab_dict['response_type']}&state={gitlab_dict['state']}&scope={gitlab_dict['scope']}"
    return url

def getToken(request: Request): 
    session_id = request.cookies.get("session_id")

    try:
        token = sessions[int(session_id)]["access_token"]
        token_creation_time = sessions[int(session_id)]["token_created_at"]
        token_lifetime = sessions[int(session_id)]["token_lifetime"]
        session_creation_time = sessions[int(session_id)]["session_created_at"]
        session_lifetime = gitlab_dict["SessionLifeTime"]
        
    except:
        print("an error has happend")
        pass
        raise RequiresLoginException

    if (time.time() - session_creation_time) > session_lifetime:
         sessions.pop(int(session_id))
         raise RequiresLoginException
    if (time.time() - token_creation_time) < token_lifetime :
        return token
    else:
        return get_refresh_token(request= request)
         
       


def get_refresh_token(request: Request):
    session_id = int(request.cookies.get("session_id"))
    refresh_token = sessions[session_id]["refresh_token"]

    refresh_url = f"{gitlab_dict['gitlab_server_url']}/oauth/token?client_id={gitlab_dict['client_id']}&client_secret={gitlab_dict['client_secret']}&refresh_token={refresh_token}&grant_type=refresh_token&redirect_uri={gitlab_dict['redirect_uri']}"
    response2 = requests.post(refresh_url)
    token = json.loads(response2.content.decode("utf-8"))

    sessions[session_id]["access_token"] = token["access_token"]
    sessions[session_id]["refresh_token"] = token["refresh_token"]
    sessions[session_id]["token_created_at"] = token["created_at"]
    sessions[session_id]["token_lifetime"] = token["expires_in"]
    print("got an refresh")
    return token["access_token"]

def getProjects(token):
    gl = gitlab.Gitlab(
        gitlab_dict["gitlab_server_url"], oauth_token=token
    )
    gl.auth()
    user = gl.users.list(search='benedikt.erkner-sach')
    print(user)
    projects = gl.projects.list(get_all=True)
    print(projects)
    project = gl.projects.get(2)
    storage = project.storage.get()
    print(storage)
    return projects


def getProfile(token):
    user_info = requests.get(f"{gitlab_dict['gitlab_server_url']}/api/v4/user", headers={"Authorization": f"Bearer {token}"})
    return json.loads(user_info.content.decode("utf-8"))

    #raise HTTPException(status_code=400, detail="Incorrect Account")
    # gitignore = gl.gitignores.get('Python') für gitignore
    #print(gitignore.content)


def create_session(token):
    session_id = len(sessions) + random.randint(0, 1000000)
    user = getProfile(token=token["access_token"])
    session = {
        "user" : user,
        "access_token" : token["access_token"],
        "refresh_token" : token["refresh_token"],
        "token_created_at" : token["created_at"],
        "token_lifetime" : token["expires_in"],
        "session_created_at" : time.time()
        }
    
    sessions[session_id] = session #finished dict
    return session_id

def create_groups(token, groups):
    gl = gitlab.Gitlab(
        gitlab_dict["gitlab_server_url"], oauth_token=token
    )
    existing_group = gl.groups.list(search=groups["name"])
    print(existing_group[0].name)
    print()
    existing = False
    for ex_groups in existing_group:
        if ex_groups.name == groups["name"]:
            existing = True
        

    # try: 
    if existing == False:
        group = gl.groups.create({'name': groups["name"], 'path': groups["name"]})
        print(group.get_id())
    #subgroup = gl.groups.create({'name': 'subgroup1', 'path': 'subgroup1', 'parent_id': group.get_id()})
        for name in groups["members"]:
            
            user = gl.users.list(search=name)
            subgroup = gl.groups.create({'name': name, 'path': name, 'parent_id': group.get_id()})
            print(user)
            member = subgroup.members.create({'user_id': user[0].id,
                                'access_level': gitlab.const.AccessLevel.OWNER})
            return "Groups created"
    else: 
        return "Groups already exist"

    # except:
    #     return "Groups"


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
    token_url = f"{gitlab_dict['gitlab_server_url']}/oauth/token?client_id={gitlab_dict['client_id']}&client_secret={gitlab_dict['client_secret']}&code={code}&grant_type={gitlab_dict['grant_type']}&redirect_uri={gitlab_dict['redirect_uri']}"
    response2 = requests.post(token_url)
    session_id = create_session(json.loads(response2.content.decode("utf-8")))
    #token = json.loads(response2.content.decode("utf-8"))["access_token"]


    RedRes = RedirectResponse(url="/projects")
    #RedRes = HTMLResponse("your loged in")
    RedRes.set_cookie(key="session_id", value=session_id)
   
    return  RedRes  


@app.get("/projects")
async def index(request: Request, token: str = Depends(getToken)):  # token=Cookie(default=None)):

    projects = getProjects(token)
    return templates.TemplateResponse(request=request, name="Projekts.j2",context={"token": token,"projects": projects})

@app.get("/group")
async def index(request: Request, token: str = Depends(getToken)):  # token=Cookie(default=None)):
    group = {
        "name" : "test",
        "members": ["benedikt.erkner-sach", "admin"]
    }
    result = create_groups(token=token, groups= group)
    return {result}



if __name__ == "__main__":
    uvicorn.run(app, port=8080, host="0.0.0.0")
