package com.arthsaarthi.app

import android.app.Service
import android.content.Intent
import android.os.Binder
import android.os.IBinder
import android.util.Log
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import java.net.ServerSocket
import java.util.concurrent.atomic.AtomicBoolean

/**
 * Android Service that hosts the FastAPI/Uvicorn backend via Chaquopy.
 *
 * This service:
 * 1. Finds a free port
 * 2. Starts the Python FastAPI server on that port
 * 3. Exposes the port to the Capacitor plugin
 *
 * The architecture mirrors the Electron desktop app where a child process
 * runs the backend and the frontend connects via HTTP to localhost.
 */
class BackendService : Service() {

    companion object {
        private const val TAG = "BackendService"
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
        startBackendServer()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        Log.i(TAG, "BackendService onStartCommand")
        startBackendServer()
        return START_STICKY
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
