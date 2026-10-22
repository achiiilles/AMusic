package com.music.amusic.ui.icons

import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.graphics.vector.addPathNodes
import androidx.compose.ui.unit.dp

/**
 * Icons from Ionicons (https://github.com/ionic-team/ionicons), MIT License.
 *
 * Each glyph is the Ionicons path data on its native 512 grid, so the outline
 * weight and round joins match the set. Outlines are strokes; [Home], [HeartFilled]
 * and the dots inside some glyphs are solid fills. Tint is applied by
 * [androidx.compose.material3.Icon].
 */
object AMusicIcons {

    private val stroke = SolidColor(Color.Black)

    /**
     * One Ionicons glyph on its native 512 grid. [strokeData] is drawn as a round-capped,
     * round-joined outline of [strokeWidth]; [fillData] is drawn solid.
     */
    private fun glyph(
        name: String,
        strokeData: String?,
        fillData: String? = null,
        strokeWidth: Float = 32f,
    ): ImageVector =
        ImageVector.Builder(
            name = name,
            defaultWidth = 24.dp, defaultHeight = 24.dp,
            viewportWidth = 512f, viewportHeight = 512f,
        ).apply {
            if (strokeData != null) {
                addPath(
                    pathData = addPathNodes(strokeData),
                    stroke = stroke,
                    strokeLineWidth = strokeWidth,
                    strokeLineCap = StrokeCap.Round,
                    strokeLineJoin = StrokeJoin.Round,
                )
            }
            if (fillData != null) {
                addPath(pathData = addPathNodes(fillData), fill = stroke)
            }
        }.build()

