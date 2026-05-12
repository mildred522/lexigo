package com.aiproduct.vocab.ui.personalization

import java.time.LocalDate

data class DailyCoverContent(
    val title: String,
    val subtitle: String,
)

object DailyCoverCatalog {
    private val covers = listOf(
        DailyCoverContent(
            title = "把今天的 10 个词吃透",
            subtitle = "先做判断，再做拼写，今天只解决眼前这一轮。",
        ),
        DailyCoverContent(
            title = "先稳住手感，再拉高正确率",
            subtitle = "保持节奏，错词会回炉，不需要一次全对。",
        ),
        DailyCoverContent(
            title = "今天适合清掉一点复习压力",
            subtitle = "把到期词先处理掉，新词会更轻松。",
        ),
        DailyCoverContent(
            title = "让记忆留下痕迹",
            subtitle = "看词义、听发音、回拼写，形成完整的一次通过。",
        ),
        DailyCoverContent(
            title = "不用学很多，先学扎实",
            subtitle = "完成这一轮，比盲目加量更重要。",
        ),
    )

    fun coverFor(date: LocalDate): DailyCoverContent {
        val index = Math.floorMod(date.toEpochDay().toInt(), covers.size)
        return covers[index]
    }
}
