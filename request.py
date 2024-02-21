# import requests

# response = requests.get('https://gitserver.westeurope.cloudapp.azure.com/oauth/authorize?client_id=272bc9be7187170fc76cebf13f8c69e7d9f66113632b3f53a664e98c3ac31a1e&redirect_uri=http://appserver-fa.westeurope.cloudapp.azure.com/&response_type=code&state=STATE&scope=api', allow_redirects=True)
# #response.raise_for_status()  # Ensure there were no errors
# print(response.url)
# print(response.history)

# print(response.text)
# # The rest of your code here


# r = requests.get('https://youtu.be/dQw4w9WgXcQ') 
# print(r.url)

import requests

# Send a GET request to the initial URL
initial_url = "https://gitserver.westeurope.cloudapp.azure.com/oauth/authorize?client_id=272bc9be7187170fc76cebf13f8c69e7d9f66113632b3f53a664e98c3ac31a1e&redirect_uri=http://appserver-fa.westeurope.cloudapp.azure.com:8080/redirect/&response_type=code&state=STATE&scope=api"
response = requests.get(initial_url, allow_redirects=False)

# Check if the request was successful
if response.status_code == 301 or response.status_code == 302:
    # Get the final URL from the 'Location' header
    final_url = response.headers['Location']
    print("Final URL:", final_url)
elif response.ok:
    # If there were no redirects, use the original URL
    final_url = initial_url
    print("Final URL:", final_url)
else:
    print("Failed to fetch the URL:", initial_url)
