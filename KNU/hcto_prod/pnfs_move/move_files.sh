#!/bin/bash
# move_files.sh LIST: move each file (path relative to /d0/scratch/choij/SKNanoOutput)
# to /pnfs/.../store/user/choij/SKNanoOutput/ over xrootd. Per file: xrdcp with adler32
# checksum (source vs destination), then size on /pnfs == size on /d0, then the /d0
# file is removed. A destination already present with the same size is not copied
# again. Nothing on /pnfs is overwritten or deleted. Exit 1 if any file fails.
SRC=/d0/scratch/choij/SKNanoOutput
PNFS=/pnfs/knu.ac.kr/data/cms/store/user/choij/SKNanoOutput
URL=root://cluster142.knu.ac.kr//store/user/choij/SKNanoOutput
rc=0; n=0
while read -r rel; do
  s=$SRC/$rel; d=$PNFS/$rel
  [ -f "$s" ] || { [ -f "$d" ] && continue; echo "MISSING $rel"; rc=1; continue; }
  if [ ! -f "$d" ]; then
    xrdcp --path --nopbar --cksum adler32:source "$s" "$URL/$rel" || { echo "XRDCP FAILED $rel"; rc=1; continue; }
  fi
  if [ "$(stat -c %s "$s")" = "$(stat -c %s "$d")" ]; then rm -f "$s"; n=$((n+1)); else echo "SIZE MISMATCH $rel"; rc=1; fi
done < "$1"
echo "moved $n files, rc=$rc"; exit $rc
