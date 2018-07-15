# coding=utf-8
from __future__ import absolute_import

### (Don't forget to remove me)
# This is a basic skeleton for your plugin's __init__.py. You probably want to adjust the class name of your plugin
# as well as the plugin mixins it's subclassing from. This is really just a basic skeleton to get you started,
# defining your plugin as a template plugin, settings and asset plugin. Feel free to add or remove mixins
# as necessary.
#
# Take a look at the documentation on what other plugin mixins are available.

import octoprint.plugin
from datetime import datetime
from isodate import isodatetime
from isodate.isostrf import DATE_EXT_COMPLETE, TIME_EXT_COMPLETE, TZ_EXT
import flask
import os
import re
import StringIO
import time
import urllib2
import zipfile
import json
import inspect
from HTMLParser import HTMLParser
import shutil

class ThingUrlException(Exception):
  def __init(self,value):
    self.parameter=value
  def __str__(self):
    return repr(self.value)

class TestException(Exception):
  def __init(self,value):
    self.parameter=value
  def __str__(self):
    return repr(self.value)

class zipsaver:
  def __init__(self,zipfile,zippath,logger):
    self.zipfile = zipfile
    self.zippath = zippath
    self._logger = logger


  def save(self,path):
    self._logger.info('saving '+ path)
    with open(path,'wb') as target:
      with self.zipfile.open(self.zippath,'r') as source:
        shutil.copyfileobj(source,target)    
    self._logger.info('saved '+path)
      

  def __str__(self):
    m = re.search(r'[^\/\\]*$',self.zippath)
    return self.zippath[m.start():m.end()]

class thingiverseParser(HTMLParser):
  def __init__(self):
    HTMLParser.__init__(self)
    self.done = False
    self.error = False
    self.title = None
    self.description = None
    self.image = None
    self.tags = []

  def asDict(self):
   return {'title':self.title,'description':self.description,'image':self.image,'tags':self.tags}

  def attrs2dict(self,attrs):
    ret = {}
    for a in attrs:
      ret[a[0]] = a[1]
    return ret

  def handle_starttag(self,tag,attrs):
    attrs = self.attrs2dict(attrs)
    self.tags.append({'tag':tag,'attrs':attrs})
    if (tag == "meta" and "property" in attrs and "content" in attrs):
      if attrs["property"] == "og:title":
        self.title = attrs["content"]
      elif attrs["property"] == "og:description":
        self.description = attrs["content"]
      elif attrs["property"] == "og:image":
        self.image = attrs["content"]
      self.done = not (self.title is None or self.description is None or self.image is None)

  def handle_endtag(self,tag):
    if (tag == "head"):
      self.Error = True
      self.done = True

class ThingiversePlugin(
     octoprint.plugin.BlueprintPlugin
    ,octoprint.plugin.TemplatePlugin
    ,octoprint.plugin.AssetPlugin
):
  def __init__(self):
    self.thingiverseThingidRegex=".*thing:(?P<thingid>[0-9]+).*"
    self.thingiverseUrl="https://www.thingiverse.com/thing:{0:.0f}"
    self.thingNameRegex="<h1>(?P<tag>.*?)</h1>.*"

    ##~~ AssetPlugin mixin

  def get_assets(self):
    return {
      'html':['index.html'],
      'css':['js/thingiverse.css'],
      'js':['js/thingiverse.js',
      'js/thingiverse_sidebar.js']
    }
    ##~~ TemplatePlugin mixin

  def get_template_configa(self):
    return [{
        'type':'sidebar',
        'name':'Thingiverse Downloader'
    }]

  ##~~ BlueprintPlugin mixin

  def is_blueprint_protected(self):
    return False

  @octoprint.plugin.BlueprintPlugin.route("/download", methods=["POST","GET"]) 
  def thingiverseDownload(self):
    data = flask.request.json
    if flask.request.args.has_key('thingid'):
      data = {'thingid':flask.request.args['thingid']}
    if (data is None):
      return flask.make_response("Expected thingid")
    return flask.make_response(flask.jsonify(self.downloadThing(data['thingid'])))


  def downloadThing(self,thing):
    #try:
      url=self.thingUrl(thing)
      retrieved=isodatetime.datetime_isoformat(datetime.utcnow())
      response=urllib2.urlopen(urllib2.Request(url, headers={'User-Agent' : "Octoprint Loader"}))
      parser = thingiverseParser();
      while True:
        respdata = response.readline()
        if (respdata == "" or parser.done):
          break
        parser.feed(respdata)
      response.close()
      response=urllib2.urlopen(urllib2.Request(url+"/zip", headers={'User-Agent' : "Octoprint Loader"}))
      zip = zipfile.ZipFile(StringIO.StringIO(response.read()),'r')
      storage = self._file_manager._storage_managers['local']
      folder = storage.add_folder(parser.title,True)
      files = [ zipsaver(zip, f ,self._logger) for f in zip.namelist() if f.endswith(".stl")]
      paths = []
      for f in files:
        path = storage.add_file(storage.join_path(folder,str(f)),f,links=[{'rel':'web','data':{'href':url,'retrieved':str(retrieved)}}],allow_overwrite=True)
        paths.append(path)
        storage.set_additional_metadata(path,"description",parser.description)
        storage.set_additional_metadata(path,"title",parser.title)
        
      return {'data':[{'filename':str(f),'folder':folder
,'path':storage.join_path(folder,str(f))
,'retrieved':retrieved} for f in 
#zip.namelist()]}
files]}
    #except Exception as ex:
      #return "{0}".format(ex)
      #pass

  def thingUrl(self,thingstring):
    thingid=0
    try:
      thingid=int(thingstring)
    except ValueError:
      pass
    if thingid==0:
      try:
        thingid=int(re.search(self.thingiverseThingidRegex,thingstring).group('thingid'))
      except (AttributeError, ValueError) as ex:
        raise ThingUrlException(str(thingstring) + " could not be converted to a thingiverse thing url"+ str(ex))
    return self.thingiverseUrl.format(thingid)
        
            
  ##~~ Softwareupdate hook

  def get_update_information(self):
    # Define the configuration for your plugin to use with the Software Update
    # Plugin here. See https://github.com/foosel/OctoPrint/wiki/Plugin:-Software-Update
    # for details.
    return dict(
      thingiverse=dict(
        displayName="Thingiverse Plugin",
        displayVersion=self._plugin_version,

        # version check: github repository
        type="github_release",
        user="ian2000611",
        repo="thingiverseDownloader",
        current=self._plugin_version,

        # update method: pip
        pip="https://github.com/ian2000611/thingiverseDownloader/archive/{target_version}.zip"
      )
    )


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Thingiverse Plugin"

def __plugin_load__():
  global __plugin_implementation__
  __plugin_implementation__ = ThingiversePlugin()

  global __plugin_hooks__
  __plugin_hooks__ = {
    "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
  }

