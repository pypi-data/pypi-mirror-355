import re
import json
import time
import datetime
import hashlib
import subprocess
import cloudscraper
from .IPTV import IPTV


class MacPortal(IPTV):
    def __init__(self, base_url, mac, sn="", device1="", device2="", signature="", post_url="", export=False):
        # important input
        self.base_url   = base_url
        self.mac        = mac
        self.sn         = sn
        self.device1    = device1
        self.device2    = device2
        self.signature  = signature
        self.post_url   = post_url
        # fetched constants
        self.ver = ""
        self.metrics = ""
        self.prehash = ""
        self.hw_version_2 = ""
        # obtained string
        self.version = ""
        self.token = ""
        self.random = ""
        self.not_valid = ""
        # obtained dict
        self.handshake_data = {}
        self.get_profile_data = {}
        self.get_main_info_data = {}
        # obtained database
        self.itv_genres = []
        self.vod_categories = []
        self.series_categories = []
        self.all_channels = {}
        # stb initialisation
        super().__init__(self.base_url, self.post_url, export)
        self.cache = {
            "category_id" : "",
            "category" : "",
            "channel_id" : "",
            "channel" : "",
            "epg" : "",
            "timestamp" : "",
            "link_data" : "",
            "link" : "",
            "name" : ""
        }
        # stb initialised
    
    
    def gen_input(self):
        super().gen_input()
        if self.base_url[-2:] == "/c":
            self.base_url = self.base_url[:-2]
        if self.sn == "":
            self.sn = hashlib.md5(self.mac.encode()).hexdigest().upper()[:13]
        if self.device2 == "":
            self.device2 = self.device1
        if self.signature == "":
            signature_input = self.mac + self.sn + self.device1 + self.device2 + self.base_url
            self.signature = hashlib.sha256(signature_input.encode()).hexdigest().upper()
        if self.post_url == "":
            self.post_url = "/server/load.php?"
        self.portal_url = self.base_url + self.post_url
        return True
    
    def gen_scraper(self):
        super().gen_scraper()
        self.scraper.headers.update({
            "User-Agent": "Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp ver: 2 rev: 250 Safari/533.3",
            "Referer": f"{self.base_url}/c/index.html",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Pragma": "no-cache",
            "X-User-Agent": f"Model: {self.stb_type}; Link: WiFi",
            "Host": f"{self.hostname}",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "Keep-Alive",
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        })
        self.scraper.cookies.set("mac", self.mac, domain=self.hostname)
        self.scraper.cookies.set("stb_lang", self.lang, domain=self.hostname)
        self.scraper.cookies.set("timezone", self.timezone, domain=self.hostname)
        return True
    
    def gen_request(self, method, payload=None, url=""):
        r = super().gen_request(method, payload, url)
        if self.status=="invalid" or self.status=="expired":
            print(f"Current portal status: {self.status}\nRetrying to load Profile...")
            self.load_profile(db=False)
        if self.status=="invalid" or self.status=="expired":
            print(f"Could not send request for portal; Status: {self.status}")
        if self.status=="on":
            if r.text.lower().startswith("authorization failed"):
                print("Authorization failed. Retrying...")
                self.load_profile(db=False)
                r = super().gen_request(method, payload, url)
            if r.text.lower().startswith("authorization failed"):
                print("Authorization failed again.")
        try:
            r.json()
        except:
            r.json = lambda: {
                "__portal_status": self.status,
                "_fallback_raw_text": r.text,
                "_status_code": r.status_code
            }
        return r
    
    
    def call_core_methods(self,keylist=[],**kwargs):
        if isinstance(keylist, str):
            keylist = [keylist]
        rlist = []
        print(self.dsh)
        print("Calling core methods for the STB Client:-")
        print("NOTE: These methods are in majority clients but not ALL")
        payloads = {
            "auth_dialog" : {
                "type"      : "stb",
                "action"    : "do_auth",
                "login"     : kwargs.get("login", ""),
                "password"  : kwargs.get("password", ""),
                "device_id" : self.device1,
                "device_id2": self.device2
            },
            "get_modules" : {
                "type"      : "stb",
                "action"    : "get_modules"
            },
            "get_localization" : {
                "type"      : "stb",
                "action"    : "get_localization"
            },
            "preload_images" : {
                "type"      : "stb",
                "action"    : "get_preload_images",
                "gmode"     : kwargs.get("gmode", "")
            },
            "portal_status_interval" : {
                "type"      : "stb",
                "action"    : "check_portal_status"
            },
            "remount_storages" : {
                "type"      : "stb",
                "action"    : "get_storages"
            },
            
            "load_channels" : {
                "type"      : "itv",
                "action"    : "get_all_channels",
                "force_ch_link_check": kwargs.get("force_ch_link_check", "false")
            },
            "load_fav_channels" : {
                "type"      : "itv",
                "action"    : "get_all_fav_channels",
                "fav"       : kwargs.get("fav", "1"),
                "force_ch_link_check" : kwargs.get("force_ch_link_check", "false")
            },
            "load_fav_itv" : {
                "type"      : "itv",
                "action"    : "get_fav_ids",
                "force_ch_link_check" : kwargs.get("force_ch_link_check", "false")
            },
            "load_recordings" : {
                "type"      : "remote_pvr",
                "action"    : "get_active_recordings"
            },
            "load_radio_channel" : {
                "type"      : "radio",
                "action"    : "get_channel_by_id",
                "number"    : kwargs.get("number", "")
            },
            "log_stream_error" : {
                "type"      : "stb",
                "action"    : "set_stream_error",
                "ch_id"     : kwargs.get("ch_id", ""),
                "event"     : kwargs.get("event", "")
            },
            "epg_loader" : {
                "type"      : "itv",
                "action"    : "get_epg_info",
                "period"    : kwargs.get("period", "3")
            },
            "advert" : {
                "type"      : "stb",
                "action"    : "get_ad",
                "video_mode": kwargs.get("video_mode", "")
            },
        }
        for key in keylist:
            payload = payloads[key]
            payload["JsHttpRequest"] = "1-xml"
            r = self.gen_request("post",payload)
            data = r.json().get("js", {})
            print(f"→ {key} Output Length:", len(r.text))
            self.gen_logs(r, f"call_core_methods {key}.js", True)
            rlist.append(r)
        print(self.dsh)
        return rlist
    
    
    def gen_ver(self):
        image_desc = f"ImageDescription: {self.image_desc}; "
        image_date = f"ImageDate: {self.image_date}; "
        portal_ver = f"PORTAL version: {self.version}; "
        api_ver = f"API Version: JS API version: {self.js_api_ver}; STB API version: {self.stb_api_ver}; "
        player_engine_ver = f"Player Engine version: {self.player_engine_ver}"
        self.ver = image_desc+image_date+portal_ver+api_ver+player_engine_ver
        return self.ver
    
    def gen_metrics(self):
        self.metrics = {
            "mac" : self.mac,
            "type" : self.client_type,
            "model" : self.stb_type,
            "uid" : self.device1,
            "random" : self.random
        }
        return self.metrics
    
    def gen_prehash(self):
        prehash_input = self.stb_type + self.gen_ver()[:56] + self.version + self.token + self.random
        self.prehash = hashlib.sha1(prehash_input.encode()).hexdigest()
        return self.prehash
    
    def gen_hw_version_2(self):
        metrics_json = json.dumps(self.metrics)
        hw_version_2_input = metrics_json + self.token
        self.hw_version_2 = hashlib.sha1(hw_version_2_input.encode()).hexdigest()
        return self.hw_version_2
    
    
    def g_version(self):
        r = self.gen_request("get",url=f"{self.base_url}/c/version.js")
        match = re.search(r"var ver = '([^']+)'", r.text)
        self.version = match.group(1)
        print("→ version.js fetched, portal version =", self.version)
        self.gen_logs(r, "get version.js")
        return self.version
    
    def g_xpcom(self):
        r = self.gen_request("get",url=f"{self.base_url}/c/xpcom.common.js")
        print("→ xpcom.common.js fetched, length =", len(r.text), "bytes")
        self.gen_logs(r, "get xpcom.common.js")
        return r.text
    
    def g_initial(self, dsh=True):
        if dsh: print(self.dsh)
        print("GET initial request for initialisation response")
        self.g_version()
        self.g_xpcom()
        if dsh: print(self.dsh)
    
    
    def p_handshake(self):
        payload = {
            "type": "stb",
            "action": "handshake",
            "token": self.token,
            "JsHttpRequest": "1-xml"
        }
        r = self.gen_request("post",payload)
        self.handshake_data = self.gen_jsondata(r,{},dict)
        self.token = self.handshake_data.get("token", "")
        self.random = self.handshake_data.get("random", "")
        self.not_valid = self.handshake_data.get("not_valid", "0")
        self.scraper.headers.update({
            "Authorization": f"Bearer {self.token}"
        })
        print("→ Token obtained:", self.token)
        print("→ Random obtained:", self.random)
        self.gen_logs(r, "post handshake.js", True)
        return self.handshake_data
    
    def p_get_profile(self):
        self.gen_ver()
        self.gen_metrics()
        self.gen_prehash()
        self.gen_hw_version_2()
        metrics_json = json.dumps(self.metrics)
        timestamp = str(int(time.time()))
        payload = {
            "type":             "stb",
            "action":           "get_profile",
            "hd":               self.hd,
            "ver":              self.ver,
            "num_banks":        self.num_banks,
            "sn":               self.sn,
            "stb_type":         self.stb_type,
            "client_type":      self.client_type,
            "image_version":    self.image_version,
            "video_out":        self.video_out,
            "device_id":        self.device1,
            "device_id2":       self.device2,
            "signature":        self.signature,
            "auth_second_step": "1",
            "hw_version":       self.hw_version,
            "not_valid_token":  self.not_valid,
            "metrics":          metrics_json,
            "hw_version_2":     self.hw_version_2,
            "timestamp":        timestamp,
            "api_signature":    self.api_signature,
            "prehash":          self.prehash,
            "JsHttpRequest":    "1-xml"
        }
        r = self.gen_request("post",payload)
        self.get_profile_data = self.gen_jsondata(r,{},dict)
        print("→ Profile received, total keys:", len(self.get_profile_data))
        self.gen_logs(r, "post get_profile.js", True)
        return self.get_profile_data
    
    def p_get_main_info(self):
        payload = {
            "type": "account_info",
            "action": "get_main_info",
            "JsHttpRequest": "1-xml"
        }
        r = self.gen_request("post",payload)
        self.get_main_info_data = self.gen_jsondata(r,{},dict)
        print("→ Main Info:", self.get_main_info_data)
        self.gen_logs(r, "post get_main_info.js", True)
        return self.get_main_info_data
    
    def p_initial(self, dsh=True):
        if dsh: print(self.dsh)
        print("POST initial request for initialisation response")
        self.p_handshake()
        self.p_get_profile()
        self.p_get_main_info()
        if dsh: print(self.dsh)
    
    
    def db_itv_genres(self):
        payload = {
            "type": "itv",
            "action": "get_genres",
            "JsHttpRequest": "1-xml"
        }
        r = self.gen_request("post",payload)
        self.itv_genres = self.gen_jsondata(r,[],list)
        print("→ Total itv genres:", len(self.itv_genres))
        self.gen_logs(r, "db itv_genres.js", True)
        return self.itv_genres
    
    def db_vod_categories(self):
        payload = {
            "type": "vod",
            "action": "get_categories",
            "JsHttpRequest": "1-xml"
        }
        r = self.gen_request("post",payload)
        self.vod_categories = self.gen_jsondata(r,[],list)
        print("→ Total vod categories:", len(self.vod_categories))
        self.gen_logs(r, "db vod_categories.js", True)
        return self.vod_categories
    
    def db_series_categories(self):
        payload = {
            "type": "series",
            "action": "get_categories",
            "JsHttpRequest": "1-xml"
        }
        r = self.gen_request("post",payload)
        self.series_categories = self.gen_jsondata(r,[],list)
        print("→ Total series categories:", len(self.series_categories))
        self.gen_logs(r, "db series_categories.js", True)
        return self.series_categories
    
    def db_all_channels(self):
        payload = {
            "type": "itv",
            "action": "get_all_channels",
            "JsHttpRequest": "1-xml"
        }
        r = self.gen_request("post",payload)
        self.all_channels = self.gen_jsondata(r,{},dict)
        if "total_items" not in self.all_channels:
            print("→ Failed to fetch channels")
            self.all_channels = {}
        else:
            print("→ Total channels:", self.all_channels["total_items"])
            all_channels = self.all_channels["data"] if "data" in self.all_channels else []
            self.all_channels = {channel["id"]: channel for channel in all_channels}
        self.gen_logs(r, "db all_channels.js", True)
        return self.all_channels
    
    
    def load_initial(self, dsh=True):
        if dsh: print(self.dsh)
        if dsh: print(self.dsh)
        self.g_initial(dsh=False)
        print(self.dsh)
        self.p_initial(dsh=False)
        if dsh: print(self.dsh)
        if dsh: print(self.dsh)
    
    def load_database(self, dsh=True):
        if dsh: print(self.dsh)
        if dsh: print(self.dsh)
        print("POST request to obtain database response")
        if dsh: print(self.dsh)
        self.db_itv_genres()
        self.db_vod_categories()
        self.db_series_categories()
        self.db_all_channels()
        if dsh: print(self.dsh)
        if dsh: print(self.dsh)
    
    def load_profile(self, db=None):
        print(self.dsh)
        print(self.dsh)
        self.status = "off"
        print("LOADING PROFILE...")
        old_length = len(self.r_list)
        print(self.dsh)
        self.load_initial(dsh=False)
        print(self.dsh)
        for r in self.r_list[old_length:]:
            text = r.text
            if text.lower().startswith("authorization failed"):
                self.status = "invalid"
                break
        if "end_date" in self.get_main_info_data and "(" in self.get_main_info_data["end_date"]:
            end_date = self.get_main_info_data["end_date"].split("(")[1].split(" ")[0]
            if end_date.startswith("-"):
                self.status = "expired"
        if self.status=="invalid" or self.status=="expired":
            print(f"{self.hostname} profile could not be loaded; Status: {self.status}")
            print(self.dsh)
            print(self.dsh)
            return
        self.status = "on"
        if db is True:
            self.load_database(dsh=False)
            print(self.dsh)
        elif db is None:
            self.db_all_channels()
            print(self.dsh)
        print(f"{self.hostname} profile successfully loaded; Status: {self.status}")
        print(self.dsh)
        print(self.dsh)
    
    
    def get_series_list(self, category_id, by_page=False, **kwargs):
        series_list = []
        series_list_by_page = []
        page = 1
        total, per_page, max_page = None, None, None
        while True:
            print(f"Fetching series for {category_id} at page {page}")
            payload = {
                "type": "series",
                "action": "get_ordered_list",
                "category": category_id,
                "movie_id": kwargs.get("movie_id","0"),
                "season_id": kwargs.get("season_id","0"),
                "episode_id": kwargs.get("episode_id","0"),
                "force_ch_link_check": kwargs.get("force_ch_link_check","0"),
                "fav": kwargs.get("fav","0"),
                "sortby": kwargs.get("sortby","added"),
                "hd": kwargs.get("hd","0"),
                "not_ended": kwargs.get("not_ended","0"),
                "p": page,
                "from_ch_id": kwargs.get("from_ch_id","0"),
                "JsHttpRequest": "1-xml"
            }
            r = self.gen_request("post",payload)
            series_data = self.gen_jsondata(r,{},dict)
            if total is None and "total_items" in series_data:
                total = series_data["total_items"]
            if per_page is None and "max_page_items" in series_data:
                per_page = series_data["max_page_items"]
            if total is not None and per_page is not None and max_page is None:
                max_page = (total//per_page) + 1
            if "data" not in series_data:
                print(f"Failed to fetch series list for {category_id} at page {page}")
                series_list_by_page.append([])
                if page>=9 and sum(len(subpage) for subpage in series_list_by_page[-3:])==0:
                    break
                page += 1
                continue
            data = series_data["data"]
            series_list_by_page.append(data)
            series_list.extend(data)
            if (total is not None and len(series_list)>=total) or (max_page is not None and page>=max_page):
                break
            page += 1
            continue
        if by_page:
            return series_list_by_page
        return series_list
    
    def get_vod_list(self, category_id, by_page=False, **kwargs):
        vod_list = []
        vod_list_by_page = []
        page = 1
        total, per_page, max_page = None, None, None
        while True:
            print(f"Fetching vod for {category_id} at page {page}")
            payload = {
                "type": "vod",
                "action": "get_ordered_list",
                "category": category_id,
                "movie_id": kwargs.get("movie_id","0"),
                "season_id": kwargs.get("season_id","0"),
                "episode_id": kwargs.get("episode_id","0"),
                "force_ch_link_check": kwargs.get("force_ch_link_check","0"),
                "fav": kwargs.get("fav","0"),
                "sortby": kwargs.get("sortby","added"),
                "hd": kwargs.get("hd","0"),
                "not_ended": kwargs.get("not_ended","0"),
                "p": page,
                "from_ch_id": kwargs.get("from_ch_id","0"),
                "JsHttpRequest": "1-xml"
            }
            r = self.gen_request("post",payload)
            vod_data = self.gen_jsondata(r,{},dict)
            if total is None and "total_items" in vod_data:
                total = vod_data["total_items"]
            if per_page is None and "max_page_items" in vod_data:
                per_page = vod_data["max_page_items"]
            if total is not None and per_page is not None and max_page is None:
                max_page = (total//per_page) + 1
            if "data" not in vod_data:
                print(f"Failed to fetch vod list for {category_id} at page {page}")
                vod_list_by_page.append([])
                if page>=9 and sum(len(subpage) for subpage in vod_list_by_page[-3:])==0:
                    break
                page += 1
                continue
            data = vod_data["data"]
            vod_list_by_page.append(data)
            vod_list.extend(data)
            if (total is not None and len(vod_list)>=total) or (max_page is not None and page>=max_page):
                break
            page += 1
            continue
        if by_page:
            return vod_list_by_page
        return vod_list
    
    def get_short_epg(self, channel_id=None):
        if channel_id is None:
            channel_id = self.cache["channel_id"]
        payload = {
            "type": "itv",
            "action": "get_short_epg",
            "ch_id": channel_id,
            "size": "10",
            "JsHttpRequest": "1-xml"
        }
        r = self.gen_request("post",payload)
        epg_data = self.gen_jsondata(r,[],list)
        if len(epg_data)==0:
            print("→ Unable to fetch short EPG for:", channel_id)
        else:
            print("→ Short EPG fetched starting from:", epg_data[0]["time"])
        self.gen_logs(r, "get_short_epg.js", True)
        return epg_data
    
    def get_epg_dated(self, channel_id=None, date="YYYY-MM-DD", by_page=False):
        if channel_id is None:
            channel_id = self.cache["channel_id"]
        epg_dated = []
        epg_dated_by_page = []
        page = 1
        total, per_page, max_page = None, None, None
        while True:
            print(f"Fetching EPG for {date} at page {page}")
            payload = {
                "type": "epg",
                "action": "get_simple_data_table",
                "ch_id": channel_id,
                "date": date,
                "p": page,
                "JsHttpRequest": "1-xml"
            }
            r = self.gen_request("post",payload)
            epg_data = self.gen_jsondata(r,{},dict)
            if total is None and "total_items" in epg_data:
                total = epg_data["total_items"]
            if per_page is None and "max_page_items" in epg_data:
                per_page = epg_data["max_page_items"]
            if total is not None and per_page is not None and max_page is None:
                max_page = (total//per_page) + 1
            if "data" not in epg_data:
                print(f"Failed to fetch EPG for {date} at page {page}")
                epg_dated_by_page.append([])
                if page>=9 and sum(len(subpage) for subpage in epg_dated_by_page[-3:])==0:
                    break
                page += 1
                continue
            data = epg_data["data"]
            epg_dated_by_page.append(data)
            epg_dated.extend(data)
            if (total is not None and len(epg_dated)>=total) or (max_page is not None and page>=max_page):
                break
            page += 1
            continue
        if by_page:
            return epg_dated_by_page
        return epg_dated
    
    def get_link(self, data):
        pattern = re.compile(r"https?://\S+")
        if isinstance(data, str):
            match = pattern.search(data)
            if match:
                link = match.group().rstrip(".,;!?\"'")
                return link
        elif isinstance(data, list):
            for item in data:
                result = self.get_link(item)
                if result:
                    return result
        elif isinstance(data, dict):
            for value in data.values():
                result = self.get_link(value)
                if result:
                    return result
        return None
    
    
    def parse_vod(self, link):
        link = link
        return link
    
    def parse_catchup(self, link):
        link = link
        return link
    
    def parse_live(self, link):
        link = link
        return link
    
    
    def load_vod(self, vod_id, vod_cmd, series_id="0", extract=True):
        print(f"Fetching vod link for vod id: {vod_id}")
        payload = {
            "type": "vod",
            "action": "create_link",
            "cmd": vod_cmd,
            "series": series_id,
            "forced_storage": "0",
            "disable_ad": "0",
            "download": "0",
            "force_ch_link_check": "0",
            "JsHttpRequest": "1-xml"
        }
        r = self.gen_request("post",payload)
        link_data = r.json().get("js", {})
        self.cache.update({
            "link_data" : link_data
        })
        print("→ Fetched link data for:", vod_id)
        if not extract:
            return link_data
        link = None
        if isinstance(link_data,dict) and "cmd" in link_data:
            link = self.get_link(link_data["cmd"])
        if link is None:
            link = self.get_link(link_data)
        if link is None:
            print("→ Unable to extract link for:", vod_id)
            print(self.dsh)
            return link_data
        link = self.parse_vod(link)
        self.cache.update({
            "timestamp" : "",
            "link" : link
        })
        print("→ LINK:\t", link)
        print(self.dsh)
        return link
    
    def load_epg(self, channel_id=None, days=2):
        if channel_id is None:
            channel_id = self.cache["channel_id"]
        epg_data = []
        date = datetime.date.today()
        print(f"Fetching EPG for {days} days")
        while days>0:
            epg_dated = self.get_epg_dated(channel_id, date.strftime("%Y-%m-%d"))
            epg_data.extend(epg_dated)
            date -= datetime.timedelta(days=1)
            days-=1
        print(f"→ Fetched total {len(epg_data)} contents")
        print(self.dsh)
        return epg_data
    
    def load_catchup(self, channel_id=None, time="HH:MM:SS", date=None, extract=True):
        if channel_id is None:
            channel_id = self.cache["channel_id"]
        else:
            self.cache.update({
                "channel_id" : channel_id,
                "channel" : self.all_channels[channel_id]
            })
        self.cache.update({
            "epg" : "",
            "timestamp" : "",
            "link_data" : "",
            "link" : ""
        })
        print(f"Fetching catchup link for: {self.cache["channel"]["name"]}")
        if date is None:
            date = datetime.datetime.now().strftime("%Y-%m-%d")
        epg_list = self.get_epg_dated(channel_id, date)
        if len(epg_list)==0:
            print("→ Failed to fetch EPG data for:", self.cache["channel"]["name"])
            print(self.dsh)
            return ""
        target_time = f"{date} {time}"
        target_time = datetime.datetime.strptime(target_time, "%Y-%m-%d %H:%M:%S")
        if datetime.datetime.strptime(epg_list[0]["time"], "%Y-%m-%d %H:%M:%S") > target_time:
            dt = datetime.datetime.strptime(date, "%Y-%m-%d")
            yesterday = (dt - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            epg_list = self.get_epg_dated(channel_id, yesterday)
        epg_id = None
        for entry in epg_list:
            start = datetime.datetime.strptime(entry["time"], "%Y-%m-%d %H:%M:%S")
            end = datetime.datetime.strptime(entry["time_to"], "%Y-%m-%d %H:%M:%S")
            if start <= target_time < end:
                self.cache.update({
                    "epg" : entry,
                    "timestamp" : entry["start_timestamp"]
                })
                epg_id = entry["id"]
                break
        if epg_id is None:
            print("→ Failed to fetch EPG data for:", self.cache["channel"]["name"])
            print(self.dsh)
            return ""
        cmd = f"auto /media/{epg_id}.mpg"
        payload = {
            "type": "tv_archive",
            "action": "create_link",
            "cmd": cmd,
            "series": "",
            "forced_storage": "0",
            "disable_ad": "0",
            "download": "0",
            "force_ch_link_check": "0",
            "JsHttpRequest": "1-xml"
        }
        r = self.gen_request("post",payload)
        link_data = r.json().get("js", {})
        self.cache.update({
            "link_data" : link_data
        })
        print("→ Fetched link data for:", self.cache["channel"]["name"])
        if not extract:
            return link_data
        link = None
        if isinstance(link_data,dict) and "cmd" in link_data:
            link = self.get_link(link_data["cmd"])
        if link is None:
            link = self.get_link(link_data)
        if link is None:
            print("→ Unable to extract link for:", self.cache["channel"]["name"])
            print(self.dsh)
            return link_data
        link = self.parse_catchup(link)
        self.cache.update({
            "link" : link
        })
        print("→ LINK:\t", link)
        print(self.dsh)
        return link
    
    def load_live(self, channel_id=None, extract=True):
        if channel_id is None:
            channel_id = self.cache["channel_id"]
        else:
            self.cache.update({
                "channel_id" : channel_id,
                "channel" : self.all_channels[channel_id]
            })
        self.cache.update({
            "epg" : "",
            "timestamp" : "",
            "link_data" : "",
            "link" : ""
        })
        print(f"Fetching live link for: {self.cache["channel"]["name"]}")
        epg_data = self.get_short_epg(self.cache["channel_id"])
        if len(epg_data)!=0:
            self.cache.update({
                "epg" : epg_data[0]
            })
        cmd = self.cache["channel"]["cmd"]
        payload = {
            "type": "itv",
            "action": "create_link",
            "cmd": cmd,
            "series": "0",
            "forced_storage": "0",
            "disable_ad": "0",
            "download": "0",
            "force_ch_link_check": "0",
            "JsHttpRequest": "1-xml"
        }
        r = self.gen_request("post",payload)
        link_data = r.json().get("js", {})
        self.cache.update({
            "link_data" : link_data
        })
        print("→ Fetched link data for:", self.cache["channel"]["name"])
        if not extract:
            return link_data
        link = None
        if isinstance(link_data,dict) and "cmd" in link_data:
            link = self.get_link(link_data["cmd"])
        if link is None:
            link = self.get_link(link_data)
        if link is None:
            print("→ Unable to extract link for:", self.cache["channel"]["name"])
            print(self.dsh)
            return link_data
        link = self.parse_live(link)
        self.cache.update({
            "timestamp" : "",
            "link" : link
        })
        print("→ LINK:\t", link)
        print(self.dsh)
        return link
    
    
    def search_itv_genres(self, query):
        print(self.dsh)
        print(f"Searching for {query} in itv genres' title:-")
        query = query.lower()
        matches = [title for title in self.itv_genres if query in title.get("title","").lower()]
        print("Fetching similar genre titles as id:title pair:-")
        for match in matches:
            print(match["id"], ":", match.get("title",""))
        print(self.dsh)
        return matches
    
    def search_vod_categories(self, query):
        print(self.dsh)
        print(f"Searching for {query} in vod categories' title:-")
        query = query.lower()
        matches = [title for title in self.vod_categories if query in title.get("title","").lower()]
        print("Fetching similar category titles as id:title pair:-")
        for match in matches:
            print(match["id"], ":", match.get("title",""))
        print(self.dsh)
        return matches
    
    def search_series_categories(self, query):
        print(self.dsh)
        print(f"Searching for {query} in series categories' title:-")
        query = query.lower()
        matches = [title for title in self.series_categories if query in title.get("title","").lower()]
        print("Fetching similar category titles as id:title pair:-")
        for match in matches:
            print(match["id"], ":", match.get("title",""))
        print(self.dsh)
        return matches
    
    def search_channel(self, query):
        print(self.dsh)
        print(f"Searching for {query} in all channels' names:-")
        query = query.lower()
        matches = [channel for channel in self.all_channels.values() if query in channel.get("name","").lower()]
        print("Fetching similar channel names as id:name pair:-")
        for match in matches:
            print(match["id"], ":", match.get("name",""))
        print(self.dsh)
        return matches
    
    
    def download_channel(self, limit=None, output=None, seek=None, progress_callback=None, callback_interval=1):
        print(self.dsh)
        if output is None:
            if self.cache["timestamp"]=="":
                output = f"video_{int(time.time())}.ts"
            else:
                output = f"video_{self.cache["timestamp"]}.ts"
        url = self.cache["link"]
        headers = (
            f"User-Agent: Lavf53.32.100\r\n"
            f"Referer: {self.base_url}/c/index.html\r\n"
            f"Cookie: mac={self.mac}; lang={self.lang}; timezone={self.timezone}\r\n"
        )
        cmd = ["ffmpeg"]
        cmd += ["-progress", "pipe:1"]
        cmd += ["-headers", headers]
        if seek is not None:
            cmd += ["-ss", seek]
        cmd += ["-i", url]
        if limit is not None:
            cmd += ["-t", str(limit)]
        cmd += ["-map", "0", "-c", "copy"]
        cmd += ["-y"]
        cmd += [output]
        print("→ Starting ffmpeg directly")
        process = subprocess.Popen(cmd,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, universal_newlines=True, bufsize=1
        )
        progress = {}
        last = 0
        while True:
            line = process.stdout.readline()
            if line == "":
                break
            line = line.strip()
            if line == "": 
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                progress[key] = value
                if key == "progress":
                    now = time.time()
                    if progress_callback and (now - last) >= callback_interval:
                        progress_callback(progress.copy(),process)
                        last = now
            if progress.get("progress") == "end":
                break
        process.wait()
        print(f"→ Downloaded and saved to: {output}")
        print(self.dsh)
        return output
    
    
    def stb(self):
        pass

