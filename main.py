from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn
from app_secrets import my_secret
import requests
app = FastAPI()


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
    requests.post(f"https://gitserver.westeurope.cloudapp.azure.com/oauth/token?client_id=272bc9be7187170fc76cebf13f8c69e7d9f66113632b3f53a664e98c3ac31a1e&client_secret={my_secret['secret']}&code={code}&grant_type=authorization_code&redirect_uri=http://appserver-fa.westeurope.cloudapp.azure.com:8080/end/")
    return {"Code": code}

@app.get("/end/")
async def the_end():
    return {"the_End"}

if __name__ == '__main__':
    uvicorn.run(app, port=8080, host='0.0.0.0')