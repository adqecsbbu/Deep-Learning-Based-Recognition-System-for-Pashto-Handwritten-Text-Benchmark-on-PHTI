#!/usr/bin/env python
#from Scientific.IO import NetCDF
import netcdf_helper #as netcdf_helper
from scipy import *
from optparse import OptionParser
import sys#, cv2
from PIL import Image, ImageChops
import numpy
from sklearn import preprocessing
import os
import fnmatch
import codecs
#from deSkew import *
#from prunLines import *
#from convertToLigature import *


DATAPATH="/media/ibrar/GENERAL/workspace/NEW_PHTI_FNL94/"

def computeScaler(listofFiles):
	imgData=[]
	seqL=[]
	height=48
	for imgname in listofFiles:
		img=Image.open(DATAPATH+imgname).convert("L")
		w,h=img.size	
		#This code will insure to keep the expect ratio locked
		nc2 = int(round(height* 1.0/h*w))
		width=nc2
		img= img.resize((width,height), Image.ANTIALIAS)
		imgData.append(img)
		seqL.append(img.size[1]*img.size[0]) 
		
	inputs2 = zeros((sum(seqL), 1), 'f')
	offset = 0
	for im in imgData:
		  image = im.transpose(Image.ROTATE_270).transpose(Image.FLIP_TOP_BOTTOM)
		  for i in image.getdata():
			inputs2[offset][0] = (float(i)/255.0)
			offset += 1
	Scalar = preprocessing.StandardScaler().fit(inputs2)
	return Scalar
		

def pashtoNC(inputfilenames,ncFile,labels,Scalar=None,Normalize=None):
	
	
	print("reading file data")
	height=48
	#brCharList=[u'\u0627',u'\u0648',u'\u0632',u'\u062f',u'\u0631', u'\u0689',u'\u0693',u'\u0698',u'\u0696',u'\u06d2',u'\u0630',u'\u0623',u'\u0622',u'\u0624',
	#u'\u060c',u'\u061b',u'\u06f0',u'\u0629']
	seqDims = []
	seqLengths = []
	targetStrings = []
	wordTargetStrings=[]
	seqTags = []
	filenames = []
	inputs=[]
	excludeFiles=[]
	
	allTrainData=[]
	for data in inputfilenames:
			
		targetString=""
		
		if len(data):
		   
				print "Collecting input data from File:",data
				#print str(path+imgname)
				img=Image.open(DATAPATH+data).convert("L") 
				#~ img=returnSkewAngle(path+imgname)
				
				#break
				#w,h=img.size	
				#~ img=prunLines(img)
				img=img.convert("L")
				#img.show()
				#break
				w,h=img.size	
				#This code will insure to keep the expect ratio locked
				nc2 = int(round(height* 1.0/h*w))
				width=nc2
				img= img.resize((width,height), Image.ANTIALIAS)
				
				dims = (img.size[1], img.size[0])
				#seqTags.append(str(fname))
				seqLengths.append(dims[0] * dims[1])
				seqDims.append(dims)
				
				#gtFile=fname.replace("tif","txt")
				#print gtdata
				gtname=data.replace("jpg","txt")
				with codecs.open(DATAPATH+gtname,'r',"utf-8") as stream:
				  line=stream.read()
				  line=line.strip()
				  line=line.replace("\n", "")
				  line=line.replace("\r", "")
				  line=line.replace("\n\r", "")
				  #Ligatures=extractLigatures(line)
				stream.close()
				#chars=chars.split(" ")
				for ch in line:
				    encodedStr = ch.encode('utf-8', "backslashreplace")
				    ##encodedStr=encodedStr.strip(" ")
				    ##encodedStr=encodedStr.replace(" ","")
				    targetString += encodedStr + ' '
				    labels.append(encodedStr)
				    ##targetString += lb + ' '
				
				targetString=targetString.strip()
				#targetString=targetString.strip("S")
				#~ print targetString
				targetStrings.append(targetString)
				seqTags.append(str(data))
				allTrainData.append(img)
					
		else:
			print "OutOut" #
	
	labels = numpy.unique(numpy.array(labels)).tolist()
	print len(labels)
	
	#return
	
	inputs = zeros((sum(seqLengths), 1), 'f')
	print shape(inputs)
	offset = 0	
	for image,gt in zip(allTrainData,targetStrings):
		
		image = image.transpose(Image.ROTATE_270).transpose(Image.FLIP_TOP_BOTTOM)
		###for ch in gt:
		#print gt#.encode('utf-8', "backslashreplace")
		#image.show()
		#break
		print "writing inputs!!",image.size
		
		for i in image.getdata():
		  inputs[offset][0] = (float(i)/255.0)# - inputMean)/inputStd
		  offset += 1
	#print len(labels)
	
	#~ if Normalize:
	  #~ Scalar = preprocessing.StandardScaler().fit(inputs)
	  
	  #~ Normalize=False
	  
	#~ ###print "Scalar........",Scalar
	inputs = Scalar.transform(inputs)
	
	
	
	file = netcdf_helper.NetCDFFile(ncFile, 'w')#format='NETCDF3_CLASSIC')
	
	netcdf_helper.createNcDim(file,'numSeqs',len(seqLengths))
	netcdf_helper.createNcDim(file,'numTimesteps',len(inputs))
	netcdf_helper.createNcDim(file,'inputPattSize',len(inputs[0]))
	netcdf_helper.createNcDim(file,'numDims',2)#Disable only when you need nc file for 1D LSTM...
	netcdf_helper.createNcDim(file,'numLabels',len(labels))

	netcdf_helper.createNcStrings(file,'seqTags',seqTags,('numSeqs','maxSeqTagLength'),'sequence tags')
	netcdf_helper.createNcStrings(file,'labels',labels,('numLabels','maxLabelLength'),'labels')
	netcdf_helper.createNcStrings(file,'targetStrings',targetStrings,('numSeqs','maxTargStringLength'),'target strings')
	#netcdf_helper.createNcStrings(file,'wordTargetStrings',wordTargetStrings,('numSeqs','maxWordTargStringLength'),'target strings')
	
	netcdf_helper.createNcVar(file,'seqLengths',seqLengths,'i',('numSeqs',),'sequence lengths')
	netcdf_helper.createNcVar(file,'seqDims',seqDims,'i',('numSeqs','numDims'),'sequence dimensions')#Only disable when you need nc file for 1D LSTM... 
	netcdf_helper.createNcVar(file,'inputs',inputs,'f',('numTimesteps','inputPattSize'),'input patterns')
	#write the data to disk
	print "closing file",ncFile
	file.close()
	return  Scalar,labels, Normalize
			
			
