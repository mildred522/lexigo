package com.aiproduct.vocab.domain.model

fun resolveDisplayMeaning(
    meaningZh: String,
    meaningSourceText: String,
): String = meaningZh.trim().ifBlank { meaningSourceText.trim() }
