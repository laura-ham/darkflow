import json, requests

class ApiClient:
	def __init__(self, api_token, ip_adres):
		self.api_token = api_token
		self.ip_adres = ip_adres
		self.default_url = 'http://' + self.ip_adres + ':8070//weaviate/v1'
		self.headers = {'X-API-KEY': self.api_token, 'Content-Type': 'application/json', 'Accept': 'application/json'}
	
	#post a new thing and return the uuid
	def post_thing(self, body):
		url = self.default_url + '/things'
		response = requests.post(url, headers=self.headers, json=body)
		if response.status_code == 202:
			result = json.loads(response.content.decode('utf-8'))
			thingId = result["thingId"]
			return thingId
		elif response.status_code == 422:
			print("post thing failed body doesn't match with schema", body)
		else:
			print(response.status_code, response.reason)
	
	#post a graphql query with a property of a class and return the class' uuid
	def post_graphql(self, body):
		url = self.default_url + '/graphql'
		response = requests.post(url, headers=self.headers, json=body)
		if response.status_code == 200:
			result = json.loads(response.content.decode('utf-8'))
			if result["data"]["listThings"]["things"]:
				return result["data"]["listThings"]["things"][0]["uuid"] #return uuid of first thing in result
			else:
				#print("graphql 1: ", response.reason)
				return None
		else:
			print("graphql 2: " + str(response.status_code) + ": " + response.reason)
			return str(response.status_code) + ": " + response.reason

	#post a graphql query with a property of a class and return all things
	def post_graphql_get_all(self, body):
		url = self.default_url + '/graphql'
		response = requests.post(url, headers=self.headers, json=body)
		if response.status_code == 200:
			result = json.loads(response.content.decode('utf-8'))
			if len(result["data"]["listThings"]["things"]) > 0:
				return result["data"]["listThings"]["things"] #return uuid of first thing in result
			else:
				return []
		else:
			print("graphql 2: " + str(response.status_code) + ": " + response.reason)
			return str(response.status_code) + ": " + response.reason
	
	#post a graphql query and return the whole json response
	def get_graphql_json(self, body):
		url = self.default_url + '/graphql'
		response = requests.post(url, headers=self.headers, json=body)
		return json.loads(response.content.decode('utf-8'))

	def delete_thing(self, thingId):
		url = self.default_url + '/things/' + thingId
		response = requests.delete(url, headers=self.headers)
		if response.status_code == 204:
			return True
		else: 
			print("delete thing failed, error code: " + str(response.status_code) + response.reason)
			return False

	def delete_all_things(self):
		url = self.default_url + '/things'
		response = requests.get(url, headers=self.headers)
		all_things = json.loads(response.content.decode('utf-8'))
		for thing in all_things["things"]:
			#if thing["@class"] == "Artwork":
			thingId = thing["thingId"]
			thing_url = self.default_url + '/things/' + thingId
			thing_response = requests.delete(thing_url, headers=self.headers)
			print(thing_url,thing_response.status_code)
		return

	def patch_thing(self, thingId, body):
		url = self.default_url + '/things/' + thingId
		response = requests.patch(url, headers=self.headers, json=body)
		if response.status_code == 200:
			return True
		else: 
			print("patch thing error: ", response.status_code, ": ", response.reason, body)
			return False