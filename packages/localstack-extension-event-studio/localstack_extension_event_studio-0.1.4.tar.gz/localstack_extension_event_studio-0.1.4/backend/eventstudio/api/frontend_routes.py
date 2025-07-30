from localstack.http import Request,Response,route
from eventstudio import static
class FrontendRoutes:
	@route('/')
	def index(request:Request,*A,**B):return Response.for_resource(static,'index.html')
	@route('/<path:path>')
	def serve_extension_frontend(self,request:Request,path:str,**A):
		if'..'in path:return Response('Not Found',status=404)
		return Response.for_resource(static,path)