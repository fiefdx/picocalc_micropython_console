# lib/ap.py
"""
MicroPython Access-Point helper.

All configuration values are handed to the driver as **bytes**.  No extra
lookup tables are required - we simply encode the Python strings to UTF-8
bytes before calling the WLAN API.
"""

import network

class AP:
    # ------------------------------------------------------------------
    # Single WLAN object – AP_IF = 1 on ESP32/ESP8266
    # ------------------------------------------------------------------
    wlan = network.WLAN(network.AP_IF)

    # Remember the last configuration (bytes) – useful for a "restart".
    ssid     = b""
    password = b""
    authmode = network.AUTH_OPEN
    channel  = 6                     # default Wi-Fi channel

    # ------------------------------------------------------------------
    # Activate / deactivate
    # ------------------------------------------------------------------
    @classmethod
    def active(cls, flag: bool) -> None:
        """Power the AP interface on (True) or off (False)."""
        cls.wlan.active(flag)

    @classmethod
    def is_active(cls) -> bool:
        """True if the AP interface is powered on."""
        return cls.wlan.active()

    # ------------------------------------------------------------------
    # Low-level configuration – everything is a *bytes* object.
    # ------------------------------------------------------------------
    @classmethod
    def _choose_auth(cls, pwd: bytes) -> int:
        """WPA-WPA2 if a password is supplied, otherwise open."""
        return network.AUTH_WPA_WPA2_PSK if pwd else network.AUTH_OPEN

    @classmethod
    def configure(
        cls,
        ssid: bytes,
        password: bytes = b"",
        channel: int = 6,
    ) -> None:
        """
        Store the config and push it to the hardware.

        Parameters
        ----------
        ssid      : bytes - network name (ESSID)
        password  : bytes - WPA/WPA2 password (empty = open)
        channel   : int   - Wi-Fi channel (default = 6)
        """
        cls.ssid     = ssid
        cls.password = password
        cls.channel  = channel
        cls.authmode = cls._choose_auth(password)

        cls.wlan.config(
            essid    = ssid,
            password = password,
            authmode = cls.authmode,
            channel  = channel,
        )
        # Give the AP a sensible static address (feel free to change).
        cls.wlan.ifconfig(
            ("192.168.4.1", "255.255.255.0",
             "192.168.4.1", "8.8.8.8")
        )

    # ------------------------------------------------------------------
    # Public high-level actions (still pure-byte handling internally)
    # ------------------------------------------------------------------
    @classmethod
    def start(
        cls,
        ssid: str,
        password: str = "",
        channel: int = 6,
    ) -> None:
        """
        Power on the AP and apply the configuration.

        `ssid` and `password` may be ordinary Python strings - they are
        encoded to UTF-8 bytes before being handed to the driver.
        """
        if not cls.wlan.active():
            cls.wlan.active(True)            # turn the interface on
        b_ssid = ssid.encode("utf-8")
        b_pwd  = password.encode("utf-8")
        cls.configure(b_ssid, b_pwd, channel)

    @classmethod
    def stop(cls) -> None:
        """Deactivate the AP."""
        cls.wlan.active(False)

    @classmethod
    def status(cls) -> dict:
        """
        Return a dictionary that holds the current AP state.

        Keys
        ----
        * active    - bool
        * essid     - bytes or None
        * authmode  - int or None
        * ifconfig  - tuple of four strings or None
        * stations  - list of (mac, ip) tuples or None
        """
        if not cls.wlan.active():
            return {
                "active": False,
                "essid": None,
                "authmode": None,
                "ifconfig": None,
                "stations": None,
            }

        return {
            "active": True,
            "essid": cls.wlan.config("essid"),
            "authmode": cls.wlan.config("authmode"),
            "ifconfig": cls.wlan.ifconfig(),
            "stations": cls.wlan.status("stations"),
        }
