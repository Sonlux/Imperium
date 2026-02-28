/**
 * @file main.c
 * @brief ESP32 MH-Z19 CO2 Sensor Node - Main Application
 */

#include <stdio.h>
#include <string.h>
#include <inttypes.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_system.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "driver/gpio.h"
#include "esp_http_server.h"

#include "config.h"
#include "mhz19.h"
#include "wifi_handler.h"
#include "mqtt_handler.h"

static const char *TAG = TAG_MAIN;
static uint32_t publish_interval_ms = DEFAULT_PUBLISH_INTERVAL_MS;

// Global metrics counters
static uint32_t g_readings_total = 0;
static uint32_t g_readings_errors = 0;
static uint32_t g_mqtt_published = 0;
static uint32_t g_mqtt_errors = 0;
static int16_t g_last_co2 = 0;
static int8_t g_last_temp = 0;
static uint8_t g_current_qos = 1;

// ============================================================================
// Prometheus Metrics HTTP Handler
// ============================================================================
static esp_err_t metrics_handler(httpd_req_t *req) {
    char response[2048];
    int len = snprintf(response, sizeof(response),
        "# HELP co2_ppm Current CO2 concentration in parts per million\n"
        "# TYPE co2_ppm gauge\n"
        "co2_ppm{device=\"%s\"} %d\n"
        "\n"
        "# HELP co2_temperature_celsius Temperature reading from sensor\n"
        "# TYPE co2_temperature_celsius gauge\n"
        "co2_temperature_celsius{device=\"%s\"} %d\n"
        "\n"
        "# HELP co2_readings_total Total successful CO2 readings\n"
        "# TYPE co2_readings_total counter\n"
        "co2_readings_total{device=\"%s\"} %" PRIu32 "\n"
        "\n"
        "# HELP co2_reading_errors_total Total CO2 reading errors\n"
        "# TYPE co2_reading_errors_total counter\n"
        "co2_reading_errors_total{device=\"%s\"} %" PRIu32 "\n"
        "\n"
        "# HELP mqtt_messages_published_total Total MQTT messages published\n"
        "# TYPE mqtt_messages_published_total counter\n"
        "mqtt_messages_published_total{device=\"%s\"} %" PRIu32 "\n"
        "\n"
        "# HELP mqtt_publish_errors_total Total MQTT publish errors\n"
        "# TYPE mqtt_publish_errors_total counter\n"
        "mqtt_publish_errors_total{device=\"%s\"} %" PRIu32 "\n"
        "\n"
        "# HELP co2_publish_interval_ms Current publish interval in milliseconds\n"
        "# TYPE co2_publish_interval_ms gauge\n"
        "co2_publish_interval_ms{device=\"%s\"} %" PRIu32 "\n"
        "\n"
        "# HELP mqtt_qos_level Current MQTT QoS level\n"
        "# TYPE mqtt_qos_level gauge\n"
        "mqtt_qos_level{device=\"%s\"} %d\n"
        "\n"
        "# HELP co2_sensor_online Sensor online status (1=online, 0=offline)\n"
        "# TYPE co2_sensor_online gauge\n"
        "co2_sensor_online{device=\"%s\"} %d\n"
        "\n"
        "# HELP co2_sensor_warmed_up Sensor warm-up status (1=ready, 0=warming)\n"
        "# TYPE co2_sensor_warmed_up gauge\n"
        "co2_sensor_warmed_up{device=\"%s\"} %d\n"
        "\n"
        "# HELP wifi_rssi_dbm WiFi signal strength in dBm\n"
        "# TYPE wifi_rssi_dbm gauge\n"
        "wifi_rssi_dbm{device=\"%s\"} %d\n",
        DEVICE_ID, g_last_co2,
        DEVICE_ID, g_last_temp,
        DEVICE_ID, g_readings_total,
        DEVICE_ID, g_readings_errors,
        DEVICE_ID, g_mqtt_published,
        DEVICE_ID, g_mqtt_errors,
        DEVICE_ID, publish_interval_ms,
        DEVICE_ID, g_current_qos,
        DEVICE_ID, (mqtt_is_connected() ? 1 : 0),
        DEVICE_ID, (mhz19_is_warmed_up() ? 1 : 0),
        DEVICE_ID, wifi_get_rssi()
    );
    
    httpd_resp_set_type(req, "text/plain");
    httpd_resp_send(req, response, len);
    return ESP_OK;
}

static httpd_handle_t start_metrics_server(void) {
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    config.server_port = METRICS_HTTP_PORT;
    config.stack_size = METRICS_HTTP_STACK;
    
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
    }
    return server;
}

