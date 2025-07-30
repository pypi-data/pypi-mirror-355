from __future__ import annotations

import socket

import psutil
from rich import box
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual.widget import Widget

from .__about__ import __version__
from ._helpers import sizeof_fmt
from .braille_stream import BrailleStream

# def get_ip():
#     s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     s.connect(("8.8.8.8", 80))
#     ip = s.getsockname()[0]
#     s.close()
#     return ip


def _autoselect_interface():
    """
    TCP/IP supports types of network interfaces:

    - Standard Ethernet Version 2 (en)
    - IEEE 802.3 (et)
    - Token-ring (tr)
    - Serial Line Internet Protocol (SLIP)
    - Loopback (lo)
    - FDDI
    - Serial Optical (so)
    - ATM (at)
    - Point-to-Point Protocol (PPP)
    - Virtual IP Address (vi)
    - Apple NCM Private Interface(anpi)
    - Apple Specific for VPN and Back to My Mac (utun)
    - Bonded Interfaces (bond)
    - VPN Interfaces (tun/tap)
    - ISDN (Integrated Services Digital Network)
    - VLAN Interfaces (vlan)
    - Virtual Machine Interfaces (vmx, vnet, etc.)
    - MPLS (Multiprotocol Label Switching)
    - Fibre Channel over Ethernet (FCoE)
    - LTE/5G (cellular)
    - InfiniBand (ib)
    - Virtual Ethernet (veth)
    - Bluetooth (bt)
    - Wi-Fi (Wireless LAN Interface) (wlan)
    """
    stats = psutil.net_if_stats()
    score_dict = {}
    for name, stats in stats.items():
        if not stats.isup:
            score_dict[name] = 0
        elif (
            # On Unix, we have `lo`, on Windows `Loopback Pseudo-Interface k`
            # and `Local Area Connection k` (the latter is valid)
            name.startswith("lo")
            or name.lower().startswith("loopback")
            or name.lower().startswith("docker")
            or name.lower().startswith("anpi")
        ):
            score_dict[name] = 1
        elif name.lower().startswith("fw") or name.lower().startswith("Bluetooth"):
            # firewire <https://github.com/nschloe/tiptop/issues/45#issuecomment-991884364>
            # or bluetooth
            score_dict[name] = 2
        elif name.lower().startswith("en"):
            # Preference given to Standard Ethernet Version 2.
            # TODO: Make this dynamic by detecting network states and activity.
            score_dict[name] = 4
        else:
            score_dict[name] = 3

    # Amongst all keys with max score, get the alphabetically first.
    # This is to prefer en0 over en5, <https://github.com/nschloe/tiptop/issues/81>.
    max_score = max(score_dict.values())
    max_keys = [key for key, score in score_dict.items() if score == max_score]
    return sorted(max_keys)[0]


