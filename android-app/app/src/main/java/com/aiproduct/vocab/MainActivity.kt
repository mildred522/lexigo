package com.aiproduct.vocab

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import com.aiproduct.vocab.ui.AppRoot
import com.aiproduct.vocab.ui.theme.VocabTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            VocabTheme {
                AppRoot()
            }
        }
    }
}
