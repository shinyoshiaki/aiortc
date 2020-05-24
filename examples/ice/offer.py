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


async def main():
    websocket = await websockets.connect(WEBSOCKET_URI)

    gatherer = RTCIceGatherer()
    transport = RTCIceTransport(gatherer)

    print("websocket")

    await gatherer.gather()

    print("gather")

    await websocket.send(
        json.dumps(
            {
                "candidates": [candidate_to_aioice(c).to_sdp() for c in gatherer.getLocalCandidates()],
                "password": transport.iceGatherer.getLocalParameters().password,
                "username": transport.iceGatherer.getLocalParameters().usernameFragment,
            }
        )
    )

    message = json.loads(await websocket.recv())

    print("message %s" % {repr(message)})

    candidates = [Candidate.from_sdp(c) for c in message["candidates"]]
    for candidate in candidates:
        transport.addRemoteCandidate(candidate_from_aioice(candidate))

    params = RTCIceParameters(usernameFragment=message["username"],
                              password=message["password"])
    print("params %s" % {repr(params)})
    await transport.start(params)

    print("connect")

    await transport._send(b"hello")
    await websocket.close()

    # certificate = RTCCertificate.generateCertificate()
    # session = RTCDtlsTransport(transport, [certificate])

asyncio.get_event_loop().run_until_complete(main())
