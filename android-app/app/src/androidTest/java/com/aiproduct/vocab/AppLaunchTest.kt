package com.aiproduct.vocab

import androidx.compose.ui.test.assertTextContains
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performTextInput
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class AppLaunchTest {
    @get:Rule
    val rule = createAndroidComposeRule<MainActivity>()

    @Test
    fun showsSearchShell() {
        val title = rule.activity.getString(R.string.search_title)
        val hint = rule.activity.getString(R.string.search_hint)
        val starredTab = rule.activity.getString(R.string.tab_starred)
        val reviewTab = rule.activity.getString(R.string.tab_review)

        rule.onNodeWithText(title).fetchSemanticsNode()
        rule.onNodeWithText(hint).fetchSemanticsNode()
        rule.onNodeWithText(starredTab).fetchSemanticsNode()
        rule.onNodeWithText(reviewTab).fetchSemanticsNode()

        rule.onNodeWithTag("search_input")
            .fetchSemanticsNode()

        rule.onNodeWithTag("search_input")
            .performTextInput("abandon")
        rule.onNodeWithTag("search_input")
            .assertTextContains("abandon")
    }

    @Test
    fun keepsQueryAfterActivityRecreate() {
        rule.onNodeWithTag("search_input")
            .fetchSemanticsNode()

        rule.onNodeWithTag("search_input")
            .performTextInput("persisted")
        rule.onNodeWithTag("search_input")
            .assertTextContains("persisted")

        rule.activityRule.scenario.recreate()
        rule.waitForIdle()

        rule.onNodeWithTag("search_input")
            .fetchSemanticsNode()
        rule.onNodeWithTag("search_input")
            .assertTextContains("persisted")
    }
}
