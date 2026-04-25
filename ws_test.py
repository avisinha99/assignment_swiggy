import asyncio

import websockets

PROJECT_ID = "2252d478-a7e9-46b4-9f04-cbdec582c895"
URL = f"ws://127.0.0.1:8000/ws?project_id={PROJECT_ID}&since_activity_id=0"


async def main() -> None:
    async with websockets.connect(URL) as ws:
        print("connected:", URL)
        while True:
            msg = await ws.recv()
            print(msg)


if __name__ == "__main__":
    asyncio.run(main())