class Net(Widget):
    def __init__(self, interface: str | None = None):
        self.interface = _autoselect_interface() if interface is None else interface
        self.sot_string = f"sot v{__version__}"
        super().__init__()

    def on_mount(self):
        self.down_box = Panel(
            "",
            title="▼ down",
            title_align="left",
            style="aquamarine3",
            width=20,
            box=box.SQUARE,
        )
        self.up_box = Panel(
            "",
            title="▲ up",
            title_align="left",
            style="yellow",
            width=20,
            box=box.SQUARE,
        )
        self.table = Table(expand=True, show_header=False, padding=0, box=None)
        # Add ratio 1 to expand that column as much as possible
        self.table.add_column("graph", no_wrap=True, ratio=1)
        self.table.add_column("box", no_wrap=True, width=20)
        self.table.add_row("", self.down_box)
        self.table.add_row("", self.up_box)

        self.group = Group(self.table, "", "")
        self.panel = Panel(
            self.group,
            title=f"[b]Net[/] - {self.interface}",
            # border_style="red3",
            border_style="bright_black",
            title_align="left",
            box=box.SQUARE,
            subtitle=self.sot_string,
            subtitle_align="right",
        )

        self.last_net = None
        self.max_recv_bytes_s = 0
        self.max_recv_bytes_s_str = ""
        self.max_sent_bytes_s = 0
        self.max_sent_bytes_s_str = ""

        self.recv_stream = BrailleStream(20, 5, 0.0, 1.0e6)
        self.sent_stream = BrailleStream(20, 5, 0.0, 1.0e6, flipud=True)

        self.refresh_ips()
        self.refresh_panel()

        self.interval_s = 2.0
        self.set_interval(self.interval_s, self.refresh_panel)
        self.set_interval(60.0, self.refresh_ips)

    def refresh_ips(self):
        addrs = psutil.net_if_addrs()[self.interface]
        ipv4 = []
        for addr in addrs:
            # ipv4?
            if addr.family == socket.AF_INET:
                ipv4.append(addr.address + " / " + addr.netmask)
        ipv6 = []
        for addr in addrs:
            # ipv6?
            if addr.family == socket.AF_INET6:
                ipv6.append(addr.address)

        ipv4 = "\n      ".join(ipv4)
        ipv6 = "\n      ".join(ipv6)

        # Textual 3.4.0+: Group renderables can be modified in place
        if len(self.group.renderables) >= 3:
            self.group.renderables[1] = f"[b]IPv4:[/] {ipv4}"
            self.group.renderables[2] = f"[b]IPv6:[/] {ipv6}"

    # would love to collect data upon each render(), but render is called too often
    # <https://github.com/willmcgugan/textual/issues/162>
    def refresh_panel(self):
        net = psutil.net_io_counters(pernic=True)[self.interface]
        if self.last_net is None:
            recv_bytes_s_string = ""
            sent_bytes_s_string = ""
        else:
            recv_bytes_s = (net.bytes_recv - self.last_net.bytes_recv) / self.interval_s
            recv_bytes_s_string = sizeof_fmt(recv_bytes_s, fmt=".1f") + "/s"
            sent_bytes_s = (net.bytes_sent - self.last_net.bytes_sent) / self.interval_s
            sent_bytes_s_string = sizeof_fmt(sent_bytes_s, fmt=".1f") + "/s"

            if recv_bytes_s > self.max_recv_bytes_s:
                self.max_recv_bytes_s = recv_bytes_s
                self.max_recv_bytes_s_str = sizeof_fmt(recv_bytes_s, fmt=".1f") + "/s"

            if sent_bytes_s > self.max_sent_bytes_s:
                self.max_sent_bytes_s = sent_bytes_s
                self.max_sent_bytes_s_str = sizeof_fmt(sent_bytes_s, fmt=".1f") + "/s"

            self.recv_stream.add_value(recv_bytes_s)
            self.sent_stream.add_value(sent_bytes_s)

        self.last_net = net

        total_recv_string = sizeof_fmt(net.bytes_recv, sep=" ", fmt=".1f")
        total_sent_string = sizeof_fmt(net.bytes_sent, sep=" ", fmt=".1f")

        self.down_box.renderable = "\n".join(
            [
                f"{recv_bytes_s_string}",
                f"max   {self.max_recv_bytes_s_str}",
                f"total {total_recv_string}",
            ]
        )
        self.up_box.renderable = "\n".join(
            [
                f"{sent_bytes_s_string}",
                f"max   {self.max_sent_bytes_s_str}",
                f"total {total_sent_string}",
            ]
        )
        self.refresh_graphs()

        self.refresh()

    def refresh_graphs(self):
        # Textual 3.4.0+: Updated table cell access pattern
        if hasattr(self.table.columns[0], "_cells"):
            self.table.columns[0]._cells[0] = Text(
                "\n".join(self.recv_stream.graph), style="aquamarine3"
            )
            self.table.columns[0]._cells[1] = Text(
                "\n".join(self.sent_stream.graph), style="yellow"
            )
        else:
            # Fallback: recreate table rows
            self.table._clear()
            self.table.add_row(
                Text("\n".join(self.recv_stream.graph), style="aquamarine3"),
                self.down_box,
            )
            self.table.add_row(
                Text("\n".join(self.sent_stream.graph), style="yellow"), self.up_box
            )

    def render(self):
        return self.panel

    async def on_resize(self, event):
        width = self.size.width - 25
        self.sent_stream.reset_width(width)
        self.recv_stream.reset_width(width)
        self.refresh_graphs()
