package com.aiproduct.vocab.ui.audio

import android.content.Context
import android.speech.tts.TextToSpeech
import android.util.Log
import com.aiproduct.vocab.ui.debug.AppDebugLog
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors
import java.util.Locale

interface WordSpeaker {
    fun speak(language: String, text: String)

    fun warmUp(language: String)

    fun shutdown()
}

class AndroidWordSpeaker(
    context: Context,
) : WordSpeaker, TextToSpeech.OnInitListener {
    private val appContext = context.applicationContext
    private val speechExecutor: ExecutorService = Executors.newSingleThreadExecutor()
    private var isReady = false
    private var textToSpeech: TextToSpeech? = TextToSpeech(appContext, this)

    override fun onInit(status: Int) {
        isReady = status == TextToSpeech.SUCCESS
        AppDebugLog.add(TAG, "system TTS init status=$status ready=$isReady")
    }

    override fun speak(language: String, text: String) {
        AppDebugLog.add(TAG, "speak requested language=$language text=$text")
        if (text.isBlank()) {
            AppDebugLog.add(TAG, "speak ignored blank text")
            return
        }
        speechExecutor.execute {
            if (!isReady) {
                Log.w(TAG, "System TTS is not ready; cannot speak fallback for language=$language")
                AppDebugLog.add(TAG, "system TTS unavailable, not ready")
                return@execute
            }
            AppDebugLog.add(TAG, "using system TTS language=$language text=$text")
            speakWithSystemTts(language, text)
        }
    }

    override fun warmUp(language: String) {
        AppDebugLog.add(TAG, "warmUp requested language=$language engine=system-tts")
    }

    override fun shutdown() {
        isReady = false
        speechExecutor.shutdownNow()
        val current = textToSpeech
        textToSpeech = null
        current?.shutdown()
    }

    private fun speakWithSystemTts(language: String, text: String) {
        val current = textToSpeech ?: return
        val locale = speechLocaleFor(language)
        val availability = current.isLanguageAvailable(locale)
        AppDebugLog.add(TAG, "system TTS language availability=$availability locale=$locale")
        if (availability < TextToSpeech.LANG_AVAILABLE) {
            AppDebugLog.add(TAG, "system TTS language unavailable; trying anyway")
        }
        current.language = locale
        val result = current.speak(text, TextToSpeech.QUEUE_FLUSH, null, "vocab-$language")
        AppDebugLog.add(TAG, "system TTS speak result=$result")
    }
}

fun speechLocaleFor(language: String): Locale = when (language.lowercase()) {
    "ja",
    "jp",
    -> Locale.forLanguageTag("ja-JP")

    "fr" -> Locale.forLanguageTag("fr-FR")
    else -> Locale.forLanguageTag("en-US")
}

private const val TAG = "AndroidWordSpeaker"
