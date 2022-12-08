

from flask import Flask

from Route import Route


def main():
	app = Flask("GitRepoCreator")
	routes: list[Route] = [
		Route(app, "/"),
		Route(app, "/users"),
		Route(app, "/users/<string:username>"),
		Route(app, "/users/<string:username>/add", "POST"),
	]
	[route.add_to_server() for route in routes]

	app.run(host="0.0.0.0", port=80);


if __name__ == '__main__':
	main()
