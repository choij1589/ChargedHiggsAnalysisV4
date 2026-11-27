#!/bin/bash
hostname; ls -d /pnfs/knu.ac.kr/data/cms/store/user/choij/RNTuple && echo "pnfs mounted"
ls /pnfs/knu.ac.kr/data/cms/store/user/choij/RNTuple | head -2
echo "proxy: $X509_USER_PROXY"; ls -la $X509_USER_PROXY 2>&1
which xrdcp xrdfs
xrdfs cluster142.knu.ac.kr ls /store/user/choij | head -3
