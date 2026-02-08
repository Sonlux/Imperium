/**
 * ESP32 Audio Node - Main Entry Point
 * Imperium IBN Framework Integration
 * 
 * Features:
 * - I2S audio capture from INMP441 microphone
 * - MQTT publishing to Raspberry Pi broker
 * - Policy-based control (QoS, sample rate, enable/disable)
 * - Prometheus metrics endpoint
 * - Auto-reconnection and error recovery
 */

#include <stdio.h>
#include <string.h>
#include <inttypes.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_system.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "esp_netif.h"
#include "esp_http_server.h"
#include "driver/gpio.h"

#include "config.h"
#include "i2s_audio.h"
#include "mqtt_handler.h"
#include "policy_handler.h"

static const char *TAG = "MAIN";

// WiFi event handler
static void wifi_event_handler(void* arg, esp_event_base_t event_base,
                               int32_t event_id, void* event_data) {
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        ESP_LOGW(TAG, "WiFi disconnected, reconnecting...");
        esp_wifi_connect();
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t* event = (ip_event_got_ip_t*) event_data;
        ESP_LOGI(TAG, "Got IP: " IPSTR, IP2STR(&event->ip_info.ip));
    }
}

// Initialize WiFi
static void wifi_init() {
    ESP_LOGI(TAG, "Initializing WiFi...");
    
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_sta();
    
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));
    
    ESP_ERROR_CHECK(esp_event_handler_register(WIFI_EVENT, ESP_EVENT_ANY_ID, 
                                               &wifi_event_handler, NULL));
    ESP_ERROR_CHECK(esp_event_handler_register(IP_EVENT, IP_EVENT_STA_GOT_IP, 
                                               &wifi_event_handler, NULL));
    
    wifi_config_t wifi_config = {};
    strcpy((char*)wifi_config.sta.ssid, WIFI_SSID);
    strcpy((char*)wifi_config.sta.password, WIFI_PASSWORD);
    wifi_config.sta.threshold.authmode = WIFI_AUTH_WPA2_PSK;
    wifi_config.sta.pmf_cfg.capable = true;
    wifi_config.sta.pmf_cfg.required = false;
    
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));
    
    // CRITICAL: Disable WiFi power saving to prevent disconnections
    ESP_LOGI(TAG, "Disabling WiFi power save mode for stability...");
    ESP_ERROR_CHECK(esp_wifi_set_ps(WIFI_PS_NONE));
    
    ESP_ERROR_CHECK(esp_wifi_start());
    
    ESP_LOGI(TAG, "WiFi initialization complete");
}