    val Queue: ImageVector by lazy { glyph("ion_list_outline", strokeData = "M160 144L448 144 M160 256L448 256 M160 368L448 368 M64 144A16 16 0 1 0 96 144A16 16 0 1 0 64 144Z M64 256A16 16 0 1 0 96 256A16 16 0 1 0 64 256Z M64 368A16 16 0 1 0 96 368A16 16 0 1 0 64 368Z") }
    val LyricsQuote: ImageVector by lazy { glyph("ion_chatbox_ellipses_outline", strokeData = "M408,64H104a56,56,0,0,0-56,56V312a56,56,0,0,0,56,56h40v80l94-78a8,8,0,0,1,5-2H408a56,56,0,0,0,56-56V120A56,56,0,0,0,408,64Z", fillData = "M128 216A32 32 0 1 0 192 216A32 32 0 1 0 128 216Z M224 216A32 32 0 1 0 288 216A32 32 0 1 0 224 216Z M320 216A32 32 0 1 0 384 216A32 32 0 1 0 320 216Z") }
    val Play: ImageVector by lazy { glyph("ion_play_outline", strokeData = "M112,111V401c0,17,17,29,31,20l248-148c12-7,12-26,0-34L143,91C129,82,112,94,112,111Z") }
    val Home: ImageVector by lazy { glyph("ion_home", strokeData = null, fillData = "M262,101a8,8,0,0,0-11,0L66,277a8,8,0,0,0-2,6L64,448a32,32,0,0,0,32,32H192a16,16,0,0,0,16-16V328a8,8,0,0,1,8-8h80a8,8,0,0,1,8,8l0,136a16,16,0,0,0,16,16h96a32,32,0,0,0,32-32l0-165a8,8,0,0,0-2-6Z M491,244l-75-72,0-109a16,16,0,0,0-16-16h-48a16,16,0,0,0-16,16l0,32L278,41C273,35,265,32,256,32h0c-9,0-17,3-22,9L21,244c-6,6-7,16-1,22A16,16,0,0,0,43,268L250,69a8,8,0,0,1,11,0L469,268a16,16,0,0,0,23-.44C498,261,497,250,491,244Z") }
    val TabExplore: ImageVector by lazy { glyph("ion_compass_outline", strokeData = "M448,256c0-106-86-192-192-192S64,150,64,256s86,192,192,192S448,362,448,256Z", fillData = "M351,151l-117,47a64,64,0,0,0-36,36l-47,117a8,8,0,0,0,10,10l117-47a64,64,0,0,0,36-36l47-117A8,8,0,0,0,351,151ZM256,280a24,24,0,1,1,24-24A24,24,0,0,1,256,280Z") }
    val TabLibrary: ImageVector by lazy { glyph("ion_library_outline", strokeData = "M48 96H80A16 16 0 0 1 96 112V448A16 16 0 0 1 80 464H48A16 16 0 0 1 32 448V112A16 16 0 0 1 48 96Z M112 224L240 224 M112 400L240 400 M128 160H224A16 16 0 0 1 240 176V448A16 16 0 0 1 224 464H128A16 16 0 0 1 112 448V176A16 16 0 0 1 128 160Z M272 48H336A16 16 0 0 1 352 64V448A16 16 0 0 1 336 464H272A16 16 0 0 1 256 448V64A16 16 0 0 1 272 48Z M422,96l-40,4c-11,1-19,12-18,23l35,322c1,12,11,20,22,19l40-4c11-1,19-12,18-23L445,115C444,103,434,95,422,96Z") }
    val TabSearch: ImageVector by lazy { glyph("ion_search_outline", strokeData = "M221,64A157,157,0,1,0,378,221,157,157,0,0,0,221,64Z M338 338L448 448") }
    val Search: ImageVector by lazy { glyph("ion_search_outline", strokeData = "M221,64A157,157,0,1,0,378,221,157,157,0,0,0,221,64Z M338 338L448 448") }
    val Explore: ImageVector by lazy { glyph("ion_compass_outline", strokeData = "M448,256c0-106-86-192-192-192S64,150,64,256s86,192,192,192S448,362,448,256Z", fillData = "M351,151l-117,47a64,64,0,0,0-36,36l-47,117a8,8,0,0,0,10,10l117-47a64,64,0,0,0,36-36l47-117A8,8,0,0,0,351,151ZM256,280a24,24,0,1,1,24-24A24,24,0,0,1,256,280Z") }
    val Shuffle: ImageVector by lazy { glyph("ion_shuffle_outline", strokeData = "M400 304 L448 352 L400 400 M400 112 L448 160 L400 208 M64,352h85a80,80,0,0,0,67-36L256,256 M64,160h85a80,80,0,0,1,67,36l80,121A80,80,0,0,0,363,352H416 M416,160H363a80,80,0,0,0-67,36L288,208") }
    val Repeat: ImageVector by lazy { glyph("ion_repeat_outline", strokeData = "M320 120 L368 168 L320 216 M352,168H144a80,80,0,0,0-80,80v16 M192 392 L144 344 L192 296 M160,344H368a80,80,0,0,0,80-80V248") }
    val Infinity: ImageVector by lazy { glyph("ion_infinite_outline", strokeData = "M256,256s-48-96-126-96c-54,0-98,43-98,96s44,96,98,96c38,0,71-22,94-48 M256,256s48,96,126,96c54,0,98-43,98-96s-44-96-98-96c-38,0-71,22-94,48") }
    val MusicNote: ImageVector by lazy { glyph("ion_musical_note_outline", strokeData = "M240,343V424a32,32,0,0,1-22,31l-21,7c-26,9-53-11-53-38h0A34,34,0,0,1,167,391l51-17A32,32,0,0,0,240,343V92a16,16,0,0,1,12-16L360,48A6,6,0,0,1,368,54v58a16,16,0,0,1-12,16l-92,23A32,32,0,0,0,240,182V221") }
    val Lyrics: ImageVector by lazy { glyph("ion_text_outline", strokeData = "M32 416 L152 96 L272 416 M230 304L74 304 M326,240c12-29,41-48,74-48h0c46,0,80,32,80,80v144 M320,358c0,36,27,58,60,58,54,0,100-27,100-106v-15c-20,0-58,1-92,5C355,304,320,320,320,358Z") }
    val ChevronRight: ImageVector by lazy { glyph("ion_chevron_forward_outline", strokeData = "M184 112 L328 256 L184 400", strokeWidth = 48f) }
    val Heart: ImageVector by lazy { glyph("ion_heart_outline", strokeData = "M353,80C288,80,256,144,256,144s-32-64-97-64C106,80,65,124,64,177c-1,109,87,187,183,252a16,16,0,0,0,18,0c96-65,184-143,183-252C447,124,406,80,353,80Z") }
    val HeartFilled: ImageVector by lazy { glyph("ion_heart", strokeData = null, fillData = "M256,448a32,32,0,0,1-18-6c-79-53-113-90-131-113-40-49-59-99-59-153C49,115,98,64,159,64c44,0,75,25,92,46a6,6,0,0,0,9,0C278,89,309,64,353,64,414,64,463,115,464,177c.54,54-19,104-59,153-19,23-53,59-131,113A32,32,0,0,1,256,448Z") }
    val Plus: ImageVector by lazy { glyph("ion_add_outline", strokeData = "M256 112L256 400 M400 256L112 256") }
    val Check: ImageVector by lazy { glyph("ion_checkmark_outline", strokeData = "M416 128 L192 384 L96 288") }
    val Download: ImageVector by lazy { glyph("ion_download_outline", strokeData = "M336,176h40a40,40,0,0,1,40,40V424a40,40,0,0,1-40,40H136a40,40,0,0,1-40-40V216a40,40,0,0,1,40-40h40 M176 272 L256 352 L336 272 M256 48L256 336") }
    val Clock: ImageVector by lazy { glyph("ion_time_outline", strokeData = "M256,64C150,64,64,150,64,256s86,192,192,192,192-86,192-192S362,64,256,64Z M256 128 L256 272 L352 272") }
    val Pin: ImageVector by lazy { glyph("ion_pin_outline", strokeData = "M192 96A64 64 0 1 0 320 96A64 64 0 1 0 192 96Z", fillData = "M272,164a9,9,0,0,0-9-9H249a9,9,0,0,0-9,9V458a32,32,0,0,0,2,12l10,24a4,4,0,0,0,7,0l10-24A32,32,0,0,0,272,458Z M256 72A24 24 0 1 0 304 72A24 24 0 1 0 256 72Z") }
    val Performance: ImageVector by lazy { glyph("ion_speedometer_outline", strokeData = "M256,64C132,64,32,164,32,288A223,223,0,0,0,88,436c1,1,2,2,3,4a25,25,0,0,0,37-.1,173,173,0,0,1,255,0,25,25,0,0,0,37,.1l3-4A223,223,0,0,0,480,288C480,164,380,64,256,64Z M256 128L256 160 M416 288L384 288 M128 288L96 288 M165 197L143 175 M347 197L369 175", fillData = "M326,232l-48,76a31,31,0,0,1-7,7,30,30,0,0,1-35-49l76-48a10,10,0,0,1,12,0A10,10,0,0,1,326,232Z") }
    val FrameRate: ImageVector by lazy { glyph("ion_film_outline", strokeData = "M76 96H436A28 28 0 0 1 464 124V388A28 28 0 0 1 436 416H76A28 28 0 0 1 48 388V124A28 28 0 0 1 76 96Z M412 336H436A28 28 0 0 1 464 364V388A28 28 0 0 1 436 416H412A28 28 0 0 1 384 388V364A28 28 0 0 1 412 336Z M412 256H436A28 28 0 0 1 464 284V308A28 28 0 0 1 436 336H412A28 28 0 0 1 384 308V284A28 28 0 0 1 412 256Z M412 176H436A28 28 0 0 1 464 204V228A28 28 0 0 1 436 256H412A28 28 0 0 1 384 228V204A28 28 0 0 1 412 176Z M412 96H436A28 28 0 0 1 464 124V148A28 28 0 0 1 436 176H412A28 28 0 0 1 384 148V124A28 28 0 0 1 412 96Z M76 336H100A28 28 0 0 1 128 364V388A28 28 0 0 1 100 416H76A28 28 0 0 1 48 388V364A28 28 0 0 1 76 336Z M76 256H100A28 28 0 0 1 128 284V308A28 28 0 0 1 100 336H76A28 28 0 0 1 48 308V284A28 28 0 0 1 76 256Z M76 176H100A28 28 0 0 1 128 204V228A28 28 0 0 1 100 256H76A28 28 0 0 1 48 228V204A28 28 0 0 1 76 176Z M76 96H100A28 28 0 0 1 128 124V148A28 28 0 0 1 100 176H76A28 28 0 0 1 48 148V124A28 28 0 0 1 76 96Z M156 96H356A28 28 0 0 1 384 124V228A28 28 0 0 1 356 256H156A28 28 0 0 1 128 228V124A28 28 0 0 1 156 96Z M156 256H356A28 28 0 0 1 384 284V388A28 28 0 0 1 356 416H156A28 28 0 0 1 128 388V284A28 28 0 0 1 156 256Z") }
    val Library: ImageVector by lazy { glyph("ion_library_outline", strokeData = "M48 96H80A16 16 0 0 1 96 112V448A16 16 0 0 1 80 464H48A16 16 0 0 1 32 448V112A16 16 0 0 1 48 96Z M112 224L240 224 M112 400L240 400 M128 160H224A16 16 0 0 1 240 176V448A16 16 0 0 1 224 464H128A16 16 0 0 1 112 448V176A16 16 0 0 1 128 160Z M272 48H336A16 16 0 0 1 352 64V448A16 16 0 0 1 336 464H272A16 16 0 0 1 256 448V64A16 16 0 0 1 272 48Z M422,96l-40,4c-11,1-19,12-18,23l35,322c1,12,11,20,22,19l40-4c11-1,19-12,18-23L445,115C444,103,434,95,422,96Z") }
    val GridView: ImageVector by lazy { glyph("ion_grid_outline", strokeData = "M68 48H204A20 20 0 0 1 224 68V204A20 20 0 0 1 204 224H68A20 20 0 0 1 48 204V68A20 20 0 0 1 68 48Z M308 48H444A20 20 0 0 1 464 68V204A20 20 0 0 1 444 224H308A20 20 0 0 1 288 204V68A20 20 0 0 1 308 48Z M68 288H204A20 20 0 0 1 224 308V444A20 20 0 0 1 204 464H68A20 20 0 0 1 48 444V308A20 20 0 0 1 68 288Z M308 288H444A20 20 0 0 1 464 308V444A20 20 0 0 1 444 464H308A20 20 0 0 1 288 444V308A20 20 0 0 1 308 288Z") }
    val ListView: ImageVector by lazy { glyph("ion_menu_outline", strokeData = "M80 160L432 160 M80 256L432 256 M80 352L432 352") }
}
