package com.aiproduct.vocab.domain.learning

enum class LearningBand {
    BEGINNER,
    INTERMEDIATE,
    ADVANCED,
}

fun LearningBand.next(): LearningBand? = when (this) {
    LearningBand.BEGINNER -> LearningBand.INTERMEDIATE
    LearningBand.INTERMEDIATE -> LearningBand.ADVANCED
    LearningBand.ADVANCED -> null
}
