package com.arthsaarthi.app

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Binder
import android.os.Build
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import java.util.concurrent.atomic.AtomicBoolean

/**
 * Android Foreground Service that hosts the FastAPI/Uvicorn backend via Chaquopy.
 *
 * Runs as a Foreground Service to prevent Android ActivityManager from killing
 * the local Python HTTP server due to app idle or background state.
 */
class BackendService : Service() {

    companion object {
        private const val TAG = "BackendService"
        private const val CHANNEL_ID = "arthsaarthi_backend_channel"
        private const val NOTIFICATION_ID = 1001

        var backendPort: Int = 0
            private set
        val isRunning = AtomicBoolean(false)

        @JvmStatic
        fun updatePort(port: Int) {
            Log.i(TAG, "Updating backend port to $port")
            backendPort = port
        }
    }

    private val binder = BackendBinder()
    private var serverThread: Thread? = null

    inner class BackendBinder : Binder() {
        fun getService(): BackendService = this@BackendService
    }

    override fun onBind(intent: Intent?): IBinder = binder

    override fun onCreate() {
        super.onCreate()
        Log.i(TAG, "BackendService onCreate")
        createNotificationChannel()
        startForegroundNotification()
        startBackendServer()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        Log.i(TAG, "BackendService onStartCommand")
        startForegroundNotification()
        startBackendServer()
        return START_STICKY
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val name = "ArthSaarthi Engine"
            val descriptionText = "Hosts the local Python backend server"
            val importance = NotificationManager.IMPORTANCE_LOW
            val channel = NotificationChannel(CHANNEL_ID, name, importance).apply {
                description = descriptionText
            }
            val notificationManager: NotificationManager =
                getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            notificationManager.createNotificationChannel(channel)
        }
    }

    private fun startForegroundNotification() {
        val notification: Notification = NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("ArthSaarthi Local Server")
            .setContentText("Local financial engine active")
            .setSmallIcon(android.R.drawable.stat_notify_sync)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setOngoing(true)
            .build()

        startForeground(NOTIFICATION_ID, notification)
    }

    private fun startBackendServer() {
        if (!isRunning.compareAndSet(false, true)) {
            Log.w(TAG, "Backend server is already running or starting...")
            return
        }

        Log.i(TAG, "Starting backend server thread...")

        // Initialize Chaquopy if not already done
        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(this))
        }

        // Initial port 0 means let Python choose
        backendPort = 0

        serverThread = Thread {
            try {
                val py = Python.getInstance()
                val runServer = py.getModule("run_server")

                // Pass the app's internal data directory
                val dataDir = filesDir.absolutePath
                Log.i(TAG, "Data directory: $dataDir")

                // Pass port 0 to indicate dynamic selection
                runServer.callAttr("start", 0, dataDir)
            } catch (e: Exception) {
                Log.e(TAG, "Backend server crashed", e)
                isRunning.set(false)
            }
        }.apply {
            isDaemon = true
            name = "arthsaarthi-backend"
            start()
        }

        Log.i(TAG, "Backend server thread started (awaiting port update from Python)")
    }

    override fun onDestroy() {
        Log.i(TAG, "BackendService onDestroy — stopping backend")
        isRunning.set(false)
        serverThread?.interrupt()
        serverThread = null
        super.onDestroy()
    }
}
