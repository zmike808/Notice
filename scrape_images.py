#!/usr/bin/env python

import argparse
import os
import urllib
import MySQLdb
import sys
import facebook
from PIL import Image

# you must create a Cursor object. It will let
#  you execute all the query you need

def setupParser():
  parser = argparse.ArgumentParser(description="Scrape pictures from Facebook.")
  parser.add_argument("node",
      help="Facebook Graph node, used as the root node in our search")
  parser.add_argument("token", help="Facebook API access token", type=str)
  return parser.parse_args()

def saveFriendPhotos(facebookId, graph, visitedPhotos):

  foundPeople = set()
  photos = graph.get_connections(facebookId, "photos", fields="source,tags")
  for photo in photos["data"]:
    if photo["id"] in visitedPhotos: continue
    visitedPhotos.add(photo["id"])
    # Download the photo from Facebook
    originalPhoto = "original_photos/" + photo["id"] + ".jpg"
    urllib.urlretrieve(photo["source"], originalPhoto)
    for person in photo["tags"]["data"]:
      try:
        foundPeople.add(person["id"])
        # Create person directory if it doesn't already exist
        if not os.path.isdir("photos/" + person["id"]):
          os.makedirs("photos/" + person["id"])
        photoLocation = "photos/" + person["id"] + "/" + photo["id"] + ".jpg"
        # Crop the photo so it only contains the face
        image = Image.open(originalPhoto)
        imageTagX = int(image.size[0] * person["x"]/100)
        imageTagY = int(image.size[1] * person["y"]/100)
        # TODO: We probably want to choose asubpicture size that varies by the
        # original size
        #print "imageid: ",photo["id"], "tagx: ",imageTagX," tagy: ",imageTagY
        subx = 50#int(image.size[0] * .25)
        suby = 50#int(image.size[1] * .25)
        dimensions = (imageTagX-subx, imageTagY-suby, imageTagX+subx, imageTagY+suby)
        area = image.crop(dimensions)
        area.save(photoLocation, "jpeg")
      except KeyError:
        # Some tags seem to have missing information. I'm not sure why.
        continue
  return foundPeople

def generateTrainingXML():
  f = open('sigsets.xml','w')
  f.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<biometric-signature-set>\n")
  dirs = os.walk('./photos').next()[1]
  for dir in dirs:
    for file in os.listdir("./photos/"+dir):
      f.write("\t<biometric-signature name=\""+dir+"\">\n\t\t<presentation file-name=\""+file+"\"/>\n\t</biometric-signature>")
  f.write("</biometric-signature-set>")
  f.close()

def main():
  args = setupParser()
  graph = facebook.GraphAPI(args.token)
  visitedPeople = set()
  visitedPhotos = set()
  foundPeople = saveFriendPhotos("me", graph, visitedPhotos)
  # Walk one level deeper
  for person in foundPeople:
    saveFriendPhotos(person, graph, visitedPhotos)
  generateTrainingXML()
  
if __name__ == "__main__":
  main()