// HTTP server for Prometheus metrics
static esp_err_t metrics_handler(httpd_req_t *req) {
    AudioStats audio_stats = g_audio.getStats();
    
    char response[2048];  // Increased buffer size for all metrics
    int len = snprintf(response, sizeof(response),
        "# HELP audio_frames_captured_total Total audio frames captured\n"
        "# TYPE audio_frames_captured_total counter\n"
        "audio_frames_captured_total{device=\"%s\"} %" PRIu32 "\n"
        "\n"
        "# HELP audio_buffer_overruns_total Audio buffer overruns\n"
        "# TYPE audio_buffer_overruns_total counter\n"
        "audio_buffer_overruns_total{device=\"%s\"} %" PRIu32 "\n"
        "\n"
        "# HELP mqtt_messages_published_total MQTT messages published\n"
        "# TYPE mqtt_messages_published_total counter\n"
        "mqtt_messages_published_total{device=\"%s\"} %" PRIu32 "\n"
        "\n"
        "# HELP mqtt_publish_errors_total MQTT publish errors\n"
        "# TYPE mqtt_publish_errors_total counter\n"
        "mqtt_publish_errors_total{device=\"%s\"} %" PRIu32 "\n"
        "\n"
        "# HELP audio_rms_level_db Current audio RMS level in dB\n"
        "# TYPE audio_rms_level_db gauge\n"
        "audio_rms_level_db{device=\"%s\"} %.2f\n"
        "\n"
        "# HELP audio_peak_amplitude Current audio peak amplitude (0-1)\n"
        "# TYPE audio_peak_amplitude gauge\n"
        "audio_peak_amplitude{device=\"%s\"} %.4f\n"
        "\n"
        "# HELP mqtt_qos_level Current MQTT QoS level\n"
        "# TYPE mqtt_qos_level gauge\n"
        "mqtt_qos_level{device=\"%s\"} %d\n"
        "\n"
        "# HELP audio_sample_rate_hz Current audio sample rate in Hz\n"
        "# TYPE audio_sample_rate_hz gauge\n"
        "audio_sample_rate_hz{device=\"%s\"} %" PRIu32 "\n"
        "\n"
        "# HELP audio_gain_multiplier Current audio gain multiplier\n"
        "# TYPE audio_gain_multiplier gauge\n"
        "audio_gain_multiplier{device=\"%s\"} %.2f\n"
        "\n"
        "# HELP telemetry_publish_interval_ms Telemetry publish interval in milliseconds\n"
        "# TYPE telemetry_publish_interval_ms gauge\n"
        "telemetry_publish_interval_ms{device=\"%s\"} %" PRIu32 "\n",
        DEVICE_ID, audio_stats.frames_captured,
        DEVICE_ID, audio_stats.buffer_overruns,
        DEVICE_ID, g_mqtt.getPublishCount(),
        DEVICE_ID, g_mqtt.getPublishErrorCount(),
        DEVICE_ID, audio_stats.rms_level_db,
        DEVICE_ID, audio_stats.peak_amplitude,
        DEVICE_ID, g_mqtt.getQoS(),
        DEVICE_ID, g_audio.getSampleRate(),
        DEVICE_ID, g_audio.getGain(),
        DEVICE_ID, g_policy.getPublishInterval()
    );
    
    httpd_resp_set_type(req, "text/plain");
    httpd_resp_send(req, response, len);
    return ESP_OK;
}

static httpd_handle_t start_metrics_server() {
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    config.server_port = METRICS_HTTP_PORT;
    config.ctrl_port = 32768;
    config.stack_size = 8192;  // Increase from default 4096 to prevent stack overflow
    
    httpd_handle_t server = NULL;
    
    if (httpd_start(&server, &config) == ESP_OK) {
        httpd_uri_t metrics_uri = {
            .uri = "/metrics",
            .method = HTTP_GET,
            .handler = metrics_handler,
            .user_ctx = NULL
        };
        httpd_register_uri_handler(server, &metrics_uri);
        ESP_LOGI(TAG, "Metrics server started on port %d", METRICS_HTTP_PORT);
    } else {
        ESP_LOGE(TAG, "Failed to start metrics server");
    }
    
    return server;
}

// Audio publishing task
static void audio_publish_task(void *param) {
    ESP_LOGI(TAG, "Audio publish task started");
    
    AudioFrame frame;
    uint32_t last_telemetry_ms = 0;
    
    while (true) {
        // Get audio frame (blocking with timeout)
        if (!g_audio.getFrame(&frame, 1000)) {
            continue;
        }
        
        // Check if device is enabled
        if (!g_policy.isEnabled()) {
            vTaskDelay(pdMS_TO_TICKS(100));
            continue;
        }
        
        // Publish audio data (raw PCM for now)
        if (g_mqtt.isConnected()) {
            bool success = g_mqtt.publishAudio(
                (uint8_t*)frame.samples,
                frame.sample_count * sizeof(int16_t),
                g_mqtt.getQoS()
            );
            
            if (!success) {
                ESP_LOGW(TAG, "Failed to publish audio frame %" PRIu32, frame.sequence_number);
            }
        }
        
        // Publish telemetry based on configured interval
        uint32_t now = xTaskGetTickCount() * portTICK_PERIOD_MS;
        uint32_t interval = g_policy.getPublishInterval();
        if (now - last_telemetry_ms > interval) {
            AudioStats stats = g_audio.getStats();
            char telemetry[300];
            snprintf(telemetry, sizeof(telemetry),
                "{\"device_id\":\"%s\","
                "\"frames_captured\":%" PRIu32 ","
                "\"buffer_overruns\":%" PRIu32 ","
                "\"rms_db\":%.2f,"
                "\"peak\":%.4f,"
                "\"mqtt_qos\":%d,"
                "\"sample_rate\":%" PRIu32 ","
                "\"audio_gain\":%.2f,"
                "\"publish_interval_ms\":%" PRIu32 ","
                "\"uptime_ms\":%" PRIu32 "}",
                DEVICE_ID,
                stats.frames_captured,
                stats.buffer_overruns,
                stats.rms_level_db,
                stats.peak_amplitude,
                g_mqtt.getQoS(),
                g_audio.getSampleRate(),
                g_audio.getGain(),
                g_policy.getPublishInterval(),
                now
            );
            
            g_mqtt.publishTelemetry(telemetry);
            last_telemetry_ms = now;
        }
        
        g_audio.releaseFrame(&frame);
    }
}

