package com.aiproduct.vocab.ui.personalization

import android.graphics.BitmapFactory
import android.net.Uri
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.produceState
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import com.aiproduct.vocab.ui.BackgroundTheme
import com.aiproduct.vocab.ui.UserPreferences
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

@Composable
fun AppBackground(
    preferences: UserPreferences,
    modifier: Modifier = Modifier,
) {
    val customBitmap = rememberCustomBackground(preferences.customBackgroundUri)
    val showCustom = preferences.useCustomBackground && customBitmap != null

    Box(modifier = modifier.fillMaxSize()) {
        if (showCustom) {
            Image(
                bitmap = checkNotNull(customBitmap),
                contentDescription = null,
                modifier = Modifier.fillMaxSize(),
                contentScale = ContentScale.Crop,
            )
        } else {
            BuiltInBackground(theme = preferences.backgroundTheme)
        }
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(
                    brush = Brush.verticalGradient(
                        colors = listOf(
                            Color(0xF5FFF9F3),
                            Color(0xD9FFF9F3),
                            Color(0xEDFFFDF8),
                        ),
                    ),
                ),
        )
    }
}

@Composable
private fun BuiltInBackground(theme: BackgroundTheme) {
    val palette = remember(theme) { theme.palette() }
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(brush = Brush.linearGradient(palette.baseGradient)),
    ) {
        Canvas(modifier = Modifier.fillMaxSize()) {
            drawCircle(
                brush = Brush.radialGradient(
                    colors = listOf(palette.accent.copy(alpha = 0.58f), Color.Transparent),
                    center = Offset(size.width * 0.18f, size.height * 0.2f),
                    radius = size.minDimension * 0.45f,
                ),
                radius = size.minDimension * 0.45f,
                center = Offset(size.width * 0.18f, size.height * 0.2f),
            )
            drawCircle(
                brush = Brush.radialGradient(
                    colors = listOf(palette.secondary.copy(alpha = 0.46f), Color.Transparent),
                    center = Offset(size.width * 0.88f, size.height * 0.28f),
                    radius = size.minDimension * 0.38f,
                ),
                radius = size.minDimension * 0.38f,
                center = Offset(size.width * 0.88f, size.height * 0.28f),
            )
            drawCircle(
                brush = Brush.radialGradient(
                    colors = listOf(palette.accent.copy(alpha = 0.28f), Color.Transparent),
                    center = Offset(size.width * 0.54f, size.height * 0.88f),
                    radius = size.minDimension * 0.5f,
                ),
                radius = size.minDimension * 0.5f,
                center = Offset(size.width * 0.54f, size.height * 0.88f),
            )
        }
    }
}

@Composable
private fun rememberCustomBackground(uriString: String?): ImageBitmap? {
    val context = LocalContext.current
    val uri = remember(uriString) { uriString?.takeIf(String::isNotBlank)?.let(Uri::parse) }
    val bitmap by produceState<ImageBitmap?>(initialValue = null, key1 = uri) {
        value = if (uri == null) {
            null
        } else {
            withContext(Dispatchers.IO) {
                runCatching {
                    context.contentResolver.openInputStream(uri)?.use { stream ->
                        BitmapFactory.decodeStream(stream)?.asImageBitmap()
                    }
                }.getOrNull()
            }
        }
    }
    return bitmap
}

private data class BackgroundPalette(
    val baseGradient: List<Color>,
    val accent: Color,
    val secondary: Color,
)

private fun BackgroundTheme.palette(): BackgroundPalette = when (this) {
    BackgroundTheme.AURORA -> BackgroundPalette(
        baseGradient = listOf(Color(0xFFEAF6F4), Color(0xFFD4ECE5), Color(0xFFF7F3E9)),
        accent = Color(0xFF7FC8A9),
        secondary = Color(0xFFF0BC7A),
    )

    BackgroundTheme.SUNRISE -> BackgroundPalette(
        baseGradient = listOf(Color(0xFFFFF2DE), Color(0xFFFFDFBF), Color(0xFFF8E8F3)),
        accent = Color(0xFFF6A55F),
        secondary = Color(0xFFE26D7C),
    )

    BackgroundTheme.FOREST -> BackgroundPalette(
        baseGradient = listOf(Color(0xFFE7F1E8), Color(0xFFD5E5D5), Color(0xFFEDE8D8)),
        accent = Color(0xFF7BAA7F),
        secondary = Color(0xFFB8A36C),
    )

    BackgroundTheme.NIGHTFALL -> BackgroundPalette(
        baseGradient = listOf(Color(0xFFE6ECF5), Color(0xFFD6E0F0), Color(0xFFEDE7F1)),
        accent = Color(0xFF7E9FD8),
        secondary = Color(0xFFB79ACD),
    )
}