// ============================================================================
// LED Status Task
// ============================================================================
static void led_task(void *pvParameters) {
    gpio_reset_pin(LED_GPIO);
    gpio_set_direction(LED_GPIO, GPIO_MODE_OUTPUT);
    
    while (1) {
        if (wifi_is_connected() && mqtt_is_connected() && mhz19_is_warmed_up()) {
            // Normal operation - slow blink
            gpio_set_level(LED_GPIO, 1);
            vTaskDelay(pdMS_TO_TICKS(LED_BLINK_NORMAL));
            gpio_set_level(LED_GPIO, 0);
            vTaskDelay(pdMS_TO_TICKS(LED_BLINK_NORMAL));
        } else {
            // Error or warming up - fast blink
            gpio_set_level(LED_GPIO, 1);
            vTaskDelay(pdMS_TO_TICKS(LED_BLINK_ERROR));
            gpio_set_level(LED_GPIO, 0);
            vTaskDelay(pdMS_TO_TICKS(LED_BLINK_ERROR));
        }
    }
}

// ============================================================================
// Sensor Reading & Publishing Task
// ============================================================================
static void sensor_task(void *pvParameters) {
    mhz19_data_t sensor_data;
    uint32_t last_publish = 0;
    
    ESP_LOGI(TAG, "Sensor task started");
    
    // Skip waiting for warm-up during debugging
    ESP_LOGI(TAG, "DEBUG: Skipping warm-up wait for stability testing");
    vTaskDelay(pdMS_TO_TICKS(5000));  // Just wait 5 seconds
    
    ESP_LOGI(TAG, "Starting measurement loop...");
    
    while (1) {
        uint32_t now = xTaskGetTickCount() * portTICK_PERIOD_MS;
        
        // Read sensor data (with error handling)
        ESP_LOGD(TAG, "Attempting sensor read...");
        esp_err_t ret = mhz19_read_data(&sensor_data);
        if (ret == ESP_OK && sensor_data.valid) {
            g_readings_total++;
            g_last_co2 = sensor_data.co2_ppm;
            g_last_temp = sensor_data.temperature;
            
            ESP_LOGI(TAG, "CO2: %u ppm, Temp: %d°C (read #%" PRIu32 ")", 
                     sensor_data.co2_ppm, sensor_data.temperature, g_readings_total);
            
            // Check for unsafe CO2 levels
            if (sensor_data.co2_ppm > 2000) {
                ESP_LOGW(TAG, "⚠️  High CO2 detected: %u ppm", sensor_data.co2_ppm);
            }
            
            // Publish telemetry if interval elapsed
            if (mqtt_is_connected() && (now - last_publish >= publish_interval_ms)) {
                ret = mqtt_publish_telemetry(&sensor_data);
                if (ret == ESP_OK) {
                    last_publish = now;
                    g_mqtt_published++;
                    ESP_LOGD(TAG, "Telemetry published");
                } else {
                    g_mqtt_errors++;
                }
            }
        } else {
            g_readings_errors++;
            ESP_LOGW(TAG, "Failed to read sensor data (err=%d)", ret);
        }
        
        // Wait before next read (minimum 2 seconds per MH-Z19 spec)
        vTaskDelay(pdMS_TO_TICKS(MHZ19_READ_INTERVAL_MS));
    }
}

// ============================================================================
// MQTT Command Handler
// ============================================================================
void handle_mqtt_command(const mqtt_command_t *cmd) {
    if (cmd == NULL || strlen(cmd->command) == 0) {
        ESP_LOGW(TAG, "Invalid command received");
        return;
    }
    
    ESP_LOGI(TAG, "Processing command: %s", cmd->command);
    
    if (strcmp(cmd->command, "SET_PUBLISH_INTERVAL") == 0) {
        if (cmd->interval_ms >= MIN_PUBLISH_INTERVAL_MS && 
            cmd->interval_ms <= MAX_PUBLISH_INTERVAL_MS) {
            publish_interval_ms = cmd->interval_ms;
            ESP_LOGI(TAG, "Publish interval set to %lu ms", publish_interval_ms);
            mqtt_publish_status("interval_updated");
        } else {
            ESP_LOGW(TAG, "Invalid interval: %d ms", cmd->interval_ms);
        }
    }
    else if (strcmp(cmd->command, "CALIBRATE_ZERO") == 0) {
        ESP_LOGI(TAG, "Calibrating zero point (400 ppm)");
        esp_err_t ret = mhz19_calibrate_zero();
        mqtt_publish_status(ret == ESP_OK ? "calibration_success" : "calibration_failed");
    }
    else if (strcmp(cmd->command, "SET_DETECTION_RANGE") == 0) {
        ESP_LOGI(TAG, "Setting detection range to %d ppm", cmd->range_ppm);
        esp_err_t ret = mhz19_set_detection_range(cmd->range_ppm);
        mqtt_publish_status(ret == ESP_OK ? "range_updated" : "range_update_failed");
    }
    else if (strcmp(cmd->command, "SET_ABC") == 0) {
        ESP_LOGI(TAG, "%s ABC", cmd->enabled ? "Enabling" : "Disabling");
        esp_err_t ret = mhz19_set_abc(cmd->enabled);
        mqtt_publish_status(ret == ESP_OK ? "abc_updated" : "abc_update_failed");
    }
    else if (strcmp(cmd->command, "GET_INFO") == 0) {
        mhz19_config_t config;
        if (mhz19_get_config(&config) == ESP_OK) {
            ESP_LOGI(TAG, "Sensor info: range=%u ppm, ABC=%s, warmed_up=%s",
                     config.detection_range,
                     config.abc_enabled ? "enabled" : "disabled",
                     config.is_warmed_up ? "yes" : "no");
        }
        mqtt_publish_status("info_requested");
    }
    else if (strcmp(cmd->command, "SET_QOS") == 0) {
        if (cmd->qos_level >= 0 && cmd->qos_level <= 2) {
            g_current_qos = cmd->qos_level;
            ESP_LOGI(TAG, "QoS level set to %d", g_current_qos);
            mqtt_publish_status("qos_updated");
        } else {
            ESP_LOGW(TAG, "Invalid QoS level: %d", cmd->qos_level);
        }
    }
    else {
        ESP_LOGW(TAG, "Unknown command: %s", cmd->command);
    }
}

