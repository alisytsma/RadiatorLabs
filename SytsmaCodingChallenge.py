import requests
import base64
import time

recordNumber = 1
sendCount = 1
start = 0
runningChecksum = 0
keepRunning = True

# read the file
def readFile(startLocation, endLocation):
    global fileToOpen
    try:
        with open("example.hex") as file:
            file.seek(startLocation)
            if (file.read(1) == '\n'):
                file.seek(startLocation+1)
            return file.read(endLocation - startLocation)
    except:
        print("File not found")

# handles posting of data and calculating the runningChecksum    
def handleData(size, data):
    global runningChecksum
    global recordNumber
    global sendCount
    # try to post the data to the server
    try:
        chunkResponse = requests.post("http://localhost:3000", "CHUNK: " + data)
        print("\tCHUNK Response:", chunkResponse.status_code,  chunkResponse.reason, chunkResponse.text.replace('\n', ''))
        checksumResponse = requests.post("http://localhost:3000", 'CHECKSUM')
        print("\tCHECKSUM Response:", checksumResponse.status_code, checksumResponse.reason, checksumResponse.text.replace('\n', ''))
        if(chunkResponse.status_code > 200 or checksumResponse.status_code > 200):
            print("**ERROR**: HTTP Error... Trying again in ")
            print("\t3" )
            time.sleep(1)
            print("\t2" )
            time.sleep(1)
            print("\t1" )
            time.sleep(1)
            handleData(size, data)
            return
        elif('0x' in checksumResponse.text):
            checksumResponse = checksumResponse.text[checksumResponse.text.find('0x'):].replace('\n', '')
            checksumResponse = int(checksumResponse, 0)
            
    # if not, retry
    except:
        print("**ERROR**: Cannot connect to server... Trying again in ")
        print("\t3" )
        time.sleep(1)
        print("\t2" )
        time.sleep(1)
        print("\t1" )
        time.sleep(1)
        handleData(size, data)
        return

    # Check to see if receiving device wrote data successfully, if not retry
    if('ERROR' in chunkResponse.text):
        print('**ERROR**: Device write error... trying again ')
        handleData(size, data)
        return
    else:  
        # calculate the runningChecksum
        decodedData = base64.b64decode(data)
        for x in range(0, len(decodedData)):
            runningChecksum += decodedData[x]
            runningChecksum %= 256
        # return current info
        print("Send Count: " + str(sendCount) + ", Record Number: " + str(recordNumber) + ", Chunk Sent: " + data + ", Checksum: " + str(runningChecksum))
        # Verify our checksum against the device's checksum
        if(checksumResponse==runningChecksum):
            print('*SUCCESS*: Checksum Verified!\n')
            sendCount += 1
        else:
            print('**CRITICAL ERROR**: Checksum verification error...terminating...')
            keepRunning = False
            exit()
            return
        

# Continue until we're done with the whole file 
while keepRunning:
    # figure out how big the record is and grab it in full
    getSize = int(readFile(start,start+2), 16)*2
    getRecord = readFile(start, start+8+getSize+2+1).replace('\n', '').replace(':', '')

    # grab the type, data, and checksum from the record
    getType = getRecord[6:8]
    getData = getRecord[8:8+getSize]
    getChecksum = getRecord[8+getSize:]

    # check for end of file using the Type code
    if (getType == '01'):
        print("********END OF FILE - DONE********")
        keepRunning = False
        break;
    
    # break data into 20 byte chunks
    tempInt = 0
    while (len(getData) > 0):
        chunk = getData[tempInt:tempInt+20]
        getData = getData[tempInt+20:]
        handleData(getSize, chunk)
    
    # increment record number for each new line
    recordNumber += 1
    
    # increment each line by it's size, plus the size of the start
    start += 8+getSize+2+1+2
