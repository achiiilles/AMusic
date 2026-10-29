package com.music.amusic.data.canvas

import java.security.MessageDigest
import java.util.Base64
import java.util.Locale
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.jsonObject
import okhttp3.Request
import okhttp3.Response

/** Local diagnostic only. No retries, request mutation, uploads or credential logging. */
internal object AppleRequestTrace {
    private val trace = ThreadLocal<String>()
    fun begin() { trace.set("Pedido ainda não enviado") }
    fun current(): String = trace.get() ?: "Sem pedido registrado nesta thread"

    private fun relevant(request: Request): Boolean =
        request.url.host == "amp-api.music.apple.com" &&
            request.url.pathSegments.getOrNull(3) == "albums"

    private fun field(obj: JsonObject?, name: String): String =
        ((obj?.get(name) as? JsonPrimitive)?.contentOrNull ?: "ausente")
            .replace('\n', ' ').replace('\r', ' ').take(160)

    private fun claims(bearer: String): String = runCatching {
        val parts = bearer.split('.')
        val header = Json.parseToJsonElement(String(Base64.getUrlDecoder().decode(parts[0]), Charsets.UTF_8)).jsonObject
        val payload = Json.parseToJsonElement(String(Base64.getUrlDecoder().decode(parts[1]), Charsets.UTF_8)).jsonObject
        "kid=${field(header, "kid")}, iss=${field(payload, "iss")}, exp=${field(payload, "exp")}"
    }.getOrDefault("claims ilegíveis")

    private fun describe(request: Request, bearer: String): String {
        val hash = MessageDigest.getInstance("SHA-256").digest(bearer.toByteArray(Charsets.UTF_8))
            .joinToString("") { "%02x".format(it.toInt() and 255) }
        return "${request.method} ${request.url}; Locale=${Locale.getDefault().toLanguageTag()}; " +
            "loja=${request.url.pathSegments.getOrNull(2)}; " +
            "User-Agent=${request.header("User-Agent")}; Origin=${request.header("Origin")}; " +
            "Referer=${request.header("Referer")}; Authorization=Bearer presente, SHA-256=$hash, ${claims(bearer)}"
    }

    fun request(request: Request, bearer: String) {
        if (!relevant(request)) return
        runCatching { trace.set(describe(request, bearer) + "; ainda sem resposta") }
    }

    fun response(response: Response, bearer: String) {
        if (!relevant(response.request)) return
        runCatching {
            // peekBody leaves the original body intact for the existing parser.
            val root = runCatching { Json.parseToJsonElement(response.peekBody(65536L).string()).jsonObject }.getOrNull()
            val error = (root?.get("errors") as? kotlinx.serialization.json.JsonArray)?.firstOrNull() as? JsonObject
            val extra = if (error == null) "" else
                "; Apple code=${field(error, "code")}, title=${field(error, "title")}, detail=${field(error, "detail")}"
            trace.set(describe(response.request, bearer) + "; HTTP ${response.code}$extra")
        }
    }
}