// Heartbeat task
static void heartbeat_task(void *param) {
    while (true) {
        if (g_mqtt.isConnected()) {
            char status[128];
            snprintf(status, sizeof(status), 
                "{\"device_id\":\"%s\",\"status\":\"online\",\"timestamp\":%" PRIu32 "}",
                DEVICE_ID, (uint32_t)(xTaskGetTickCount() * portTICK_PERIOD_MS));
            g_mqtt.publishStatus(status);
        }
        vTaskDelay(pdMS_TO_TICKS(10000));  // Every 10 seconds
    }
}

// Main application entry
extern "C" void app_main(void) {
    ESP_LOGI(TAG, "=== ESP32 Audio Node Starting ===");
    ESP_LOGI(TAG, "Device ID: %s", DEVICE_ID);
    ESP_LOGI(TAG, "Firmware: %s", FIRMWARE_VERSION);
    
    // Initialize NVS
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);
    
    // Initialize WiFi
    wifi_init();
    
    // Wait for WiFi connection
    ESP_LOGI(TAG, "Waiting for WiFi connection...");
    vTaskDelay(pdMS_TO_TICKS(5000));
    
    // Initialize audio capture
    if (!g_audio.init()) {
        ESP_LOGE(TAG, "Failed to initialize audio");
        return;
    }
    
    // Initialize MQTT
    if (!g_mqtt.init()) {
        ESP_LOGE(TAG, "Failed to initialize MQTT");
        return;
    }
    
    // Set up control message callback
    g_mqtt.subscribeControl([](const char* topic, const char* data, int len) {
        g_policy.processControlMessage(data, len);
    });
    
    // Connect to MQTT broker
    g_mqtt.connect();
    
    // Wait for MQTT connection
    ESP_LOGI(TAG, "Waiting for MQTT connection...");
    int retry = 0;
    while (!g_mqtt.isConnected() && retry < 30) {
        vTaskDelay(pdMS_TO_TICKS(1000));
        retry++;
    }
    
    if (!g_mqtt.isConnected()) {
        ESP_LOGW(TAG, "MQTT not connected, continuing anyway...");
    }
    
    // Publish device metadata
    char metadata[256];
    snprintf(metadata, sizeof(metadata),
        "{\"device_id\":\"%s\","
        "\"type\":\"%s\","
        "\"firmware\":\"%s\","
        "\"sample_rate\":%d,"
        "\"channels\":%d,"
        "\"bits_per_sample\":%d}",
        DEVICE_ID, DEVICE_TYPE, FIRMWARE_VERSION,
        I2S_SAMPLE_RATE, I2S_CHANNELS, I2S_BITS_PER_SAMPLE
    );
    g_mqtt.publishMetadata(metadata);
    
    // Start audio capture
    if (!g_audio.start()) {
        ESP_LOGE(TAG, "Failed to start audio capture");
        return;
    }
    
    // Start metrics server
    if (METRICS_ENABLED) {
        start_metrics_server();
    }
    
    // Create audio publishing task
    xTaskCreate(audio_publish_task, "audio_pub", 4096, NULL, TASK_PRIORITY_MQTT, NULL);
    
    // Create heartbeat task
    xTaskCreate(heartbeat_task, "heartbeat", 2048, NULL, TASK_PRIORITY_METRICS, NULL);
    
    ESP_LOGI(TAG, "=== ESP32 Audio Node Running ===");
    ESP_LOGI(TAG, "Publishing audio to: %s", TOPIC_AUDIO_DATA);
    ESP_LOGI(TAG, "Listening for control on: %s", TOPIC_CONTROL);
    ESP_LOGI(TAG, "Metrics available at: http://<device-ip>:%d/metrics", METRICS_HTTP_PORT);
}
