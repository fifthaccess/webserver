from fastapi import FastAPI , Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from gitlab import gitlab
import json
import uvicorn
from app_secrets import my_secret
import requests
app = FastAPI()
link = "https://gitserver.westeurope.cloudapp.azure.com/oauth/authorize?client_id=272bc9be7187170fc76cebf13f8c69e7d9f66113632b3f53a664e98c3ac31a1e&redirect_uri=http://appserver-fa.westeurope.cloudapp.azure.com:8080/redirect/&response_type=code&state=STATE&scope=api"

templates = Jinja2Templates(directory= "templates")

app.mount("/static", StaticFiles(directory="static"), name="static")

def outh(token):
    gl = gitlab.Gitlab('https://gitserver.westeurope.cloudapp.azure.com', oauth_token=token)
    gl.auth()

    projects = gl.projects.list(get_all=True)
    print(projects)
    return projects

@app.get("/items/", response_class=HTMLResponse)
async def read_items():
    return """
    <html>
        <head>
            <title>Some HTML in here</title>
        </head>
        <body>
            <h1>Look ma! HTML!</h1>
        </body>
    </html>
    """

#https://gitserver.westeurope.cloudapp.azure.com/oauth/token?client_id=272bc9be7187170fc76cebf13f8c69e7d9f66113632b3f53a664e98c3ac31a1e&client_secret=my_secret["secret"]&code={code}&grant_type=authorization_code&redirect_uri=http://appserver-fa.westeurope.cloudapp.azure.com:8080/end/

@app.get("/redirect/")
async def redirect(code):
    my_secret["secret"]
    res =  requests.post(f"https://gitserver.westeurope.cloudapp.azure.com/oauth/token?client_id=272bc9be7187170fc76cebf13f8c69e7d9f66113632b3f53a664e98c3ac31a1e&client_secret={my_secret['secret']}&code={code}&grant_type=authorization_code&redirect_uri=http://appserver-fa.westeurope.cloudapp.azure.com:8080/redirect/")
    token = json.loads(res.content.decode('utf-8'))["access_token"]
    projects = outh(token=token)
    projects = projects[0].name
    return {"Code": code, "response": token , "projects": projects}

@app.get("/end/")
async def the_end():
    return {"the_End"}


@app.get("/", response_class=HTMLResponse)
async def jinja(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.j2", context={"mylink": link}
    )




if __name__ == '__main__':
    uvicorn.run(app, port=8080, host='0.0.0.0')