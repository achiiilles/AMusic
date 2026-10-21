import sys
P_AM = 'app/src/main/java/com/music/amusic/data/canvas/AppleMusicCanvas.kt'
P_REPO = 'app/src/main/java/com/music/amusic/data/canvas/AppleAlbumColorRepository.kt'
def rep(s, old, new):
    n = s.count(old)
    if n != 1:
        print('ANCHOR COUNT', n, repr(old[:70]))
        sys.exit(1)
    return s.replace(old, new)
am = open(P_AM, encoding='utf-8').read()
am = rep(am,
'''            .addQueryParameter("limit", "10")
            .build()
            .toString()

        val body = get(url, bearer) ?: return null
        val root = runCatching { json.parseToJsonElement(body).jsonObject }.getOrNull() ?: return null
        val hits = root["results"]?.jsonObject
            ?.get("albums")?.jsonObject
            ?.get("data")?.jsonArray
            ?: return AppleAlbumColorsResult(null)''',
'''            .addQueryParameter("limit", "10")
            .addQueryParameter("extend", "editorialVideo")
            .build()
            .toString()

        val body = get(url, bearer) ?: return null
        val root = runCatching { json.parseToJsonElement(body).jsonObject }.getOrNull() ?: return null
        val hits = root["results"]?.jsonObject
            ?.get("albums")?.jsonObject
            ?.get("data")?.jsonArray
            ?: return AppleAlbumColorsResult(null)''')
am = rep(am,
'''            val artwork = attributes["artwork"]?.jsonObject ?: continue
            val background = artwork["bgColor"]?.jsonPrimitive?.contentOrNull?.hexToArgb() ?: continue
            val accent = artwork["textColor1"]?.jsonPrimitive?.contentOrNull?.hexToArgb() ?: background
''',
'''            // The colour Apple draws the album page on is the one of the release's
            // header artwork. For a release with motion artwork that is the colour
            // of the animation's preview frame (the tall one on a phone), which is
            // not always the colour of the sleeve itself: Short n' Sweet is blue on
            // the sleeve and dark brown on its page. A release without motion
            // artwork has only the sleeve's own colour.
            val video = attributes["editorialVideo"] as? JsonObject
            val frames = listOf("motionDetailTall", "motionDetailSquare").mapNotNull { key ->
                (video?.get(key) as? JsonObject)?.get("previewFrame") as? JsonObject
            }
            val sources = frames + listOfNotNull(attributes["artwork"] as? JsonObject)
            val source = sources.firstOrNull { candidate ->
                candidate["bgColor"]?.jsonPrimitive?.contentOrNull?.hexToArgb() != null
            } ?: continue
            val background = source["bgColor"]?.jsonPrimitive?.contentOrNull?.hexToArgb() ?: continue
            val accent = source["textColor1"]?.jsonPrimitive?.contentOrNull?.hexToArgb() ?: background
''')
am = rep(am,
'''about; only the answer differs: `attributes.artwork.bgColor` and
     * `textColor1` instead of the motion artwork.''',
'''about; only the answer differs: the colour of the album page
     * (`bgColor` and `textColor1` of the motion artwork's preview frame, else of
     * `attributes.artwork`) instead of the motion artwork itself.''')
open(P_AM, 'w', encoding='utf-8').write(am)
rp = open(P_REPO, encoding='utf-8').read()
rp = rep(rp,
''' * They come from `attributes.artwork` on the catalog API, so nothing has to be
 * decoded from the sleeve to find them.''',
''' * They come from the catalog API: the preview frame of the release's motion
 * artwork when it has one (that is the colour Apple's own album page uses), else
 * `attributes.artwork`. Nothing has to be decoded from the sleeve to find them.''')
open(P_REPO, 'w', encoding='utf-8').write(rp)
print('OK')
