package com.aiproduct.vocab.util

data class MeasuredValue<T>(
    val value: T,
    val durationMillis: Long,
)

inline fun <T> measureDurationMillis(
    nowMillis: () -> Long,
    block: () -> T,
): MeasuredValue<T> {
    val startedAt = nowMillis()
    val value = block()
    val finishedAt = nowMillis()
    return MeasuredValue(
        value = value,
        durationMillis = (finishedAt - startedAt).coerceAtLeast(0L),
    )
}
