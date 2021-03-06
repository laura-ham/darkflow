import cv2, sched, time, ApiClient, sys, configparser, datetime
from darkflow.net.build import TFNet

counter = 1
def buildLog( i ):
    global counter
    counter += 1
    print(str(counter).zfill(7)  + " | " + str(datetime.datetime.now().time()) + " | " + i) 

arguments = sys.argv[1:]
if (len(arguments) == 0):
	buildLog("ERROR: Add one argument with the version name of the config")
	sys.exit()
elif (len(arguments) == 1):	
	version = arguments[0]
else:
	buildLog("ERROR: Too many arguments given.")
	sys.exit()

config = configparser.ConfigParser()
config.read('weaviate_config.ini')

#define weaviate api key and ip adress where weaviate is running, and connect to api client class
api_token = config[version]['api_token']
ip_address = config[version]['ip_address']
locationUrl = config[version]['locationUrl']
api = ApiClient.ApiClient(api_token, ip_address)

cap = cv2.VideoCapture(1)
s = sched.scheduler(time.time, time.sleep)
counter = 0

def cref(uuid):
	cref_schema = {}
	cref_schema["locationUrl"] = locationUrl
	cref_schema["type"] = "Thing"
	cref_schema["$cref"] = uuid
	return cref_schema

def get_key(property_name, property_value, class_name):
	#query with GraphQL if thing already exists in weaviate
	
	#schema in things left out, only uuid needed
	
	body = {"query": "{listThings(schema:\"" + property_name + ":" + str(property_value) + "\", class:\"" + class_name + "\") {things{uuid}}}"}
	result = api.post_graphql(body)
	if result is not None: #if uuid found, return uuid
		return result
	else: #make new thing and return uuid
		return False

def post_thing(thing):
	body = {}	
	body["@context"] = "http://dbpedia.org"
	body["@class"] = "Thing"
	schema = {}
	schema["name"] = thing["name"]
	schema["size"] = thing["size"]
	schema["location"] = room_cref
	body["schema"] = schema
	result = api.post_thing(body)

def patch_thing(uuid, thing):
	body = {}
	body["op"] = "replace"
	body["path"] = "/schema/size"
	body["value"] = thing["size"]
	result = api.patch_thing(uuid, [body])

def get_things_in_room():
	body = {"query": "{ listThings(class:\"Thing\") { things { uuid schema { name location {schema {roomCode}}} } } }"}
	result = api.post_graphql_get_all(body)
	weaviate_things = []
	for thing in result:
		location = thing["schema"]["location"]["schema"]["roomCode"]
		if location == 'DEA 01.001':
			thing_props = {"uuid": thing["uuid"], "name": thing["schema"]["name"]}
			weaviate_things.append(thing_props)
	return weaviate_things

def import_things_weaviate(things):
	#get all things in weaviate room
	weaviate_things = get_things_in_room()
	weaviate_thing_list = []
	for thing in weaviate_things:
		if (thing["name"] == "Light 1 DEA 01.001") or (thing["name"] == "Light 2 DEA 01.001") or (thing["name"] == "Light 3 DEA 01.001") or (thing["name"] == "Smartphone"):
			continue
		weaviate_thing_list.append(thing)
	room_objects = things
	
	#update already existing things in room
	for weaviate_thing in weaviate_things:
		for object in room_objects:
			if weaviate_thing["name"] == object["name"]:
				#patch thing in weaviate
				patch_thing(weaviate_thing["uuid"], object)
				room_objects.remove(object)
				weaviate_thing_list.remove(weaviate_thing)
				break

	#delete thing from room if not recognized on picture
	for weaviate_thing in weaviate_thing_list:
		#delete thing from room
		api.delete_thing(weaviate_thing["uuid"])

	#add new thing to weaviate if recognized on picture but not already in weaviate
	for object in room_objects:
		#post thing
		post_thing(object)


def check_objects(objects):
	things = []
	check_labels = open('check_labels.txt').read()
	for object in objects:
		if object["name"] in check_labels:
			things.append(object)
	print(things)
	return things

def get_objects(img):
	results = tfnet.return_predict(img)
	objects = []
	for result in results:
		if result['confidence'] >= 0.5:
			x = result['bottomright']['x'] - result['topleft']['x']
			y = result['bottomright']['y'] - result['topleft']['y']
			object = {}
			object["name"] = result["label"]
			object["size"] = x*y
			objects.append(object)
	return objects

def take_picture():
	ret, frame = cap.read()
	#filename = 'testcapture' + str(counter) + '.jpg'
	#cv2.imwrite(filename, frame)
	return frame

def get_picture(): 
	global counter
	s.enter(5, 1, get_picture, ())
	picture = take_picture()
	objects = get_objects(picture)
	things = check_objects(objects)
	import_things_weaviate(things)
	counter += 1

def start_taking_pics():
	get_picture()
	s.run()

def load_model():
	options = {"model": "cfg/yolo.cfg", "load": "bin/yolo.weights", "threshold": 0.1}
	tfnet = TFNet(options)
	return tfnet

room_uuid = get_key("roomCode", "DEA 01.001", "Room")
room_cref = cref(room_uuid)

tfnet = load_model()
start_taking_pics()
cap.release()
cv2.destroyAllWindows()