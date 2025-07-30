import req
import img

# mc.players('play.trexmine.com')
def players(ip):
    """**this function returns your server players count :** ```mc.players('play.trexmine.com')``` **and result is alike** ```2192 / 2193``` **!**"""
    print("Runnig...")
    response = req.req(f"https://api.mcsrvstat.us/3/{ip}")
    online = response.json()['players']['online']
    max = response.json()['players']['max']
    return f"{online} / {max}"

# mc.ip('play.trexmine.com')
def ip(ip):
    """**this function returns ip of server :** ```mc.ip('play.trexmine.com')``` **and result is alike** ```212.80.8.242``` **!**"""
    print("Runnig...")
    response = req.req(f"https://api.mcsrvstat.us/3/{ip}")
    return response.json()['ip']

# mc.ipp('play.trexmine.com')
def ipp(ip):
    """**this function returns ip & port of server :** ```mc.ipp('play.trexmine.com')``` **and result is alike** ```212.80.8.242:25565``` **!**"""
    print("Runnig...")
    response = req.req(f"https://api.mcsrvstat.us/3/{ip}")
    res_ip = response.json()['ip']
    res_port = response.json()['port']
    return f"{res_ip}:{res_port}"

# mc.motdc('play.trexmine.com')
def motdc(ip):
    """**this function returns clean motd of server :** ```mc.motdc('play.trexmine.com')``` **and result is alike** ```['                 TrexMine 1.8 - 1.21', '            SKYWARS BETA - RELEASED!']``` **!**"""
    print("Runnig...")
    response = req.req(f"https://api.mcsrvstat.us/3/{ip}")
    return response.json()['motd']['clean']

# mc.motdr('play.trexmine.com')
def motdr(ip):
    """**this function returns raw motd of server :** ```mc.motdr('play.trexmine.com')``` **and result is alike** ```['§r                 §2§lTrex§r§a§lMine §r§71.8 §r§8- §r§71.21§r', '§r§f            §r§d§lSKYWARS §r§e§lBETA §r§7- §r§b§lRELEASED!§r']``` **!**"""
    print("Runnig...")
    response = req.req(f"https://api.mcsrvstat.us/3/{ip}")
    return response.json()['motd']['raw']

# mc.version('play.trexmine.com')
def version(ip):
    """**this function returns versions can join server :** ```mc.version('play.trexmine.com')``` **and result is alike** ```1.8 - 1.20``` **!**"""
    print("Runnig...")
    response = req.req(f"https://api.mcsrvstat.us/3/{ip}")
    return response.json()['version']

# # mc.icon('play.trexmine.com')
# def icon(ip):
#     """**this function response icon of server :** ```mc.ip('play.trexmine.com')``` **and result is** ```icon.png``` **!**"""
#     print("Runnig...")
#     response = req.req(f"https://api.mcsrvstat.us/3/{ip}")
#     return img.png(req.req(response.json()['icon']).content,"icon")
    
# mc.is_online('play.trexmine.com')
def is_online(ip):
    """**this function returns true or false :** ```mc.is_online('play.trexmine.com')``` **and result is alike** ```true``` **!**"""
    print("Runnig...")
    response = req.req(f"https://api.mcsrvstat.us/3/{ip}")
    return response.json()['online']
