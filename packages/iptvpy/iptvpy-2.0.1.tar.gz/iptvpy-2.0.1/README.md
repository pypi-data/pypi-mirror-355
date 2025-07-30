# iptvpy

**iptvpy** is a modular Python library for IPTV portal interaction.

---

## Features

- Base `IPTV` class for IPTV portal
- Easy to extend for other IPTV systems
- Uses `cloudscraper` to bypass Cloudflare
- Optional logging/export of responses

---

## Requirements

- Python 3.x
- `cloudscraper`

### Install dependencies manually

```bash
pip install cloudscraper --upgrade
```

---

## Installation

```bash
pip install iptvpy
```

---

## Usage

### IPTV

Core class with:

* `gen_jsondata()` — safely extracts JSON, optionally from `.js` key
* `gen_logs()` — logs responses to `self.r_list` and to files if required
* `gen_input()` — parses URL/host details and holds logic for client-side variables
* `gen_scraper()` — initializes a Cloudflare-capable session
* `gen_request()` — performs `GET` or `POST` requests

Subclasses like `MacPortal`, `XtreamPortal` can build on this to implement specific authentication flows and APIs.

---

## Notes

- Has child class `MacPortal` (Stalker/Ministra like portals); check `src/MacPortal.py` and study code for usage
- Planned to add child class `XtreamPortal` (Xtream-Codes like portals)
- Planned to write perfect README.md

---

## License

**Apache License 2.0**

This library is open-source and free to use under the [Apache 2.0 License](./LICENSE).

---

## Contributing

Contributions, suggestions, and feature requests are welcome! Feel free to submit an issue or PR.

---

## Author

Developed by [भाग्य ज्योति (Bhagya Jyoti)](https://github.com/BhagyaJyoti22006)

---

**Happy iptv portal-ing!**

