import asyncio
from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosedOK
import websockets
import pyedflib
import numpy as np
import time
import io
import json
import re
import pyarrow as pa
import avro.schema
from avro.io import DatumWriter, BinaryEncoder

# open avro schema
with open("eeg2.avsc", "r") as f:
    schema = avro.schema.parse(f.read())

# read edf file and extract channel names, sample frequency, startdate, and EEG data
edf = "stephen_dcf340a2.edf"
f = pyedflib.highlevel.read_edf_header(edf)
if 'channels' in f.keys():
    pattern = re.compile(r'(?:EEG\s)?([A-Z0-9]+)(?:-[A-Z0-9]+)?')
    channels = []
    for c in f['channels']:
        if pattern.match(c):
            channels.append(c)
        else:
            raise ValueError('unexpected channel name')
else:
    raise KeyError("channels not valid key")
if 'SignalHeaders' not in f.keys():
    raise KeyError("SignalHeaders not valid key")
elif 'sample_frequency' not in f['SignalHeaders'][0].keys(): 
    raise KeyError("sample_frequency not valid key")
else:
    fs = f['SignalHeaders'][0]['sample_frequency']
if 'startdate' not in f.keys():
    raise KeyError("startdate not valid key")
else:
    startdate = f['startdate']
data = pyedflib.highlevel.read_edf(edf)[0]

RATE = 250
INTERVAL = 1.0 / RATE
factor = fs // RATE
data = data[::int(factor)] # reduce data to 250 Hz

batch_size = 25

async def send_eeg():
    try:
        async with websockets.connect("ws://10.0.0.205:8001", max_size=None) as websocket:
            await websocket.send("tablet") # notify server tablet is connected
            start = time.perf_counter()
            messageIdx = 0

            # compute seek time from datetime object to ms and set seek stamp
            seekTime = int(startdate.timestamp() * 1000)
            seekStamp = 0
        
            for i in range(0, data.shape[1], batch_size):
                # convert data to bytes directly - transpose chunk first
                data_T = data[:, i:i+batch_size].T.astype(np.float32)
                data_bytes = data_T.tobytes()

                # compute last time and last stamp from seek time and seek stamp respectively
                lastTime = seekTime + int(data.shape[1] / fs * 1000)
                lastStamp = seekStamp + batch_size - 1
    
                # create data following avro schema
                epoch = {
                    "messageIdx": messageIdx,
                    "montage": channels,
                    "seekTime": seekTime,
                    "lastTime": lastTime,
                    "seekStamp": seekStamp,
                    "lastStamp": lastStamp,
                    "samplingFreq": fs,
                    "streamType": "EEG",
                    "streamTypeCustom": None,
                    "shape": [batch_size, len(channels)],
                    "data": data_bytes
                }
        
                # serialize
                buffer = io.BytesIO()
                writer = DatumWriter(schema)
                enc = BinaryEncoder(buffer)
                writer.write(epoch, enc)
                serialized = buffer.getvalue()
        
                await websocket.send(serialized)

                # increment the following fields for next batch
                messageIdx += 1 # index for next chunk
                seekTime += int(batch_size / fs * 1000) # increment by 100ms (0.1s)
                seekStamp += batch_size # increment by batch size
        
                # ensures each sample is sent every 4 ms
                elapsed = time.perf_counter() - start
                target = (i+1) * INTERVAL
                delay = max(0, target - elapsed)
                await asyncio.sleep(delay)
        
            print("Done streaming EEG data")
    except Exception as e:
        print(e)

asyncio.run(send_eeg())
        