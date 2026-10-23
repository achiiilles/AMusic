import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
PKG = ROOT + "/app/src/main/java/com/music/amusic/"


def patch(path, pairs):
    text = open(path, encoding="utf-8", newline="").read()
    for old, new in pairs:
        if text.count(old) != 1:
            raise SystemExit("no unique match in %s for: %s" % (path, old[:70]))
        text = text.replace(old, new)
    open(path, "w", encoding="utf-8", newline="").write(text)


CANVAS = [
    ('''    fun catalogGet(path: String, params: Map<String, String> = emptyMap()): String? {
        val bearer = token() ?: return null
''', '''    fun catalogGet(path: String, params: Map<String, String> = emptyMap()): String? {
        lastCatalogProblem = null
        val bearer = token() ?: run {
            lastCatalogProblem = "sem acesso à Apple (sem token)"
            return null
        }
'''),
    ('''    /** Apple's colours are six hex digits with no prefix. */''', '''    /**
     * Why the last [catalogGet] returned null, in a few Portuguese words ("erro
     * HTTP 403", "sem resposta (SocketTimeoutException)"); null when it answered.
     * Read straight after a null answer, only to tell the user what went wrong.
     */
    @Volatile
    var lastCatalogProblem: String? = null
        private set

    /** Apple's colours are six hex digits with no prefix. */'''),
    ('''                        null
                    }
                    else -> null
                }
            }
        }.getOrNull()
    }''', '''                        lastCatalogProblem = "erro HTTP 401"
                        null
                    }
                    else -> {
                        lastCatalogProblem = "erro HTTP ${response.code}"
                        null
                    }
                }
            }
        }.onFailure {
            lastCatalogProblem = "sem resposta (${it.javaClass.simpleName})"
        }.getOrNull()
    }'''),
]

SHELVES = [
    ('''    private val targets = ConcurrentHashMap<String, AppleShelfTarget>()
''', '''    /**
     * Why "Talvez você goste" is not on an album page, in Portuguese, by page id.
     * Set whenever the page's answer was read without that shelf, and removed when
     * the shelf is there. The album page shows it in the shelf's place.
     */
    private val relatedNotes = ConcurrentHashMap<String, String>()
    private val targets = ConcurrentHashMap<String, AppleShelfTarget>()
'''),
    ('''    /** What an Apple card id stands for; null for anything that is not one. */''', '''    /** The reason "Talvez você goste" is missing for the page; null when it is shown or not known yet. */
    fun relatedNote(browseId: String): String? = relatedNotes[browseId]

    private fun setNote(browseId: String, note: String?) {
        if (note == null) relatedNotes.remove(browseId) else relatedNotes[browseId] = note
    }

    private fun catalogProblem(): String = AppleMusicCanvas.lastCatalogProblem ?: "sem resposta"

    /** What an Apple card id stands for; null for anything that is not one. */'''),
    ('''            runCatching { load(album, artist, trackCount, year, trackTitles) }
                .onFailure { Log.d(TAG, "shelves failed for $album: $it") }
                .getOrNull()''', '''            runCatching { load(browseId, album, artist, trackCount, year, trackTitles) }
                .onFailure {
                    Log.d(TAG, "shelves failed for $album: $it")
                    setNote(
                        browseId,
                        "A busca no Apple Music falhou (${it.javaClass.simpleName}: ${it.message.orEmpty().take(60)})",
                    )
                }
                .getOrNull()'''),
    ('''    private fun load(
        album: String,''', '''    private fun load(
        browseId: String,
        album: String,'''),
    ('''        val choice = AppleReleaseMatcher.choose(album, artist, trackCount, year, trackTitles) ?: return null
        val albumId = choice.collectionId?.toString() ?: return emptyList()
        val body = AppleMusicCanvas.catalogGet(
            "albums/$albumId",
            mapOf("views" to "appears-on,related-albums", "include" to "artists", "l" to "pt-BR"),
        ) ?: return null
        val record = Json.parseToJsonElement(body).jsonObject["data"]?.jsonArray
            ?.firstOrNull() as? JsonObject ?: return emptyList()
''', '''        val choice = AppleReleaseMatcher.choose(album, artist, trackCount, year, trackTitles) ?: run {
            setNote(browseId, "Não consegui achar este álbum no Apple Music (artista não encontrado ou sem resposta da busca)")
            return null
        }
        val albumId = choice.collectionId?.toString() ?: run {
            setNote(browseId, "Não achei este álbum entre os lançamentos de ${choice.artistName} no Apple Music")
            return emptyList()
        }
        val body = AppleMusicCanvas.catalogGet(
            "albums/$albumId",
            mapOf("views" to "appears-on,related-albums", "include" to "artists", "l" to "pt-BR"),
        ) ?: run {
            setNote(browseId, "A busca no Apple Music falhou (${catalogProblem()})")
            return null
        }
        val record = Json.parseToJsonElement(body).jsonObject["data"]?.jsonArray
            ?.firstOrNull() as? JsonObject ?: run {
            setNote(browseId, "A Apple respondeu sem dados deste álbum (HTTP 200, lista vazia)")
            return emptyList()
        }
'''),
    ('''        val relatedRecords = pagedView(
            views,
            "related-albums",
            "albums/$albumId/view/related-albums",
            askWhenEmpty = true,
        )''', '''        val askNotes = mutableListOf<String>()
        val relatedRecords = pagedView(
            views,
            "related-albums",
            "albums/$albumId/view/related-albums",
            askWhenEmpty = true,
            notes = askNotes,
        )'''),
    ('''        if (related.isNotEmpty()) {
            shelves += HomeShelf(title = "Talvez você goste", items = related)
        } else {
            Log.d(
                TAG,
                "related-albums for $albumId: no cards (view in the album answer: ${views?.containsKey("related-albums") == true})",
            )
        }''', '''        if (related.isNotEmpty()) {
            shelves += HomeShelf(title = "Talvez você goste", items = related)
            setNote(browseId, null)
        } else {
            Log.d(
                TAG,
                "related-albums for $albumId: no cards (view in the album answer: ${views?.containsKey("related-albums") == true})",
            )
            // The reason shown on the album page where the shelf would be.
            val ownAlbum = relatedRecords.count { it.text("id") == albumId }
            val sawInAnswer = when {
                views == null -> "sem seções na resposta do álbum"
                views.containsKey("related-albums") -> "related-albums veio vazio"
                else -> "sem related-albums (seções: ${views.keys.joinToString().ifEmpty { "nenhuma" }})"
            }
            val reason = when {
                relatedRecords.isNotEmpty() -> {
                    val kept = (relatedRecords.size - ownAlbum).coerceAtMost(MAX_PAGED_CARDS)
                    "Todos os cards foram descartados (${relatedRecords.size} recebidos: " +
                        "$ownAlbum eram o próprio álbum, ${(kept - related.size).coerceAtLeast(0)} sem nome ou endereço)"
                }
                askNotes.isNotEmpty() -> "A busca de recomendações no Apple Music falhou (${askNotes.joinToString("; ")})"
                else -> "A Apple não devolveu recomendações para este álbum ($sawInAnswer; consulta própria: 0 cards)"
            }
            setNote(browseId, reason)
        }'''),
    ('''        viewPath: String,
        askWhenEmpty: Boolean = false,
    ): List<JsonObject> {''', '''        viewPath: String,
        askWhenEmpty: Boolean = false,
        notes: MutableList<String>? = null,
    ): List<JsonObject> {'''),
    ('''            val page = body?.let { runCatching { Json.parseToJsonElement(it).jsonObject }.getOrNull() }
            if (page != null) {
                records += (page["data"] as? kotlinx.serialization.json.JsonArray).orEmpty()
                    .mapNotNull { it as? JsonObject }
                next = (page["next"] as? JsonPrimitive)?.contentOrNull
            }
            Log.d(TAG, "view $name asked on its own''', '''            val page = body?.let { runCatching { Json.parseToJsonElement(it).jsonObject }.getOrNull() }
            if (body == null) {
                notes?.add(catalogProblem())
            } else if (page == null) {
                notes?.add("resposta ilegível")
            }
            if (page != null) {
                records += (page["data"] as? kotlinx.serialization.json.JsonArray).orEmpty()
                    .mapNotNull { it as? JsonObject }
                next = (page["next"] as? JsonPrimitive)?.contentOrNull
            }
            Log.d(TAG, "view $name asked on its own'''),
]

