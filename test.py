from gitlab import gitlab
gl = gitlab.Gitlab('https://gitserver.westeurope.cloudapp.azure.com', oauth_token='c7ddb765a43b2cf1f16c3bb845e1a8d95a3e77b3169e6b9fa51fa76d2d52d9e7')
gl.auth()

projects = gl.projects.list(get_all=True)
print(projects)