from aiortc import (RTCIceTransport, RTCIceGatherer, RTCCertificate, RTCDtlsTransport, RTCIceCandidate, RTCIceParameters)
from aioice import (Candidate)
import asyncio
import websockets
import json

WEBSOCKET_URI = "ws://127.0.0.1:8765"


def candidate_to_aioice(x: RTCIceCandidate) -> Candidate:
    return Candidate(
        component=x.component,
        foundation=x.foundation,
        host=x.ip,
        port=x.port,
        priority=x.priority,
        related_address=x.relatedAddress,
        related_port=x.relatedPort,
        transport=x.protocol,
        tcptype=x.tcpType,
        type=x.type,
    )


def candidate_from_aioice(x: Candidate) -> RTCIceCandidate:
    return RTCIceCandidate(
        component=x.component,
        foundation=x.foundation,
        ip=x.host,
        port=x.port,
        priority=x.priority,
        protocol=x.transport,
        relatedAddress=x.related_address,
        relatedPort=x.related_port,
        tcpType=x.tcptype,
        type=x.type,
    )


class DummyDataReceiver:
    def __init__(self):
        self.data = []

    async def _handle_data(self, data):
        self.data.append(data)


async def main():
    websocket = await websockets.connect(WEBSOCKET_URI)

    gatherer = RTCIceGatherer()
    transport = RTCIceTransport(gatherer)

    # asyncio.get_event_loop().run_until_complete()
    await gatherer.gather()

    print("gather")

    message = json.loads(await websocket.recv())

    print("message %s" % {repr(message)})

    candidates = [Candidate.from_sdp(c) for c in message["candidates"]]
    for candidate in candidates:
        transport.addRemoteCandidate(candidate_from_aioice(candidate))

    await websocket.send(
        json.dumps(
            {
                "candidates": [candidate_to_aioice(c).to_sdp() for c in gatherer.getLocalCandidates()],
                "password": transport.iceGatherer.getLocalParameters().password,
                "username": transport.iceGatherer.getLocalParameters().usernameFragment,
            }
        )
    )

    params = RTCIceParameters(usernameFragment=message["username"],
                              password=message["password"])
    print("params %s" % {repr(params)})
    await transport.start(params)

    print("connect")

    certificate = RTCCertificate.generateCertificate()
    session = RTCDtlsTransport(transport, [certificate])
    receiver = DummyDataReceiver()
    session._register_data_receiver(receiver)
    params = session.getLocalParameters()
    print("dtls params %s %s %s" % {params.fingerprints[0].algorithm, params.fingerprints[0].value, params.role})

    data = await transport._recv()
    print("message %s" % {repr(data)})
    await websocket.close()

    # await session.start()

asyncio.get_event_loop().run_until_complete(main())
