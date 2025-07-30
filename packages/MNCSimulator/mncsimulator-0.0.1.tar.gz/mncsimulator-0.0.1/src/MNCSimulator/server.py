import asyncio
from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosedOK
import numpy as np
import pyarrow as pa
import io
import avro.schema
from avro.io import DatumWriter, BinaryEncoder, DatumReader, BinaryDecoder

# open avro schema
with open("eeg2.avsc", "r") as f:
    schema = avro.schema.parse(f.read())
    
clients = {"tablet": None, "browser": None}

async def handler(websocket):
    client = await websocket.recv()
    print(f"{client} currently connected")

    if client not in clients:
        await websocket.send("Invalid client")
        await websocket.close()
        return

    clients[client] = websocket
    try:
        if client == "tablet":
            # if browser not connected, sleep till browser connects
            while clients["browser"] is None:
                print("Tablet waiting for browser...")
                await asyncio.sleep(0.5)
                
            while True:
                msg = await websocket.recv()

                # deserialize
                buffer = io.BytesIO(msg)
                reader = DatumReader(schema, None)
                dec = BinaryDecoder(buffer)
                deserialized = reader.read(dec)

                # reconstruct data from bytes to floats and correct shape
                data_new = np.frombuffer(deserialized['data'], dtype=np.float32).reshape((deserialized['shape'][0], deserialized['shape'][1]))
                channels = deserialized['montage']

                # create arrow schema for data by channels
                schema_arrow = pa.schema([
                    (c, pa.float32()) for c in channels
                ])

                # serialize data with arrow
                arrow_table = pa.Table.from_arrays(
                    [pa.array(data_new[:, c], type=pa.float32()) for c in range(len(channels))],
                    schema=schema_arrow
                )
                buffer = io.BytesIO()
                with pa.RecordBatchStreamWriter(buffer, arrow_table.schema) as writer:
                    writer.write_table(arrow_table)
                arrow_bytes = buffer.getvalue()

                # create data following avro schema with data serialized in arrow
                epoch = {
                    "messageIdx": deserialized['messageIdx'],
                    "montage": channels,
                    "seekTime": deserialized['seekTime'],
                    "lastTime": deserialized['lastTime'],
                    "seekStamp": deserialized['seekStamp'],
                    "lastStamp": deserialized['lastStamp'],
                    "samplingFreq": deserialized['samplingFreq'],
                    "streamType": deserialized['streamType'],
                    "streamTypeCustom": deserialized['streamTypeCustom'],
                    "shape": deserialized['shape'],
                    "data": arrow_bytes
                }

                # serialize
                buffer = io.BytesIO()
                writer = DatumWriter(schema)
                enc = BinaryEncoder(buffer)
                writer.write(epoch, enc)
                serialized = buffer.getvalue()

                # if browser connected, send serialized data to browser
                if clients["browser"]:
                    await clients["browser"].send(serialized)
                    print("Sent to browser")
        else:
            while True:
                await asyncio.sleep(1) # if tablet not connected, sleep till connected
    except ConnectionClosedOK:
        print(f"{client} disconnected")
    finally:
        clients[client] = None

async def main():
    async with serve(handler, "0.0.0.0", 8001, max_size=None):
        print("WebSocket server running at ws://0.0.0.0:8001")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())