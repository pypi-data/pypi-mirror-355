from __future__ import annotations
import asyncio
from typing import TYPE_CHECKING, List, Optional, Dict, Any, Tuple # Added Tuple for UUID parsing helper

from .consts import SDK_LOGGER # Use SDK logger
from .wiim_device import WiimDevice, GeneralEventCallback
from .exceptions import WiimException
from .consts import WiimHttpCommand, MultiroomAttribute, DeviceAttribute # Renamed
from .discovery import async_discover_wiim_devices_upnp
from .exceptions import WiimDeviceException, WiimRequestException

if TYPE_CHECKING:
    from aiohttp import ClientSession


class WiimController:
    """Manages multiple WiiM devices and multiroom groups."""

    def __init__(self, session: ClientSession, event_callback: GeneralEventCallback | None = None):
        self.session = session
        self._devices: Dict[str, WiimDevice] = {}  # UDN: WiimDevice
        self._multiroom_groups: Dict[str, List[str]] = {} # Leader UDN: [Follower UDNs]
        self._event_callback = event_callback # Callback for device state changes
        self.logger = SDK_LOGGER
        # Note: If WiimData also holds entity_id_to_udn_map, it should be managed from __init__.py
        # or passed into this controller. For now, assume this controller gets devices.


    def get_device(self, udn: str) -> WiimDevice | None:
        """Get a device by its UDN."""
        return self._devices.get(udn)

    @property
    def devices(self) -> List[WiimDevice]:
        """Return a list of all managed WiiM devices."""
        return list(self._devices.values())

    async def add_device(self, wiim_device: WiimDevice) -> None:
        """Add a WiiM device to the controller."""
        if wiim_device.udn in self._devices:
            self.logger.debug("Device %s already managed.", wiim_device.udn)
            # If the device is already known, update its reference in case of new details
            # Or decide to just return if it's already there
            # For robust updates, you might want to replace the existing object or merge properties.
            # self._devices[wiim_device.udn] = wiim_device 
            return

        self._devices[wiim_device.udn] = wiim_device
        self.logger.info("Added device %s (%s) to controller.", wiim_device.name, wiim_device.udn)
        # It's better to update multiroom status for this *new* device individually
        # or rely on async_update_all_multiroom_status being called after a batch of adds.
        # Calling async_update_all_multiroom_status here might be too frequent if many devices
        # are added at once. However, for a single add, it's fine.
        await self.async_update_all_multiroom_status()


    async def remove_device(self, udn: str) -> None:
        """Remove a WiiM device from the controller."""
        device = self._devices.pop(udn, None)
        if device:
            await device.disconnect() # Clean up device's resources (e.g., UPnP subscriptions)
            self.logger.info("Removed device %s (%s) from controller.", device.name, udn)
            # Update multiroom status as a device was removed
            await self.async_update_all_multiroom_status()
        else:
            self.logger.debug("Device %s not found for removal.", udn)

    async def discover_and_add_devices(self) -> None:
        """Discover devices using UPnP and add them."""
        self.logger.info("Starting UPnP discovery for WiiM devices...")
        discovered = await async_discover_wiim_devices_upnp(self.session)
        for dev in discovered:
            if dev.udn not in self._devices:
                await self.add_device(dev) # This calls async_update_all_multiroom_status for each
        self.logger.info("Discovery finished. Total managed devices: %s", len(self._devices))
        # Ensure a final full update after discovery is done
        await self.async_update_all_multiroom_status()


    async def async_update_multiroom_status(self, leader_device: WiimDevice) -> None:
        """
        Updates the multiroom status for a group where leader_device is the leader.
        Multiroom grouping is typically done via HTTP API for Linkplay/WiiM.
        """
        if not leader_device._http_api:
            self.logger.debug("Leader device %s has no HTTP API, cannot update multiroom status.", leader_device.name)
            # Clear any existing group info for this leader if API is gone
            if leader_device.udn in self._multiroom_groups:
                del self._multiroom_groups[leader_device.udn]
            return

        try:
            # Query the leader for its multiroom list
            response = await leader_device._http_request(WiimHttpCommand.MULTIROOM_LIST)
            
            # Linkplay Multiroom_List structure is often:
            # {"num":X, "slaves":[{"name":"...", "ip":"...", "uuid":"..."}]}
            num_followers = int(response.get(MultiroomAttribute.NUM_FOLLOWERS, 0))
            follower_udns: List[str] = []

            if num_followers > 0:
                slaves_list = response.get(MultiroomAttribute.FOLLOWER_LIST, [])
                if isinstance(slaves_list, list):
                    for slave_info in slaves_list:
                        if isinstance(slave_info, dict):
                            # The UUID in MULTIROOM_LIST might be a shortened/modified form
                            # You need a reliable way to map it back to the full UDN
                            slave_uuid_short = slave_info.get(MultiroomAttribute.UUID) 
                            
                            if slave_uuid_short:
                                # This is a critical helper to convert short UUID from multiroom list
                                # back to the full UDN (uuid:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
                                full_follower_udn = self._restore_full_udn(slave_uuid_short, leader_device.udn)
                                
                                if full_follower_udn:
                                    follower_device = self.get_device(full_follower_udn)
                                    if follower_device:
                                        follower_udns.append(full_follower_udn)
                                    else:
                                        self.logger.warning("Multiroom follower UDN %s for leader %s not found in managed devices.",
                                                            full_follower_udn, leader_device.name)
                                else:
                                    self.logger.warning("Could not restore full UDN from short UUID %s for leader %s.",
                                                        slave_uuid_short, leader_device.name)
                            else:
                                self.logger.warning("Slave info missing UUID: %s", slave_info)
                        else:
                            self.logger.warning("Unexpected slave_info format in multiroom list: %s", slave_info)
                else:
                    self.logger.warning("Follower list is not a list: %s", slaves_list)
            else:
                follower_udns = []

            # Update the controller's internal _multiroom_groups map
            self._multiroom_groups[leader_device.udn] = follower_udns
            self.logger.info("Updated multiroom status for leader %s (UDN: %s): %s followers (%s)",
                             leader_device.name, leader_device.udn, len(follower_udns), follower_udns)

        except WiimRequestException as e:
            self.logger.warning("Failed to get multiroom list for leader %s (UDN: %s): %s", leader_device.name, leader_device.udn, e)
            # If request fails, assume this device is no longer a leader of a group
            if leader_device.udn in self._multiroom_groups:
                del self._multiroom_groups[leader_device.udn]
        except (ValueError, TypeError, KeyError) as e:
            self.logger.warning("Error parsing multiroom data for leader %s (UDN: %s): %s", leader_device.name, leader_device.udn, e, exc_info=True)
            if leader_device.udn in self._multiroom_groups:
                del self._multiroom_groups[leader_device.udn]

    def _restore_full_udn(self, short_uuid: str, leader_udn: str) -> str | None:
        """Restores a full UDN (uuid:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)"""
        prefix = short_uuid[:8]
        part1 = short_uuid[0:8]
        part2 = short_uuid[8:12]
        part3 = short_uuid[12:16]
        part4 = short_uuid[16:20]
        part5 = short_uuid[20:] + prefix # This implies cleaned is 20 chars long, and prefix is first 8.
        full_uuid = f"uuid:{part1}-{part2}-{part3}-{part4}-{part5}"
        return full_uuid

    async def async_update_all_multiroom_status(self) -> None:
        """Updates multiroom status for all managed devices that could be leaders."""
        self.logger.debug("Updating all multiroom statuses...")
        
        # Capture current leaders before clearing, might be useful for debugging
        # current_leaders_snapshot = list(self._multiroom_groups.keys())
        
        # Clear existing groups first before re-populating
        self._multiroom_groups.clear()

        # Iterate over a *copy* of self._devices.values() to prevent "dictionary changed size during iteration"
        # This ensures the loop is stable even if add/remove devices occur concurrently.
        for device in list(self._devices.values()): # IMPORTANT: Iterate over a copy
            # Attempt to update multiroom status for each device.
            # async_update_multiroom_status will determine if the device is a leader
            # and populate _multiroom_groups accordingly.
            await self.async_update_multiroom_status(device)

        # After populating all groups, refine the _multiroom_groups to ensure consistency.
        # This step helps if a device might report itself as a leader while also being a follower
        # of another group. Only actual leaders should remain keys in _multiroom_groups.
        all_followers_being_led = set()
        for leader_udn, follower_udns in self._multiroom_groups.items():
            for follower_udn in follower_udns:
                all_followers_being_led.add(follower_udn)

        final_groups = {}
        for leader_udn, follower_udns in self._multiroom_groups.items():
            # If a device is listed as a leader, but also appears as a follower in another group,
            # it should not be considered a leader. This is a consistency check.
            if leader_udn not in all_followers_being_led:
                final_groups[leader_udn] = follower_udns
            else:
                self.logger.debug("Device %s was a leader but is also a follower; removing from leader list.", leader_udn)
        
        self._multiroom_groups = final_groups
        self.logger.info("Finished updating all multiroom statuses. Current groups: %s", self._multiroom_groups)


    def get_device_group_info(self, device_udn: str) -> Optional[Dict[str, str]]:
        """
        Get the group role (leader/follower/standalone) and leader UDN for a given device.
        Returns: {"role": "leader"|"follower"|"standalone", "leader_udn": leader's UDN}
        """
        if device_udn in self._multiroom_groups:
            # Check if this device is explicitly listed as a leader
            return {"role": "leader", "leader_udn": device_udn}
        
        # Check if it's a follower of any existing group
        for leader_udn, follower_udns in self._multiroom_groups.items():
            if device_udn in follower_udns:
                return {"role": "follower", "leader_udn": leader_udn}
        
        # If the device is known to the controller but not in any group
        if self.get_device(device_udn):
            return {"role": "standalone", "leader_udn": device_udn}
        
        return None # Device not managed or not part of any group


    def get_group_members(self, device_udn: str) -> List[WiimDevice]:
        """
        Get all members of the group the given device belongs to (including itself).
        Returns a list of WiimDevice objects.
        """
        leader_udn: Optional[str] = None
        group_members_udns: List[str] = []

        # Find the group this device belongs to
        if device_udn in self._multiroom_groups:
            # This device is a leader
            leader_udn = device_udn
            group_members_udns = [leader_udn] + self._multiroom_groups[leader_udn]
        else:
            # Check if it's a follower
            for l_udn, f_udns in self._multiroom_groups.items():
                if device_udn in f_udns:
                    leader_udn = l_udn
                    group_members_udns = [leader_udn] + f_udns
                    break
        
        if not group_members_udns:
            # Device is standalone or not found
            device = self.get_device(device_udn)
            return [device] if device else []

        # Convert UDNs to WiimDevice objects
        result_devices: List[WiimDevice] = []
        for udn in set(group_members_udns): # Use set to handle potential duplicates
            device_obj = self.get_device(udn)
            if device_obj:
                result_devices.append(device_obj)
        return result_devices


    async def async_join_group(self, leader_udn: str, follower_udn: str) -> None:
        """Make follower_udn join the group led by leader_udn."""
        leader = self.get_device(leader_udn)
        follower = self.get_device(follower_udn)

        if not leader or not follower:
            raise WiimException("Leader or follower device not found.")
        if not leader._http_api or not follower._http_api:
            raise WiimException("HTTP API not available for leader or follower.")
        
        # Ensure leader's IP is available for the command
        leader_ip_for_cmd = leader.ip_address
        if not leader_ip_for_cmd:
            raise WiimException(f"Cannot determine leader's IP for JoinGroup command for {leader.name}")
        
        # Helper to format UDN for Linkplay commands (removes 'uuid:' and hyphens, and the suffix part if it's part of the UDN)
        def format_udn_for_command(udn: str) -> str:
            if udn.startswith("uuid:"):
                udn = udn[5:]
            udn = udn.replace("-", "")
            # Assuming the last 8 chars might be a specific suffix to remove if it's added by the device
            # This is a heuristic; verify with Linkplay API docs if needed.
            if len(udn) > 12 and udn.endswith(udn[-12:-4]): # If the last 8 chars match the 8 chars before that
                 return udn[:-8] # Remove the last 8 chars
            return udn

        try:
            # The command MULTIROOM_JOIN is executed on the FOLLOWER device.
            # Format: "ConnectMasterAp:JoinGroupMaster:{leader_ip}:{leader_udn_short}"
            formatted_leader_udn = format_udn_for_command(leader.udn)
            join_command_url = WiimHttpCommand.MULTIROOM_JOIN.format(leader_ip_for_cmd, formatted_leader_udn)
            
            self.logger.info("Follower %s sending join command to leader %s: %s", follower.name, leader.name, join_command_url)
            await follower._http_command_ok(join_command_url)
            self.logger.info("Device %s successfully sent join command to leader %s", follower.name, leader.name)
            
            # After joining, update the leader's multiroom status to reflect the new group member
            await self.async_update_multiroom_status(leader) 
        except WiimRequestException as e:
            self.logger.warning("Failed to make %s join %s: %s", follower.name, leader.name, e)
            raise

    async def async_ungroup_device(self, device_udn: str) -> None:
        """Make a device leave its current group. If it's a leader, the whole group is disbanded."""
        device = self.get_device(device_udn)
        if not device or not device._http_api:
            raise WiimException("Device not found or HTTP API unavailable.")

        group_info = self.get_device_group_info(device_udn)
        original_leader_to_update: WiimDevice | None = None
        self.logger.info("Gourp info %s, device uid = %s", group_info, device_udn)

        if group_info and group_info.get("role") == "leader":
            # Device is a leader, ungroup the whole group
            self.logger.info("Ungrouping multiroom group led by %s (UDN: %s)", device.name, device.udn)
            await device._http_command_ok(WiimHttpCommand.MULTIROOM_UNGROUP)
            # Remove from internal groups map immediately
            if device_udn in self._multiroom_groups:
                del self._multiroom_groups[device_udn]
            original_leader_to_update = device # This device needs its status updated
        elif group_info and group_info.get("role") == "follower":
            # Device is a follower, kick it from the group (leader executes kick)
            leader_udn_of_follower = group_info.get("leader_udn")
            leader_of_this_device = self.get_device(leader_udn_of_follower)
            
            if not leader_of_this_device:
                raise WiimException(f"Leader {leader_udn_of_follower} for follower {device.name} not found.")
            if not leader_of_this_device._http_api:
                raise WiimException(f"Leader {leader_of_this_device.name} HTTP API unavailable for Kick command.")

            follower_ip_for_cmd = device.ip_address
            if not follower_ip_for_cmd:
                 raise WiimException(f"Cannot determine follower's IP for Kick command for {device.name}")
            
            self.logger.info("Kicking device %s from group led by %s", device.name, leader_of_this_device.name)
            await leader_of_this_device._http_command_ok(WiimHttpCommand.MULTIROOM_KICK, follower_ip_for_cmd)
            original_leader_to_update = leader_of_this_device # Leader's status needs update
        else:
            self.logger.info("Device %s is not part of any multiroom group, no ungroup action needed.", device.name)
            return # Not in a group

        # After any ungroup operation, update the affected leader's status (or all if no specific leader)
        if original_leader_to_update:
            await self.async_update_multiroom_status(original_leader_to_update)
        else:
            # Fallback if ungrouping a standalone or complex scenario.
            # This should ideally be caught by get_device_group_info.
            self.logger.warning("Ungrouped device %s, but no specific leader to update. Updating all multiroom status.", device.name)
            await self.async_update_all_multiroom_status()

