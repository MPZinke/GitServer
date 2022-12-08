#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "MPZinke"

########################################################################################################################
#                                                                                                                      #
#   created by: MPZinke                                                                                                #
#   on 2022.12.08                                                                                                      #
#                                                                                                                      #
#   DESCRIPTION:                                                                                                       #
#   BUGS:                                                                                                              #
#   FUTURE:                                                                                                            #
#                                                                                                                      #
########################################################################################################################


from flask import Flask, request
import inspect
import os
import re
import types
from typing import List
from werkzeug.exceptions import Forbidden, Unauthorized


Module = types.ModuleType  # typedef types.ModuleType


class Route:
	PARAM_REGEX = r"<(int|string):([_a-zA-Z][_a-zA-Z0-9]*)>"
	PARAM_NAME_REGEX = r"<(?:int|string):([_a-zA-Z][_a-zA-Z0-9]*)>"

	def __init__(self, server: Flask, endpoint: str, *methods: List[str], root: Module=None, secure: bool=True):
		self._server: Flask = server
		if(root is None):
			import Root as root

		self._root: Module = root
		self._endpoint: str = endpoint
		self._methods: List[str] = ["GET"] if(not methods) else methods
		self._is_secure = secure
		self._callbacks = {method: self.callback_function(method) for method in self._methods}


	def __str__(self):
		callback_str = ",".join([f"{method}: {callback.__name__}" for method, callback in self._callbacks.items()])
		return f"{self._endpoint} {callback_str}"


	def add_to_server(self) -> None:
		"""
		SUMMARY: Adds the route to the Flask server.
		DETAILS: Creates a function that calls the required function (based on method) and sets it to the endpoint.
		NOTES: Instead of @app.route decorator, adds a route to the server.
		FROM:  https://stackoverflow.com/a/40466535
		"""
		def endpoint_function(*args: list, **kwargs: dict):  # smart_curtain instead of self
			"""
			SUMMARY: Checks auth & calls function for request method.
			PARAMS:  Takes the args & kwargs claimed.
			DETAILS: Checks the authentication & authorizaton. Makes a call to the correct method function.
			RETURNS: The value(s) returned from calling the correct method function.
			"""
			# if(self._is_secure and "Authorization" not in request.headers):
			# 	raise Unauthorized()

			# elif(self._is_secure and self.unauthorized()):
			# 	raise Forbidden()

			return self._callbacks[request.method](*args, **kwargs)

		self._server.add_url_rule(self._endpoint, self._endpoint, endpoint_function, methods=self._methods)
		# Adds the url with a trailing slash
		if(len(self._endpoint) > 1 and self._endpoint[-1] == '/'):
			slashed_endpoint = f"{self._endpoint}/"
			self._server.add_url_rule(slashed_endpoint, slashed_endpoint, endpoint_function, methods=self._methods)


	def unauthorized(self) -> bool:
		"""
		SUMMARY: Checks the authorizaton of the requestor.
		RETURNS: Whether the requestor has the correct bearer token or is a curtain (via IP).
		THROWS:  [Execution] Unauthorized exception if not authorized.
		"""
		AUTHORIZED, UNAUTHORIZED = False, True

		# token: str = os.getenv("SMARTCURTAIN_BACKEND_API_KEY")
		# if(request.headers.get("Authorization") == f"Bearer {token}"):
		# 	return AUTHORIZED

		# if(self._SmartCurtain.Curtain(ip_address=request.remote_addr) is None):
		# 	return UNAUTHORIZED

		return AUTHORIZED


	def callback_function(self, method: str) -> str:
		"""
		SUMMARY: Determines the callback function for the request method.
		"""
		module_path_parts: list[str] = [part.replace('.', '_') for part in self.path_parts()]
		callback_module: Module = self.__module(self._root, module_path_parts)
		return self.__modules_method_function(method, callback_module)


	def __module(self, current_module: Module, path_parts: list[str]):
		"""
		SUMMARY: Gets the module down the path of the endpoint.
		DETAILS: Recursively descends module to find the bottom most module (if exists).
		RETURNS: The module allegedly containing the method for the endpoint.
		THROWS:  [Start] Exception if module not found
		"""
		if(len(path) == 0):
			return current_module

		if(not hasattr(current_module, path[0])):
			raise Exception(f"Module not found: {path[0]}")

		return self.__module(getattr(current_module, path[0]), path[1:])


	def __modules_method_function(self, method: str, module: Module) -> bool:
		"""
		SUMMARY: Gets the desired callback for the endpoint based on name, params, and module.
		"""
		callback_params = {param[1]: param[0] for param in re.findall(self.PARAM_REGEX, self._endpoint)}

		# Check through functions to see if names & params match.
		module_function_tuples = [method for method in inspect.getmembers(module) if(inspect.isfunction(method[1]))]
		for function_name, function in module_function_tuples:
			# Check if function name or param-len do not match
			function_params: dict = function.__annotations__
			if(function_name != method or len(callback_params) != len(function_params)):
				continue

			# Check if function params match
			mapping = {"int": int, "string": str}
			if(all(mapping.get(type, type) == function_params[name] for name, type in callback_params.items())):
				return function

		callback_param_str: str = ", ".join(callback_params.keys())
		raise Exception(f"No matching function for method '{method}' with params: '{callback_param_str}'" +
		  f" for module '{module.__name__}'")


	def path_parts(self) -> List[str]:
		"""
		SUMMARY: Gets the rescinding parts to a path starting at the root directory.
		"""
		def is_param(part: str) -> bool:
			return re.fullmatch(self.PARAM_REGEX, part)

		if(self._endpoint == "/"):
			return []

		parts = os.path.normpath(self._endpoint).split(os.sep)
		# Strip the type from the parameters
		# [param name if(part is param) else part for part in parts]
		parts = [re.findall(self.PARAM_NAME_REGEX, part)[0] if(is_param(part)) else part for part in parts]
		return parts[int(self._endpoint[0] == '/'):]  # ignore empty '' if path starts with '/'
