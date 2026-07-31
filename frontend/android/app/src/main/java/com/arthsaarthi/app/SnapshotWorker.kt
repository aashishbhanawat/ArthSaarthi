package com.arthsaarthi.app

import android.content.Context
import android.content.Intent
import android.util.Log
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.withContext
import java.io.OutputStream
import java.net.HttpURLConnection
import java.net.URL

class SnapshotWorker(appContext: Context, workerParams: WorkerParameters) :
    CoroutineWorker(appContext, workerParams) {

    companion object {
        private const val TAG = "SnapshotWorker"
        private const val HEALTH_CHECK_INTERVAL_MS = 1000L
        private const val HEALTH_CHECK_MAX_RETRIES = 60 // 60 seconds max wait
    }

    override suspend fun doWork(): Result = withContext(Dispatchers.IO) {
        Log.i(TAG, "Starting background daily snapshot worker...")

        // 1. Ensure the BackendService is running
        val intent = Intent(applicationContext, BackendService::class.java)
        applicationContext.startService(intent)

        // 2. Wait for backend to be ready
        val port = waitForBackendReady()
        if (port <= 0) {
            Log.e(TAG, "Backend failed to start or become healthy in time.")
            return@withContext Result.failure()
        }

        // 3. Make the API call to trigger snapshots
        try {
            val url = URL("http://127.0.0.1:$port/api/v1/system/snapshots/run-daily")
            val conn = url.openConnection() as HttpURLConnection
            conn.requestMethod = "POST"
            conn.connectTimeout = 5000
            conn.readTimeout = 60000 // Snapshots might take a minute for many portfolios
            
            // Send empty POST body
            conn.doOutput = true
            conn.setRequestProperty("Content-Type", "application/json")
            conn.setRequestProperty("Accept", "application/json")
            val os: OutputStream = conn.outputStream
            val input = "{}"
            os.write(input.toByteArray(Charsets.UTF_8))
            os.close()

            val responseCode = conn.responseCode
            if (responseCode in 200..299) {
                val responseStr = conn.inputStream.bufferedReader().use { it.readText() }
                Log.i(TAG, "Snapshot completed successfully: $responseStr")
                conn.disconnect()
                return@withContext Result.success()
            } else {
                val errStr = conn.errorStream?.bufferedReader()?.use { it.readText() } ?: ""
                Log.e(TAG, "Snapshot API failed with status $responseCode: $errStr")
                conn.disconnect()
                return@withContext Result.retry()
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error calling snapshot API", e)
            return@withContext Result.retry()
        }
    }

    private suspend fun waitForBackendReady(): Int {
        for (i in 0 until HEALTH_CHECK_MAX_RETRIES) {
            val port = BackendService.backendPort
            if (port > 0 && BackendService.isRunning.get()) {
                try {
                    val url = URL("http://127.0.0.1:$port/api/v1/auth/status")
                    val conn = url.openConnection() as HttpURLConnection
                    conn.connectTimeout = 2000
                    conn.readTimeout = 2000
                    conn.requestMethod = "GET"
                    val responseCode = conn.responseCode
                    conn.disconnect()

                    if (responseCode in 200..299) {
                        Log.i(TAG, "Backend is ready on port $port for background worker")
                        return port
                    }
                } catch (e: Exception) {
                    // Server not yet ready
                }
            }
            delay(HEALTH_CHECK_INTERVAL_MS)
        }
        return -1
    }
}