// ============================================================================
// Main Application
// ============================================================================
void app_main(void) {
    ESP_LOGI(TAG, "═══════════════════════════════════════════");
    ESP_LOGI(TAG, "  ESP32 MH-Z19 CO2 Sensor Node");
    ESP_LOGI(TAG, "  Device: %s", DEVICE_ID);
    ESP_LOGI(TAG, "  Version: %s", FIRMWARE_VERSION);
    ESP_LOGI(TAG, "═══════════════════════════════════════════");
    
    // Initialize NVS
    ESP_LOGI(TAG, "Step 1: Initializing NVS...");
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);
    ESP_LOGI(TAG, "✓ NVS initialized");
    
    // Initialize MH-Z19 sensor
    ESP_LOGI(TAG, "Step 2: Initializing MH-Z19 sensor...");
    ret = mhz19_init();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "MH-Z19 init failed: %d - continuing anyway", ret);
    } else {
        ESP_LOGI(TAG, "✓ MH-Z19 initialized (warming up for 3 minutes)");
    }
    
    // Initialize WiFi
    ESP_LOGI(TAG, "Step 3: Connecting to WiFi...");
    ESP_ERROR_CHECK(wifi_init_sta());
    ESP_LOGI(TAG, "✓ WiFi connected (RSSI: %d dBm)", wifi_get_rssi());
    
    // Give system time to stabilize after WiFi
    ESP_LOGI(TAG, "Step 4: Stabilizing system...");
    vTaskDelay(pdMS_TO_TICKS(1000));
    
    // Start Prometheus metrics HTTP server
    ESP_LOGI(TAG, "Step 4b: Starting metrics server...");
    start_metrics_server();
    ESP_LOGI(TAG, "✓ Metrics available at http://<ip>:%d/metrics", METRICS_HTTP_PORT);
    
    // Initialize MQTT
    ESP_LOGI(TAG, "Step 5: Connecting to MQTT broker...");
    ret = mqtt_init();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "MQTT init failed: %d", ret);
    }
    ESP_LOGI(TAG, "Waiting for MQTT connection...");
    vTaskDelay(pdMS_TO_TICKS(3000));  // Wait for MQTT connection
    ESP_LOGI(TAG, "✓ MQTT setup complete");
    
    // Create tasks
    ESP_LOGI(TAG, "Step 6: Creating tasks...");
    xTaskCreate(led_task, "LED", LED_TASK_STACK, NULL, LED_TASK_PRIORITY, NULL);
    xTaskCreate(sensor_task, "SENSOR", SENSOR_TASK_STACK, NULL, SENSOR_TASK_PRIORITY, NULL);
    
    ESP_LOGI(TAG, "═══════════════════════════════════════════");
    ESP_LOGI(TAG, "  System initialized successfully!");
    ESP_LOGI(TAG, "  Monitoring CO2 levels...");
    ESP_LOGI(TAG, "═══════════════════════════════════════════");
    
    // Main loop (monitoring)
    while (1) {
        if (!wifi_is_connected()) {
            ESP_LOGW(TAG, "WiFi disconnected, attempting reconnect...");
        }
        if (!mqtt_is_connected()) {
            ESP_LOGW(TAG, "MQTT disconnected");
        }
        vTaskDelay(pdMS_TO_TICKS(30000));  // Check every 30 seconds
    }
}