DETAIL = [
    ('''        ) ?: appleShelves
    }
''', '''        ) ?: appleShelves
        appleRelatedNote = AppleAlbumShelves.relatedNote(page.browseId.orEmpty())
    }
'''),
    ('''    LaunchedEffect(page.browseId, page.title, appleAlbumCredit, appleAlbumEligible, songs.size) {
        if (!appleAlbumEligible || appleAlbumCredit.isBlank() || songs.isEmpty()) return@LaunchedEffect
        appleShelves''', '''    // Why "Talvez você goste" is not drawn, when Apple's answer for this page
    // has no such shelf: a quiet line of text in the shelf's place.
    var appleRelatedNote by remember(page.browseId) {
        mutableStateOf(
            if (appleAlbumEligible) AppleAlbumShelves.relatedNote(page.browseId.orEmpty()) else null,
        )
    }
    LaunchedEffect(page.browseId, page.title, appleAlbumCredit, appleAlbumEligible, songs.size) {
        if (!appleAlbumEligible || appleAlbumCredit.isBlank() || songs.isEmpty()) return@LaunchedEffect
        appleShelves'''),
    ('''    val appleAlbum = appleAlbumResult?.colors
    val palette = remem''', '''    val relatedNoteShown = appleAlbumEligible && appleRelatedNote != null &&
        appleShelves.none { it.title.trim().equals("Talvez você goste", ignoreCase = true) } &&
        visibleSections.none { it.title.trim().equals("Talvez você goste", ignoreCase = true) }
    val relatedNoteAlpha by animateFloatAsState(
        targetValue = if (relatedNoteShown) 1f else 0f,
        animationSpec = tween(durationMillis = 350, easing = FastOutSlowInEasing),
    )
    val appleAlbum = appleAlbumResult?.colors
    val palette = remem'''),
    ('''            if (isArtist) aboutItem()''', '''            // In the place of "Talvez você goste" when it cannot be drawn: why.
            if (relatedNoteShown) {
                item(key = "apple-related-note") {
                    Text(
                        text = "Talvez você goste não apareceu. ${appleRelatedNote.orEmpty()}",
                        style = MaterialTheme.typography.bodySmall,
                        color = palette.onBackgroundVariant,
                        modifier = Modifier
                            .padding(start = ARTIST_CONTENT_GUTTER, end = ARTIST_CONTENT_GUTTER, top = 22.dp, bottom = 8.dp)
                            .graphicsLayer { this.alpha = relatedNoteAlpha },
                    )
                }
            }
            if (isArtist) aboutItem()'''),
]

patch(PKG + "data/canvas/AppleMusicCanvas.kt", CANVAS)
patch(PKG + "data/canvas/AppleAlbumShelves.kt", SHELVES)
patch(PKG + "ui/screens/DetailScreen.kt", DETAIL)
print("patched")
