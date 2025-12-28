# -*- coding: utf-8 -*-

import os
import sys
import time
import tempfile
import urllib.request
import subprocess


def main():
    if len(sys.argv) < 3:
        return 2

    target_exe = os.path.abspath(sys.argv[1])
    url = sys.argv[2]

    app_dir = os.path.dirname(target_exe)
    tmp_new = os.path.join(tempfile.gettempdir(), "GameGiveawaysPro.new.exe")

    # дать основному приложению закрыться (иначе Windows не даст заменить exe)
    time.sleep(1.2)

    urllib.request.urlretrieve(url, tmp_new)

    # несколько попыток замены
    for _ in range(30):
        try:
            if os.path.exists(target_exe):
                try:
                    os.remove(target_exe)
                except Exception:
                    pass
            os.replace(tmp_new, target_exe)
            break
        except Exception:
            time.sleep(0.4)
    else:
        return 3

    subprocess.Popen([target_exe], cwd=app_dir, close_fds=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
