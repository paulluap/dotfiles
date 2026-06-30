#!/usr/bin/env bash 
url=$1
if [[ -z $url ]]; then
    echo "url is empty"
    exit 1
fi
proxy_ports=('4781' '7897' '9050')
pp=''
for p in "${proxy_ports[@]}"; do 
    if nc -z localhost $p 2>&1 > /dev/null; then
        pp=$p
        break
    fi
done
if [[ -z $pp ]]; then
    echo "proxy port not found"
    eixt 1
fi

set -e 

title=$(yt-dlp --proxy "socks5://127.0.0.1:$pp" --get-title "$url")
mkdir "${title}"
(cd "${title}" && yt-dlp -f "bv*[height<=480]+ba/b[height<=480]" --write-subs \
    --write-thumbnail --convert-thumbnails png \
    --merge-output-format mp4 \
    --sub-format srt --proxy socks5://127.0.0.1:$pp "$url")