if __name__ == "__main__":
	
	pattern="*.txt"
	allnames=[]
	train_names=[]
	test_names=[]
	val_names=[]
	
	
	labels=[]

	with codecs.open("NEW_PHTI_FNL94.txt",'r','utf-8') as stream:
		for ln in stream.readlines():
			ln=ln.strip('\n')
			#~ print (ln)
			allnames.append(ln)
	stream.close()

	
	
	print(str(len(train_names)))
	#~ print (fnames)
		
	lines=[]
	for fn in allnames:
		#~ print (fn)
		gtf=fn.replace("jpg",'txt')
		line=codecs.open(DATAPATH+gtf,'r',"utf-8").readline()
		#~ print(line)
        #~ line=stream.read()
		line=line.strip('\n')
		line=line.replace("\n", "")
		line=line.replace("\r", "")
		line=line.replace("\n\r", "")
		lines.append(line)
			
	for ln in lines:
		for ch in ln:
			encodedStr = ch.encode('utf-8', "backslashreplace")
			labels.append(encodedStr)	
	#~ print(str(len(set(labels))))
	print ("Computing Scalar....")
	Scalar=computeScaler(allnames[0:18140])
	print ("Scalar computed")
	
	#~ print(str(len(train_names)))
	Normalize=True
	Scalar,labels, Normalize=pashtoNC(allnames[0:9070],"PHTI_Train_MDNC_0_1.nc",labels,Scalar,Normalize)
	Scalar,labels, Normalize=pashtoNC(allnames[9071:18140],"PHTI_Train_MDNC_0_2.nc",labels,Scalar,Normalize)
	Scalar,labels, Normalize=pashtoNC(allnames[18141:22027],"PHTI_Val_MDNC_0_1.nc",labels,Scalar,Normalize)
	Scalar,labels, Normalize=pashtoNC(allnames[22028:len(allnames)],"PHTI_Test_MDNC_0_1.nc",labels,Scalar,Normalize)
	
