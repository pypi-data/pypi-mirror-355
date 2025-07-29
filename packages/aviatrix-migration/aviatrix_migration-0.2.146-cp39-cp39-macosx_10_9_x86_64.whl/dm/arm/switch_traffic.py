#!/usr/bin/python3
# -*- coding: utf-8 -*-
from dm.arm._switch_traffic import *  # noqa: F403
from dm.arm.res.Globals import Globals

if __name__ == "__main__":
    try:
        main()  # noqa: F405
    except (Exception, KeyboardInterrupt) as e:
        if Globals.getRevert() is not None and not Globals.getRevert():
            tf.storeRevertInfo(Globals.getRevertInfo())
            sys.exit(1)

