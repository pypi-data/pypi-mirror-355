# SvStats

A lightweight Python wrapper By Amirabolfazle, providing access to a variety of AI-powered tools such as:

* Image generation
* Logo and QR code creation
* Ai Response

---

## 📦 Installation

```bash
pip install svstats
```

---

## 🚀 Usage

### ![Minecraft](https://raw.githubusercontent.com/github/explore/9d8add24505ed5774d080d1e1b751be8ebaaedb3/topics/minecraft/minecraft.png)

```python
from svstats import mc

# **this function returns your server players count :** ```mc.players('play.trexmine.com')``` **and result is alike** ```2192 / 2193``` **!**
mc.players('play.trexmine.com')


# **this function returns ip of server :** ```mc.ip('play.trexmine.com')``` **and result is alike** ```212.80.8.242``` **!**
mc.ip('play.trexmine.com')


# **this function returns ip & port of server :** ```mc.ipp('play.trexmine.com')``` **and result is alike** ```212.80.8.242:25565``` **!**
mc.ipp('play.trexmine.com')


# this function returns clean motd of server :** ```mc.motdc('play.trexmine.com')``` **and result is alike** ```['                 TrexMine 1.8 - 1.21', '            SKYWARS BETA - RELEASED!']``` **!**
mc.motdc('play.trexmine.com')


# this function returns raw motd of server :** ```mc.motdr('play.trexmine.com')``` **and result is alike** ```['§r                 §2§lTrex§r§a§lMine §r§71.8 §r§8- §r§71.21§r', '§r§f            §r§d§lSKYWARS §r§e§lBETA §r§7- §r§b§lRELEASED!§r']``` **!**
mc.motdr('play.trexmine.com')


# this function returns versions can join server :** ```mc.version('play.trexmine.com')``` **and result is alike** ```1.8 - 1.20``` **!**
mc.version('play.trexmine.com')


# this function returns true or false :** ```mc.is_online('play.trexmine.com')``` **and result is alike** ```True``` **!**
mc.is_online('play.trexmine.com')
```

---


## 📄 License

MIT License
