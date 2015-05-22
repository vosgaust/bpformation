# -*- coding: utf-8 -*-
"""
Manage Blueprints.
"""

import os
import re
import sys
import json
import time
from lxml import objectify, etree

import bpformation


#
# TODO vCur:
#  o Delete
#  o Export
#  o Import
#  o Create
#  o Change


#
# TODO vNext:
#


class Blueprint():

	#visibility_stoi = { 'Public': 1, 'Private': 2, 'Shared': 3}
	limited_printable_chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&'()*+,-./:;<=>?@[]^_`{|}~  "


#	@staticmethod
#	def Delete(uuids):
#		for uuid in uuids:
#			r = bpformation.web.CallScrape("POST","/blueprints/packages/DeletePackage/",
#							               payload={"id": uuid, "classification": "Script", })
#			if r.status_code<400 and r.status_code>=200:
#				bpformation.output.Status('SUCCESS',3,"%s package deleted" % uuid)
#			else:
#				bpformation.output.Status('ERROR',3,"%s package deletion error (status code %s)" % (uuid,r.status_code))


	@staticmethod
	def _ParseExportTaskDeployPackage(root):
		for package in root.iter("DeployPackage"):
			print package.get("ID")
			package_obj = {"id": package.get("ID"), "uuid": package.get("UUID"), "name": package.get("Title") }
			if package.get("Server"):  package_obj['server'] = package.get("Server")
			print package.get("Server")
			# TODO - design time parameters
			#for prop in package[0]:
			#	if prop.get("Value")=="True":  package_obj[prop.get("Name").lower()] = True
			#	elif prop.get("Value")=="False":  package_obj[prop.get("Name").lower()] = False
			#	else:  package_obj[prop.get("Name").lower()] = prop.get("Value")
			print package_obj

			return(package_obj)


	@staticmethod
	def _ParseExportTaskBuildServer(root):
		# Server foundation data
		server = { 'name': root.get("Alias"), 'uuid': root.get("UUID"), 'description': root.get("Description"),
				   'id': root.get("ID"), 'template': root.get("Template"), 'cpu': root.get("CpuCount"), 
				   'ram': root.get("MemoryGB"), 'disks': [], 'packages': [] }

		# TODO - parse multiple disks
		server['packages'] = [ Blueprint._ParseExportTaskDeployPackage(o) for o in root.findall(".//DeployPackage") ]
		server['disks'] = [ Blueprint._ParseExportTaskDisk(o) for o in root.findall(".//AddDisk") ]
		#server['packages'] = Blueprint._ParseExportTaskDeployPackage(root)
		# TODO other system packages

		# AddDisk
		for disk in root.iter("AddDisk"):
			disk_obj = {"id": disk.get("ID"), "uuid": disk.get("UUID")}
			for prop in disk[0]:
				# TODO - set standard disk
				if prop.get("Value")=="True":  disk_obj[prop.get("Name").lower()] = True
				elif prop.get("Value")=="False":  disk_obj[prop.get("Name").lower()] = False
				else:  disk_obj[prop.get("Name").lower()] = prop.get("Value")
			server['disks'].append(disk_obj)

		bp['servers'].append(server)


	@staticmethod
	def Export(id):

		# Blueprint definition
		r = bpformation.web.CallScrape("GET","/Blueprints/Designer/BlueprintXml/%s" % id)
		if r.status_code<200 or r.status_code>=300:
			bpformation.output.Status('ERROR',3,"Error retrieving data (http response %s)" % r.status_code)
			raise(bpformation.BPFormationFatalExeption("Fatal Error"))

		t = etree.XML(r.text)
		
		bp = {'metadata': {}, 'tasks': []}
		for o in t.findall(".//Tasks/*"):
			print o.tag
			if o.tag=="BuildServer":  bp['tasks'].append(Blueprint._ParseExportTaskBuildServer(o))
			if o.tag=="DeployPackage":  bp['tasks'].append(Blueprint._ParseExportTaskDeployPackage(o))
			else:  print "Unknown: %s" % o.tag

		# Blueprint top-level and metadata
		# TODO - need to maintain the ordering of all scripts and server build commands
		# TODO - add system and other tasks done outside of a single server level
		#bp['packages'] = [ Blueprint._ParseExportTaskDeployPackage(o) for o in t.findall(".//Tasks/DeployPackage") ]

		print json.dumps(bp,sort_keys=True,indent=4,separators=(',', ': '))


	# Available, but not returning:
	#  o Price information
	#  o Environment size details (server count, memory, CPU, etc.)
	#  o Blueprint description
	@staticmethod
	def List(filters):
		r = bpformation.web.CallScrape("POST","/blueprints/browser/LoadTemplates",payload={
					'Search-PageSize': 1000,
					'Search-PageNumber': 1,
				}).text

		blueprints = []
		for blueprint_html in filter(lambda x: x in Blueprint.limited_printable_chars, r).split('class="blueprint-specs"'):
			try:
				blueprints.append({'name': re.search('class="blueprint-header">.*<label>(.+?)</label>',blueprint_html).group(1),
						           'owner': re.search('<div class="author">by (.+?)</div>',blueprint_html).group(1),
								   'date_added': re.search('<em>(.+?)</em>',blueprint_html).group(1),
								   'description': re.search('<div class="blueprint-desc">\s*<div><strong>(.+?)</strong>',blueprint_html).group(1),
								   'visibility': re.search('<div class="right-col"><strong>(.+?)</strong></div>',blueprint_html).group(1),
						           'id': re.search('<a href="/blueprints/browser/details/(\d+)">',blueprint_html).group(1) })
				
			except:
				pass

		# Apply filters if any are specified
		if not filters:  blueprints_final = blueprints
		else:
			blueprints_final = []
			for blueprint in blueprints:
				match = True
				for one_filter in filters:
					if not re.search(one_filter," ".join(blueprint.values()),re.IGNORECASE):  match = False
				if  match:  blueprints_final.append(blueprint)

		return(blueprints_final)




