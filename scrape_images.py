#!/usr/bin/env python

import argparse
import os
import urllib
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

def populateVisitedPeople():
  visitedPeople = set()
  for filename in os.listdir("original_photos"):
    visitedPeople.add(os.path.splitext(filename)[0])
  return visitedPeople

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
  f = open('./photos/sigset.xml','w')
  #count = 1
  f.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<biometric-signature-set>\n")
  dirs = os.walk('./photos').next()[1]
  for dir in dirs:
    for file in os.listdir("./photos/"+dir):#presentation name="4" file-format="jpeg" file-name="S001-04-t10_01.jpg" modality="face"/  
      #f.write("\t<biometric-signature name=\""+dir+"\">\n\t\t<presentation name=\""+count+"\"file-format=\"jpeg\" file-name=\""dir+"/"+file+"\" modality=\"face\"/>\n\t</biometric-signature>")
      f.write("\t<biometric-signature name=\""+dir+"\">\n\t\t<presentation file-name=\""+dir+"/"+file+"\"/>\n\t</biometric-signature>")
      #count += 1
  f.write("\n</biometric-signature-set>")
  f.close()

def main():
  args = setupParser()
  graph = facebook.GraphAPI(args.token)
  visitedPeople = populateVisitedPeople()
  visitedPhotos = set()
  foundPeople = saveFriendPhotos("me", graph, visitedPhotos)
  # Walk one level deeper
  for person in foundPeople:
    saveFriendPhotos(person, graph, visitedPhotos)
  generateTrainingXML()
  os.system('br -algorithm \'Open+Cvt(Gray)+Cascade(FrontalFace)+ASEFEyes+Affine(88,88,0.25,0.35)+FTE(DFFS,instances=1)+Mask+Blur(1.1)+Gamma(0.2)+DoG(1,2)+ContrastEq(0.1,10)+LBP(1,2)+RectRegions(8,8,6,6)+Hist(59)+PCA(0.95,instances=1)+Normalize(L2)+Cat+Dup(12)+RndSubspace(0.05,1)+LDA(0.98,instances=-2)+Cat+PCA(768,instances=1)+Normalize(L1)+Quantize:MatchProbability(ByteL1)\' -path ./photos -train "sigset.xml" sofit')
  os.system('rm ./photos/sigset.xml')
  os.system('br -algorithm FaceRecognition -enrollAll -enroll ./photos  \'sofit.gal;sofit.csv[separator=;]\'')
  #os.system('
  
if __name__ == "__main__":
  main()
