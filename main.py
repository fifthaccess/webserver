from fastapi import FastAPI, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import Cookie
from gitlab import gitlab
 
import json
import uvicorn
import requests

from app_secrets import my_secret

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


gitlab_dict = {
    "client_id": "272bc9be7187170fc76cebf13f8c69e7d9f66113632b3f53a664e98c3ac31a1e",
    "client_secret": my_secret["secret"],
    "redirect_uri": "http://appserver-fa.westeurope.cloudapp.azure.com:8080/auth/gitlab",
    "response_type": "code",
    "state": "STATE",
    "scope": "api",
    "grant_type": "authorization_code",
}


async def debugRequest (request:Request):  
    print(request.url)
    print(request.headers)
    print(await request.body())
    print(request.cookies)
    

def getLoginUrl():
    url = f"https://gitserver.westeurope.cloudapp.azure.com/oauth/authorize?client_id={gitlab_dict['client_id']}&redirect_uri={gitlab_dict['redirect_uri']}&response_type={gitlab_dict['response_type']}&state={gitlab_dict['state']}&scope={gitlab_dict['scope']}"
    return url


@app.get("/login/gitlab")
async def login_google():
    url = getLoginUrl()
    return RedirectResponse(url=url)


@app.get("/auth/gitlab")
async def auth_google(request: Request):
    code = request.query_params.get("code")
    token_url = f"https://gitserver.westeurope.cloudapp.azure.com/oauth/token?client_id={gitlab_dict['client_id']}&client_secret={gitlab_dict['client_secret']}&code={code}&grant_type={gitlab_dict['grant_type']}&redirect_uri={gitlab_dict['redirect_uri']}"
    response2 = requests.post(token_url)
    await response2
    access_token = json.loads(response2.content.decode("utf-8"))["access_token"]

    # user_info = requests.get(
    #    "https://gitserver.westeurope.cloudapp.azure.com/api/v4/user",
    #    headers={"Authorization": f"Bearer {access_token}"},
    # )
    
    tempRes = templates.TemplateResponse(request=request, name="index.j2")
    tempRes.set_cookie(key="token", value=access_token)
    return tempRes
    


@app.get("/")
async def index(request: Request, token=Cookie(default=None)):

    if token:
        return templates.TemplateResponse(request=request, name="index.j2")
    else:
        url = getLoginUrl()
        return RedirectResponse(url=url)


def outh(token):
    gl = gitlab.Gitlab(
        "https://gitserver.westeurope.cloudapp.azure.com", oauth_token=token
    )
    gl.auth()

    projects = gl.projects.list(get_all=True)
    print(projects)
    return projects


if __name__ == "__main__":
    uvicorn.run(app, port=8080, host="0.0.0.0")
