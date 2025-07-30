import json
import cloudscraper


class IPTV:
    def __init__(self, base_url, post_url="", export=False):
        self.status = "off"
        self.r_list = []
        self.export = False
        self.dsh = "----------------------------------------"
        # important input
        self.base_url   = base_url
        # known constants
        self.lang = "en"
        self.timezone = "Europe/Paris"
        self.client_type = "STB"
        self.stb_type = "MAG250"
        self.hd = "1"
        self.num_banks = "2"
        self.image_desc = "0.2.18-r23-250"
        self.image_date = "Wed Aug 29 10:49:53 EEST 2018"
        self.image_version = "218"
        self.video_out = "hdmi"
        self.hw_version = "2.17-IB-00"
        self.api_signature = "262"
        self.js_api_ver = "343"
        self.stb_api_ver = "146"
        self.api_ver = [f"JS API version: {self.js_api_ver}", f"STB API version: {self.stb_api_ver}"]
        self.player_engine_ver = "0x58c&"
        # stb initialisation
        self.gen_input()
        self.gen_scraper()
        if export is True: self.export = True
        # stb initialised
    
    
    def gen_jsondata(self, jsondata, construct=None, validate=None, js_key=True):
        if construct is None or validate is None:
            construct, validate = {}, dict
        data = jsondata.json()
        if js_key:
            data = data.get("js", construct)
        if isinstance(data,validate):
            return data
        return construct
    
    def gen_logs(self, r, filename, pretty=False):
        self.r_list.append(r)
        if self.export is False:
            return False
        if pretty:
            r = json.dumps(r.json(), indent=2, ensure_ascii=False)
        else:
            r = r.text
        with open(f"{filename}", "w", encoding="utf-8") as file:
            file.write(r)
        return True
    
    
    def gen_input(self):
        if self.base_url[-1] == "/":
            self.base_url = self.base_url[:-1]
        self.hostname   = self.base_url.split("://", 1)[-1].split("/",1)[0]
        if ":" in self.hostname:
            self.port = ":" + self.hostname.split(":", 1)[1]
            self.hostname = self.hostname.split(":", 1)[0]
        else:
            self.port = ""
        self.portal_url = self.base_url + self.post_url
        return True
    
    def gen_scraper(self):
        self.scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "linux"}
        )
        return True
        
    def gen_request(self, method, payload=None, url=""):
        if payload is None:
            payload = {}
        if url=="":
            url = self.portal_url
        if method=="get":
            r = self.scraper.get(url, params=payload)
            r.raise_for_status()
        if method=="post":
            r = self.scraper.post(url, data=payload)
            r.raise_for_status()
        return r
    
    
    def stb(self):
        pass

