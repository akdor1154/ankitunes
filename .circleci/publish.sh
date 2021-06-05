curl 'https://ankiweb.net/shared/upload' \
-H 'User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:88.0) Gecko/20100101 Firefox/88.0' \
-H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8' \
-H 'Accept-Language: en-GB,en;q=0.5' \
--compressed \
-H 'Referer: https://ankiweb.net/shared/upload?id=1456964007' \
-H 'Content-Type: multipart/form-data; boundary=---------------------------199144852533685843341430090735' \
-H 'Origin: https://ankiweb.net' \
-H 'DNT: 1' \
-H 'Connection: keep-alive' \
-H 'Cookie: ankiweb=CENSORED' \
-H 'Upgrade-Insecure-Requests: 1' \
-H 'TE: Trailers' \
--data-binary $'-----------------------------199144852533685843341430090735\r\n
Content-Disposition: form-data; name="title"\r\n
\r\n
AnkiTunes\r\n
-----------------------------199144852533685843341430090735\r\n
Content-Disposition: form-data; name="tags"\r\n
\r\n
tunes, irish, itm, thesession, the session\r\n
-----------------------------199144852533685843341430090735\r\n
Content-Disposition: form-data; name="supportURL"\r\n
\r\n
https://github.com/akdor1154/ankitunes\r\n
-----------------------------199144852533685843341430090735\r\n
Content-Disposition: form-data; name="v21file0"; filename="ankitunes.ankiaddon"\r\n
Content-Type: application/octet-stream\r\n
\r\n
-----------------------------199144852533685843341430090735\r\n
Content-Disposition: form-data; name="minVer0"\r\n
\r\n
45\r\n
-----------------------------199144852533685843341430090735\r\n
Content-Disposition: form-data; name="maxVer0"\r\n
\r\n
45\r\n
-----------------------------199144852533685843341430090735\r\n
Content-Disposition: form-data; name="desc"\r\n
\r\n
Test upload...\r\n
-----------------------------199144852533685843341430090735\r\n
Content-Disposition: form-data; name="id"\r\n
\r\n
1456964007\r\n
-----------------------------199144852533685843341430090735\r\n
Content-Disposition: form-data; name="submit"\r\n
\r\n
Update\r\n
-----------------------------199144852533685843341430090735--\r\n'