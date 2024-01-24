import requests

response = requests.get('https://google.com')
response.raise_for_status()  # Ensure there were no errors
print(response)
# The rest of your code here