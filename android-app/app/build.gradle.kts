plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

val repoRootDir = rootProject.projectDir.parentFile
val generatedDictionaryAssetsDir = layout.buildDirectory.dir("generated/assets/dictionary")

val syncAndroidDictionaryAssets = tasks.register("syncAndroidDictionaryAssets", Exec::class) {
    group = "build setup"
    description = "Sync packaged dictionary assets into app/build/generated/assets/dictionary."
    workingDir = repoRootDir
    commandLine(
        "python",
        "scripts/sync_android_dictionary_assets.py",
        "--package-dir",
        repoRootDir.resolve("artifacts/package").path,
        "--assets-dir",
        generatedDictionaryAssetsDir.get().asFile.path,
    )

    inputs.files(
        repoRootDir.resolve("artifacts/package/dictionary.db"),
        repoRootDir.resolve("artifacts/package/manifest.json"),
    )
    outputs.files(
        generatedDictionaryAssetsDir.map { it.file("dictionary.db").asFile },
        generatedDictionaryAssetsDir.map { it.file("manifest.json").asFile },
    )
}

tasks.named("preBuild") {
    dependsOn(syncAndroidDictionaryAssets)
}

android {
    namespace = "com.aiproduct.vocab"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.aiproduct.vocab"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro",
            )
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    buildFeatures {
        compose = true
    }

    androidResources {
        noCompress += "db"
    }

    sourceSets {
        getByName("main").assets.srcDir(generatedDictionaryAssetsDir)
    }
}

dependencies {
    val composeBom = platform("androidx.compose:compose-bom:2024.10.01")

    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.6")
    implementation("androidx.lifecycle:lifecycle-viewmodel-ktx:2.8.6")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.6")
    implementation("androidx.activity:activity-compose:1.9.2")
    implementation(composeBom)
    androidTestImplementation(composeBom)
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")

    testImplementation("junit:junit:4.13.2")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.8.1")
    testImplementation("org.json:json:20240303")

    androidTestImplementation("androidx.test.ext:junit:1.2.1")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.6.1")
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")

    debugImplementation("androidx.compose.ui:ui-tooling")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
}
