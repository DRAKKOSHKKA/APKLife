package ru.apklife.app

import android.annotation.SuppressLint
import android.graphics.Bitmap
import android.net.Uri
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.view.View
import android.view.animation.AccelerateDecelerateInterpolator
import android.webkit.ConsoleMessage
import android.webkit.WebChromeClient
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.LinearLayout
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import com.google.android.material.button.MaterialButton
import java.net.InetSocketAddress
import java.net.Socket

/**
 * MainActivity — единственная Activity приложения APKLife для Android.
 *
 * Архитектура приложения:
 * 1. При запуске: показываем splash-overlay с прогресс-индикатором
 * 2. В фоновом потоке: инициализируем Chaquopy (встроенный Python) и запускаем Flask-сервер
 * 3. Ждём пока Flask привяжется к порту 5000 на localhost
 * 4. WebView загружает http://127.0.0.1:5000 — полноценное расписание
 * 5. Пользователь взаимодействует с расписанием через WebView
 *
 * Особенности:
 * - Pull-to-refresh (SwipeRefreshLayout) для перезагрузки страницы
 * - Кнопка "Назад" навигирует по истории WebView вместо закрытия приложения
 * - Splash-экран с анимацией исчезновения
 * - Экран ошибки с кнопкой "Повторить"
 * - Полная поддержка JavaScript, DOM Storage, cookie
 */
class MainActivity : AppCompatActivity() {

    companion object {
        private const val TAG = "APKLife"

        /** Адрес локального Flask-сервера */
        private const val SERVER_HOST = "127.0.0.1"
        private const val SERVER_PORT = 5000
        private const val SERVER_URL = "http://$SERVER_HOST:$SERVER_PORT"

        /** Сколько раз пытаемся подключиться к серверу (раз × задержка = макс. ожидание) */
        private const val SERVER_POLL_RETRIES = 120
        private const val SERVER_POLL_DELAY_MS = 500L
    }

    // UI-элементы
    private lateinit var webView: WebView
    private lateinit var swipeRefresh: SwipeRefreshLayout
    private lateinit var splashOverlay: LinearLayout
    private lateinit var errorOverlay: LinearLayout
    private lateinit var errorMessage: TextView
    private lateinit var loadingText: TextView
    private lateinit var retryButton: MaterialButton

    // Хэндлер для работы с UI-потоком из фоновых задач
    private val mainHandler = Handler(Looper.getMainLooper())

    // Флаг: сервер успешно стартовал и WebView загрузил страницу
    private var serverReady = false

    // -------------------------------------------------------------------------
    // Lifecycle
    // -------------------------------------------------------------------------

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        setContentView(R.layout.activity_main)

        WindowCompat.setDecorFitsSystemWindows(window, true)

        WindowInsetsControllerCompat(window, window.decorView).apply {
            isAppearanceLightStatusBars = false
            isAppearanceLightNavigationBars = false
        }

        // Привязываем все UI-элементы
        bindViews()

        // Настраиваем WebView (JavaScript, DOM Storage, User Agent)
        configureWebView()

        // Настраиваем pull-to-refresh
        configureSwipeRefresh()

        // Настраиваем кнопку "Повторить" на экране ошибки
        retryButton.setOnClickListener {
            showSplash()
            startFlaskServer()
        }

