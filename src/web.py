import cherrypy
import json
import os
from cherrypy.lib.static import serve_file
import logging

WEB_PORT = 5800

log = logging.getLogger('WebService')

class Root:
    @cherrypy.expose
    def index(self, name="/"):
        if name == "/":
            raise cherrypy.HTTPRedirect("/index.html")

        print ("NAME IS %s" % name )
        return serve_file(os.path.join(static_dir, name))

@cherrypy.expose
class VisionSettingsService(object):

    def __init__(self,vision_settings):
        self.vision_settings = vision_settings

    @cherrypy.tools.accept(media='application/json')
    @cherrypy.tools.json_out()
    def GET(self):
        return self.vision_settings.__dict__

    @cherrypy.tools.accept(media='application/json')
    @cherrypy.tools.json_in()
    def POST(self,**kwargs):
        log.info("Update Settings: %s", str(cherrypy.request.json))
        log.info("Update Params: %s" , str(kwargs))
        self.vision_settings.update_from_dict(cherrypy.request.json)

        if 'perm' in kwargs.keys():
            if kwargs['perm']:
                log.warn("Saving Defaults...")
                self.vision_settings.save_defaults()

        #self.vision_settings.__dict__.update( cherrypy.request.json )


@cherrypy.expose
class VisionDataService(object):

    def __init__(self,vision_data):
        self.vision_data = vision_data

    @cherrypy.tools.accept(media='application/json')
    @cherrypy.tools.json_out()
    def GET(self):
        return self.vision_data.__dict__




SERVER_CONF = {
    'server.socket_port': WEB_PORT,
    'server.socket_host': '0.0.0.0'
}
#wow, seems like there's a better way to do this!
static_dir = os.path.abspath( 
     os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)),"../static/"))

print ("Static Dir= %s" % static_dir)
ROOT_CONF = {
    '/': {  # Root folder.
        'tools.staticdir.on':   True,  # Enable or disable this rule.
        'tools.staticdir.root': static_dir,
        'tools.staticdir.dir':  '' 
    }      
}
SETTINGS_CONF = {
    '/': {  
        'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
        'tools.response_headers.on': True,
        'tools.response_headers.headers': [ ('Content-Type','application/json')]        
    }
}
DATA_CONF =  {
    '/': {  # Root folder.
        'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
        'tools.response_headers.on': True,
        'tools.response_headers.headers': [ ('Content-Type','application/json')]        
    }          
}


def stop_server():
    cherrypy.engine.stop()

def start_server( vision_settings, vision_data):
    cherrypy.config.update(SERVER_CONF)

    cherrypy.tree.mount(Root(),'/',ROOT_CONF)
    cherrypy.tree.mount(VisionSettingsService(vision_settings),'/settings', SETTINGS_CONF)
    cherrypy.tree.mount(VisionDataService(vision_data),'/data', DATA_CONF)
    cherrypy.engine.start()

if __name__ == '__main__':
    from data import VisionData,VisionSettings
    start_server(VisionSettings(),VisionData())
    cherrypy.engine.block()
