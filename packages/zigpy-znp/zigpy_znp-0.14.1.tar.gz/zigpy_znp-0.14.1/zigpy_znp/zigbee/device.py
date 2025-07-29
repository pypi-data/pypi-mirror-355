from __future__ import annotations

import logging

import zigpy.zdo
import zigpy.types
import zigpy.device
import zigpy.application

LOGGER = logging.getLogger(__name__)


class ZNPCoordinator(zigpy.device.Device):
    """
    Coordinator zigpy device that keeps track of our endpoints and clusters.
    """

    @property
    def manufacturer(self):
        return "Texas Instruments"

    @property
    def model(self):
        return "Coordinator"

    async def request(
        self,
        profile,
        cluster,
        src_ep,
        dst_ep,
        sequence,
        data,
        expect_reply=True,
        timeout=2 * zigpy.device.APS_REPLY_TIMEOUT,
        use_ieee=False,
        ask_for_ack: bool | None = None,
        priority: int = zigpy.types.PacketPriority.NORMAL,
    ):
        """
        Normal `zigpy.device.Device:request` except its default timeout is longer.
        """

        return await super().request(
            profile=profile,
            cluster=cluster,
            src_ep=src_ep,
            dst_ep=dst_ep,
            sequence=sequence,
            data=data,
            expect_reply=expect_reply,
            timeout=timeout,
            use_ieee=use_ieee,
            ask_for_ack=ask_for_ack,
            priority=priority,
        )