        // Запускаем Flask-сервер в фоне
        startFlaskServer()
    }

    /**
     * Обработка кнопки "Назад":
     * - Если WebView может вернуться назад по истории — навигируем назад
     * - Иначе — стандартное поведение (выход из приложения)
     */
    @Suppress("DEPRECATION")
    override fun onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack()
        } else {
            super.onBackPressed()
        }
    }

    // -------------------------------------------------------------------------
    // Инициализация UI-компонентов
    // -------------------------------------------------------------------------

    private fun bindViews() {
        webView = findViewById(R.id.webView)
        swipeRefresh = findViewById(R.id.swipeRefresh)
        splashOverlay = findViewById(R.id.splashOverlay)
        errorOverlay = findViewById(R.id.errorOverlay)
        errorMessage = findViewById(R.id.errorMessage)
        loadingText = findViewById(R.id.loadingText)
        retryButton = findViewById(R.id.retryButton)
    }

    /**
     * Настройка WebView для полноценной работы веб-приложения.
     *
     * Включаем:
     * - JavaScript (обязательно для Flask-шаблонов)
     * - DOM Storage (для localStorage — кэш настроек и DEV-панели)
     * - Database Storage (для оффлайн-функционала)
     * - Zoom-контроль (пользователь может увеличить масштаб)
     * - Кастомный User-Agent с пометкой "APKLife-Android"
     */
    @SuppressLint("SetJavaScriptEnabled")
    private fun configureWebView() {
        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            databaseEnabled = true
            setSupportZoom(true)
            builtInZoomControls = true
            displayZoomControls = false
            loadWithOverviewMode = true
            useWideViewPort = true
            allowContentAccess = true

            // Кастомный User-Agent помогает серверу узнать, что запрос идёт из Android-версии
            userAgentString = "$userAgentString APKLife-Android/1.0"
        }

        // WebViewClient — перехватываем навигацию, чтобы все ссылки открывались внутри приложения
        webView.webViewClient = object : WebViewClient() {

            override fun onPageStarted(view: WebView?, url: String?, favicon: Bitmap?) {
                super.onPageStarted(view, url, favicon)
                // Пока загружается страница, показываем индикатор refresh
                if (serverReady) {
                    swipeRefresh.isRefreshing = true
                }
            }

            override fun onPageFinished(view: WebView?, url: String?) {
                super.onPageFinished(view, url)
                swipeRefresh.isRefreshing = false

                // Если это первая успешная загрузка — прячем splash
                if (!serverReady) {
                    serverReady = true
                    hideSplashWithAnimation()
                }
            }

            override fun onReceivedError(
                view: WebView?,
                request: WebResourceRequest?,
                error: WebResourceError?
            ) {
                super.onReceivedError(view, request, error)
                // Ошибка на основной странице (не подресурсе)
                if (request?.isForMainFrame == true) {
                    Log.e(TAG, "WebView error: ${error?.description}")
                }
            }

            /**
             * Все URL с нашего localhost открываем в WebView.
             * Внешние ссылки (например, ссылки на Google) — тоже в WebView,
             * потому что наше приложение самодостаточно.
             */
            override fun shouldOverrideUrlLoading(
                view: WebView?,
                request: WebResourceRequest?
            ): Boolean {
                val url = request?.url?.toString() ?: return false
                // Всё что на localhost — грузим внутри
                if (url.startsWith(SERVER_URL)) return false
                // Внешние URL тоже грузим внутри WebView (опционально)
                view?.loadUrl(url)
                return true
            }
        }

        // WebChromeClient — для отладки (console.log из JS попадает в Logcat)
        webView.webChromeClient = object : WebChromeClient() {
            override fun onConsoleMessage(consoleMessage: ConsoleMessage?): Boolean {
                consoleMessage?.let {
                    Log.d(TAG, "JS [${it.messageLevel()}]: ${it.message()} (${it.sourceId()}:${it.lineNumber()})")
                }
                return true
            }
        }
    }

    /**
     * Настройка SwipeRefreshLayout в стиле Material Design 3.
     * Цвет индикатора = primary, фон = surface.
     */
    private fun configureSwipeRefresh() {
        swipeRefresh.setColorSchemeResources(R.color.md3_primary)
        swipeRefresh.setProgressBackgroundColorSchemeResource(R.color.md3_surface_container)
        swipeRefresh.setOnRefreshListener {
            if (serverReady) {
                webView.reload()
            } else {
                swipeRefresh.isRefreshing = false
            }
        }
    }

    // -------------------------------------------------------------------------
    // Запуск Flask-сервера через Chaquopy
    // -------------------------------------------------------------------------

    /**
     * Запускает Flask-сервер в фоновом потоке:
     * 1. Инициализирует Python-интерпретатор Chaquopy
     * 2. Вызывает android_entry.start_server() — запускает Flask
     * 3. Ждёт привязки Flask к порту (polling TCP-сокетом)
     * 4. При успехе — загружает WebView; при неудаче — показывает ошибку
     */
    private fun startFlaskServer() {
        Thread {
            try {
                // Шаг 1: Инициализация Python
                updateLoadingText("Инициализация Python…")
                if (!Python.isStarted()) {
                    Python.start(AndroidPlatform(this))
                }
                Log.i(TAG, "Python runtime initialized")

                // Шаг 2: Запуск Flask-сервера
                updateLoadingText("Запуск Flask-сервера…")
                val py = Python.getInstance()
                val module = py.getModule("android_entry")
                module.callAttr("start_server")
                Log.i(TAG, "Flask server start_server() called")

                // Шаг 3: Ожидание готовности сервера
                updateLoadingText("Ожидание сервера…")
                val serverUp = waitForServer(
                    SERVER_HOST, SERVER_PORT,
                    SERVER_POLL_RETRIES, SERVER_POLL_DELAY_MS
                )

                if (serverUp) {
                    Log.i(TAG, "Flask server is ready on $SERVER_URL")
                    // Шаг 4: Загрузка WebView
                    mainHandler.post {
                        webView.loadUrl(SERVER_URL)
                    }
                } else {
                    Log.e(TAG, "Flask server failed to start within timeout")
                    mainHandler.post {
                        showError("Сервер не запустился за 60 секунд.\nПроверьте логи Chaquopy.")
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "Failed to start Flask server", e)
                mainHandler.post {
                    showError("Ошибка: ${e.localizedMessage ?: e.toString()}")
                }
            }
        }.start()
    }

    /**
     * Пробует подключиться к TCP-порту Flask-сервера.
     * Повторяет [retries] раз с задержкой [delayMs] между попытками.
     *
     * @return true если сервер ответил, false если время вышло
     */
    private fun waitForServer(host: String, port: Int, retries: Int, delayMs: Long): Boolean {
        repeat(retries) { attempt ->
            try {
                Socket().use { socket ->
                    socket.connect(InetSocketAddress(host, port), 300)
                    return true
                }
            } catch (_: Exception) {
                if (attempt % 10 == 0) {
                    Log.d(TAG, "Waiting for Flask... attempt ${attempt + 1}/$retries")
                }
                Thread.sleep(delayMs)
            }
        }
        return false
    }

    // -------------------------------------------------------------------------
    // UI: управление overlay-экранами
    // -------------------------------------------------------------------------

    /** Показать splash-overlay (скрыть ошибку и WebView) */
    private fun showSplash() {
        splashOverlay.visibility = View.VISIBLE
        errorOverlay.visibility = View.GONE
        webView.visibility = View.INVISIBLE
    }

    /** Плавно убрать splash-overlay с анимацией fade-out */
    private fun hideSplashWithAnimation() {
        splashOverlay.animate()
            .alpha(0f)
            .setDuration(400)
            .setInterpolator(AccelerateDecelerateInterpolator())
            .withEndAction {
                splashOverlay.visibility = View.GONE
                splashOverlay.alpha = 1f
                webView.visibility = View.VISIBLE
            }
            .start()
    }

    /** Показать экран ошибки с сообщением */
    private fun showError(message: String) {
        splashOverlay.visibility = View.GONE
        errorOverlay.visibility = View.VISIBLE
        errorMessage.text = message
        webView.visibility = View.INVISIBLE
    }

    /** Обновить текст под спиннером загрузки (из фонового потока) */
    private fun updateLoadingText(text: String) {
        mainHandler.post {
            loadingText.text = text
        }
    }
}
