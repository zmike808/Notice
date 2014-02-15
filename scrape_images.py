#!/usr/bin/env python

import argparse
import os
import urllib
import MySQLdb
import facebook
from PIL import Image
db = MySQLdb.connect(host="localhost", # your host, usually localhost
                     user="pennapps", # your username
                      passwd="pennapps", # your password
                      db="pennapps") # name of the data base

# you must create a Cursor object. It will let
#  you execute all the query you need
cur = db.cursor()

def setupParser():
  parser = argparse.ArgumentParser(description="Scrape pictures from Facebook.")
  parser.add_argument("node",
      help="Facebook Graph node, used as the root node in our search")
  parser.add_argument("token", help="Facebook API access token", type=str)
  return parser.parse_args()

def saveFriendPhotos(facebookId, graph, visitedPhotos):

  foundPeople = set()
  photos = graph.get_connections(facebookId, "photos", fields="images,tags")
  for photo in photos["data"]:
    if photo["id"] in visitedPhotos: continue
    visitedPhotos.add(photo["id"])
    # Download the photo from Facebook
    originalPhoto = "original_photos/" + photo["id"] + ".jpg"
    urllib.urlretrieve(photo["images"][0]["source"], originalPhoto)
    for person in photo["tags"]["data"]:
      try:
        foundPeople.add(person["id"])
        sqlformattedID = "'"+person["id"]+"'"
        sqlformattedName = "'"+person["name"]+"'"
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
        dimensions = (imageTagX-50, imageTagY-50, imageTagX+50, imageTagY+50)
        area = image.crop(dimensions)
        area.save(photoLocation, "jpeg")
        try:
            sql = "INSERT INTO names VALUES("+sqlformattedID+","+sqlformattedName+")"
            cur.execute(sql)
        except IntegrityError: #means its already inserted/exists
            continue
      except KeyError:
        # Some tags seem to have missing information. I'm not sure why.
        continue
  return foundPeople

def main():
  args = setupParser()
  graph = facebook.GraphAPI(args.token)
  visitedPeople = set()
  visitedPhotos = set()
  foundPeople = saveFriendPhotos("me", graph, visitedPhotos)
  # Walk one level deeper
  for person in foundPeople:
    saveFriendPhotos(person, graph, visitedPhotos)

if __name__ == "__main__":
  main()
