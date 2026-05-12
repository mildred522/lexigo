package com.aiproduct.vocab.data.settings

import android.content.Context
import com.aiproduct.vocab.ui.BackgroundTheme
import com.aiproduct.vocab.domain.learning.LearningLanguage
import com.aiproduct.vocab.ui.UserPreferences

class UserPreferencesStore(
    context: Context,
) {
    private val prefs = context.applicationContext.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    fun load(): UserPreferences = UserPreferences(
        defaultLearningLanguage = prefs.getString(KEY_DEFAULT_LANGUAGE, LearningLanguage.JAPANESE.name)
            ?.let { runCatching { LearningLanguage.valueOf(it) }.getOrNull() }
            ?: LearningLanguage.JAPANESE,
        autoResumeSessions = prefs.getBoolean(KEY_AUTO_RESUME, true),
        frenchAccentInsensitive = prefs.getBoolean(KEY_FRENCH_ACCENT_INSENSITIVE, true),
        backgroundTheme = prefs.getString(KEY_BACKGROUND_THEME, BackgroundTheme.AURORA.name)
            ?.let { runCatching { BackgroundTheme.valueOf(it) }.getOrNull() }
            ?: BackgroundTheme.AURORA,
        customBackgroundUri = prefs.getString(KEY_CUSTOM_BACKGROUND_URI, null),
        useCustomBackground = prefs.getBoolean(KEY_USE_CUSTOM_BACKGROUND, false),
        showDailyCover = prefs.getBoolean(KEY_SHOW_DAILY_COVER, true),
        debugModeEnabled = prefs.getBoolean(KEY_DEBUG_MODE_ENABLED, false),
    )

    fun save(preferences: UserPreferences) {
        prefs.edit()
            .putString(KEY_DEFAULT_LANGUAGE, preferences.defaultLearningLanguage.name)
            .putBoolean(KEY_AUTO_RESUME, preferences.autoResumeSessions)
            .putBoolean(KEY_FRENCH_ACCENT_INSENSITIVE, preferences.frenchAccentInsensitive)
            .putString(KEY_BACKGROUND_THEME, preferences.backgroundTheme.name)
            .putString(KEY_CUSTOM_BACKGROUND_URI, preferences.customBackgroundUri)
            .putBoolean(KEY_USE_CUSTOM_BACKGROUND, preferences.useCustomBackground)
            .putBoolean(KEY_SHOW_DAILY_COVER, preferences.showDailyCover)
            .putBoolean(KEY_DEBUG_MODE_ENABLED, preferences.debugModeEnabled)
            .apply()
    }

    companion object {
        private const val PREFS_NAME = "user-preferences"
        private const val KEY_DEFAULT_LANGUAGE = "default_learning_language"
        private const val KEY_AUTO_RESUME = "auto_resume_sessions"
        private const val KEY_FRENCH_ACCENT_INSENSITIVE = "french_accent_insensitive"
        private const val KEY_BACKGROUND_THEME = "background_theme"
        private const val KEY_CUSTOM_BACKGROUND_URI = "custom_background_uri"
        private const val KEY_USE_CUSTOM_BACKGROUND = "use_custom_background"
        private const val KEY_SHOW_DAILY_COVER = "show_daily_cover"
        private const val KEY_DEBUG_MODE_ENABLED = "debug_mode_enabled"
    }
}
