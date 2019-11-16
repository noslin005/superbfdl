from smcscrapper import Supermicro

model = "X11SSH-F"

updater = Supermicro()
bios = updater.get_bios(model)
print(updater.firmwares)
updater.close()
