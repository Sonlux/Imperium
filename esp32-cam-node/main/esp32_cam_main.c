/*
 * ESP32-CAM OV2640 - Imperium IBN Node (ESP-IDF)
 * 
 * Device ID: esp32-cam-1
 * Hardware: AI-Thinker ESP32-CAM, OV2640 Camera
 * Framework: ESP-IDF (native C)
 * 
 * Features:
 * - WiFi connectivity
 * - MQTT camera frame publishing
 * - Dynamic control: resolution, frame rate, quality, brightness
 * - HTTP metrics endpoint
 * - Intent-Based Networking integration
 * 
 * Author: Imperium IBN Project
 * Version: 1.0.0
 * Date: 2026-02-10
 */

#include <stdio.h>
#include <string.h>
#include <inttypes.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"
#include "esp_system.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "esp_camera.h"
#include "esp_http_server.h"
#include "mqtt_client.h"
#include "cJSON.h"

// ============================================================================
// CONFIGURATION
// ============================================================================

// WiFi Settings
#define WIFI_SSID "Galaxy A56 5G A76A"
#define WIFI_PASSWORD "12345678"

// MQTT Settings
#define MQTT_BROKER_URI "mqtt://10.218.189.192:1883"
#define DEVICE_ID "esp32-cam-1"

// MQTT Topics
#define TOPIC_IMAGES "iot/esp32-cam-1/images"
#define TOPIC_TELEMETRY "iot/esp32-cam-1/telemetry"
#define TOPIC_CONTROL "iot/esp32-cam-1/control"
#define TOPIC_STATUS "iot/esp32-cam-1/status"

// Camera Configuration
typedef struct {
    framesize_t resolution;
    int quality;
    int brightness;
    int contrast;
    int saturation;
    uint32_t capture_interval_ms;
    bool enabled;
} cam_settings_t;

cam_settings_t g_cam_settings = {
    .resolution = FRAMESIZE_SVGA,  // 800x600
    .quality = 10,
    .brightness = 0,
    .contrast = 0,
    .saturation = 0,
    .capture_interval_ms = 5000,
    .enabled = true
};

// MQTT Configuration
static int mqtt_qos = 1;

// Runtime Metrics
typedef struct {
    uint32_t frames_captured;
    uint32_t frames_sent;
    uint32_t frames_error;
    uint32_t bytes_total;
    uint32_t last_frame_size;
    uint32_t last_capture_duration_ms;
    float fps;
    uint32_t wifi_reconnects;
    uint32_t mqtt_reconnects;
} metrics_t;

metrics_t metrics = {0};

// Timing
static uint32_t last_capture_time = 0;
static uint32_t last_telemetry_time = 0;
static uint32_t last_fps_calculation = 0;
static uint32_t fps_frame_count = 0;
static const uint32_t TELEMETRY_INTERVAL_MS = 10000;

// Handles
static esp_mqtt_client_handle_t mqtt_client = NULL;
static httpd_handle_t http_server = NULL;
static EventGroupHandle_t wifi_event_group;
static const int WIFI_CONNECTED_BIT = BIT0;

static const char *TAG = "ESP32-CAM";

// ============================================================================
// CAMERA PINS (AI-Thinker ESP32-CAM)
// ============================================================================

#define CAM_PIN_PWDN    32
#define CAM_PIN_RESET   -1
#define CAM_PIN_XCLK    0
#define CAM_PIN_SIOD    26
#define CAM_PIN_SIOC    27

#define CAM_PIN_D7      35
#define CAM_PIN_D6      34
#define CAM_PIN_D5      39
#define CAM_PIN_D4      36
#define CAM_PIN_D3      21
#define CAM_PIN_D2      19
#define CAM_PIN_D1      18
#define CAM_PIN_D0      5
#define CAM_PIN_VSYNC   25
#define CAM_PIN_HREF    23
#define CAM_PIN_PCLK    22

// ============================================================================
// CAMERA FUNCTIONS
// ============================================================================

static camera_config_t camera_config = {
    .pin_pwdn = CAM_PIN_PWDN,
    .pin_reset = CAM_PIN_RESET,
    .pin_xclk = CAM_PIN_XCLK,
    .pin_sscb_sda = CAM_PIN_SIOD,
    .pin_sscb_scl = CAM_PIN_SIOC,
    
    .pin_d7 = CAM_PIN_D7,
    .pin_d6 = CAM_PIN_D6,
    .pin_d5 = CAM_PIN_D5,
    .pin_d4 = CAM_PIN_D4,
    .pin_d3 = CAM_PIN_D3,
    .pin_d2 = CAM_PIN_D2,
    .pin_d1 = CAM_PIN_D1,
    .pin_d0 = CAM_PIN_D0,
    .pin_vsync = CAM_PIN_VSYNC,
    .pin_href = CAM_PIN_HREF,
    .pin_pclk = CAM_PIN_PCLK,
    
    .xclk_freq_hz = 20000000,
    .ledc_timer = LEDC_TIMER_0,
    .ledc_channel = LEDC_CHANNEL_0,
    
    .pixel_format = PIXFORMAT_JPEG,
    .frame_size = FRAMESIZE_SVGA,
    .jpeg_quality = 10,
    .fb_count = 2,
    .grab_mode = CAMERA_GRAB_LATEST
};

void init_camera(void) {
    ESP_LOGI(TAG, "Initializing camera...");
    
    esp_err_t err = esp_camera_init(&camera_config);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Camera init failed with error 0x%x", err);
        return;
    }
    
    sensor_t *s = esp_camera_sensor_get();
    if (s != NULL) {
        s->set_framesize(s, g_cam_settings.resolution);
        s->set_quality(s, g_cam_settings.quality);
        s->set_brightness(s, g_cam_settings.brightness);
        s->set_contrast(s, g_cam_settings.contrast);
        s->set_saturation(s, g_cam_settings.saturation);
    }
    
    ESP_LOGI(TAG, "Camera initialized successfully");
}

void capture_and_publish_frame(void) {
    if (!g_cam_settings.enabled || mqtt_client == NULL) {
        return;
    }
    
    uint32_t start_time = xTaskGetTickCount() * portTICK_PERIOD_MS;
    
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb) {
        ESP_LOGE(TAG, "Camera capture failed");
        metrics.frames_error++;
        return;
    }
    
    metrics.frames_captured++;
    metrics.last_frame_size = fb->len;
    metrics.last_capture_duration_ms = (xTaskGetTickCount() * portTICK_PERIOD_MS) - start_time;
    
    // Publish to MQTT
    int msg_id = esp_mqtt_client_publish(mqtt_client, TOPIC_IMAGES, (const char *)fb->buf, fb->len, mqtt_qos, 0);
    
    if (msg_id >= 0) {
        metrics.frames_sent++;
        metrics.bytes_total += fb->len;
        ESP_LOGI(TAG, "Frame published: %u bytes (%.1f KB)", fb->len, fb->len / 1024.0);
    } else {
        metrics.frames_error++;
        ESP_LOGE(TAG, "Failed to publish frame");
    }
    
    esp_camera_fb_return(fb);
    
    // Calculate FPS
    fps_frame_count++;
    uint32_t now = xTaskGetTickCount() * portTICK_PERIOD_MS;
    if (now - last_fps_calculation >= 1000) {
        metrics.fps = fps_frame_count * 1000.0 / (now - last_fps_calculation);
        fps_frame_count = 0;
        last_fps_calculation = now;
    }
}

// ============================================================================
// WiFi FUNCTIONS
// ============================================================================

static void wifi_event_handler(void* arg, esp_event_base_t event_base, int32_t event_id, void* event_data) {
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        ESP_LOGI(TAG, "WiFi disconnected, reconnecting...");
        metrics.wifi_reconnects++;
        esp_wifi_connect();
        xEventGroupClearBits(wifi_event_group, WIFI_CONNECTED_BIT);
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t* event = (ip_event_got_ip_t*) event_data;
        ESP_LOGI(TAG, "WiFi connected! IP: " IPSTR, IP2STR(&event->ip_info.ip));
        xEventGroupSetBits(wifi_event_group, WIFI_CONNECTED_BIT);
    }
}

void init_wifi(void) {
    wifi_event_group = xEventGroupCreate();
    
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_sta();
    
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));
    
    esp_event_handler_instance_t instance_any_id;
    esp_event_handler_instance_t instance_got_ip;
    ESP_ERROR_CHECK(esp_event_handler_instance_register(WIFI_EVENT, ESP_EVENT_ANY_ID, &wifi_event_handler, NULL, &instance_any_id));
    ESP_ERROR_CHECK(esp_event_handler_instance_register(IP_EVENT, IP_EVENT_STA_GOT_IP, &wifi_event_handler, NULL, &instance_got_ip));
    
    wifi_config_t wifi_config = {
        .sta = {
            .ssid = WIFI_SSID,
            .password = WIFI_PASSWORD,
        },
    };
    
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));
    ESP_ERROR_CHECK(esp_wifi_start());
    
    ESP_LOGI(TAG, "Connecting to WiFi: %s", WIFI_SSID);
    xEventGroupWaitBits(wifi_event_group, WIFI_CONNECTED_BIT, pdFALSE, pdTRUE, portMAX_DELAY);
}

// ============================================================================
// MQTT FUNCTIONS
// ============================================================================

static void handle_control_message(const char *data, int data_len) {
    cJSON *json = cJSON_ParseWithLength(data, data_len);
    if (json == NULL) {
        ESP_LOGE(TAG, "JSON parse error");
        return;
    }
    
    bool changed = false;
    sensor_t *s = esp_camera_sensor_get();
    
    // Resolution control
    cJSON *resolution = cJSON_GetObjectItem(json, "resolution");
    if (resolution && cJSON_IsString(resolution)) {
        const char *res_str = resolution->valuestring;
        framesize_t new_res = FRAMESIZE_SVGA;
        
        if (strcmp(res_str, "QVGA") == 0) new_res = FRAMESIZE_QVGA;
        else if (strcmp(res_str, "VGA") == 0) new_res = FRAMESIZE_VGA;
        else if (strcmp(res_str, "SVGA") == 0) new_res = FRAMESIZE_SVGA;
        else if (strcmp(res_str, "XGA") == 0) new_res = FRAMESIZE_XGA;
        else if (strcmp(res_str, "HD") == 0) new_res = FRAMESIZE_HD;
        else if (strcmp(res_str, "SXGA") == 0) new_res = FRAMESIZE_SXGA;
        else if (strcmp(res_str, "UXGA") == 0) new_res = FRAMESIZE_UXGA;
        
        if (new_res != g_cam_settings.resolution) {
            g_cam_settings.resolution = new_res;
            if (s) s->set_framesize(s, new_res);
            changed = true;
            ESP_LOGI(TAG, "Resolution changed to: %s", res_str);
        }
    }
    
    // Quality control
    cJSON *quality = cJSON_GetObjectItem(json, "quality");
    if (quality && cJSON_IsNumber(quality)) {
        int new_quality = quality->valueint;
        if (new_quality >= 0 && new_quality <= 63 && new_quality != g_cam_settings.quality) {
            g_cam_settings.quality = new_quality;
            if (s) s->set_quality(s, new_quality);
            changed = true;
            ESP_LOGI(TAG, "Quality changed to: %d", new_quality);
        }
    }
    
    // Brightness control
    cJSON *brightness = cJSON_GetObjectItem(json, "brightness");
    if (brightness && cJSON_IsNumber(brightness)) {
        int new_brightness = brightness->valueint;
        if (new_brightness >= -2 && new_brightness <= 2 && new_brightness != g_cam_settings.brightness) {
            g_cam_settings.brightness = new_brightness;
            if (s) s->set_brightness(s, new_brightness);
            changed = true;
            ESP_LOGI(TAG, "Brightness changed to: %d", new_brightness);
        }
    }
    
    // Capture interval control
    cJSON *capture_interval = cJSON_GetObjectItem(json, "capture_interval_ms");
    if (capture_interval && cJSON_IsNumber(capture_interval)) {
        uint32_t new_interval = capture_interval->valueint;
        if (new_interval >= 100 && new_interval != g_cam_settings.capture_interval_ms) {
            g_cam_settings.capture_interval_ms = new_interval;
            changed = true;
            ESP_LOGI(TAG, "Capture interval changed to: %" PRIu32 " ms", new_interval);
        }
    }
    
    // Camera enable/disable
    cJSON *enabled = cJSON_GetObjectItem(json, "enabled");
    if (enabled && cJSON_IsBool(enabled)) {
        bool new_enabled = cJSON_IsTrue(enabled);
        if (new_enabled != g_cam_settings.enabled) {
            g_cam_settings.enabled = new_enabled;
            changed = true;
            ESP_LOGI(TAG, "Camera %s", new_enabled ? "enabled" : "disabled");
        }
    }
    
    // QoS control
    cJSON *qos = cJSON_GetObjectItem(json, "mqtt_qos");
    if (qos && cJSON_IsNumber(qos)) {
        int new_qos = qos->valueint;
        if (new_qos >= 0 && new_qos <= 2 && new_qos != mqtt_qos) {
            mqtt_qos = new_qos;
            changed = true;
            ESP_LOGI(TAG, "MQTT QoS changed to: %d", mqtt_qos);
        }
    }
    
    cJSON_Delete(json);
}

static void mqtt_event_handler(void *handler_args, esp_event_base_t base, int32_t event_id, void *event_data) {
    esp_mqtt_event_handle_t event = event_data;
    
    switch ((esp_mqtt_event_id_t)event_id) {
        case MQTT_EVENT_CONNECTED:
            ESP_LOGI(TAG, "MQTT Connected");
            metrics.mqtt_reconnects++;
            esp_mqtt_client_subscribe(mqtt_client, TOPIC_CONTROL, mqtt_qos);
            ESP_LOGI(TAG, "Subscribed to: %s", TOPIC_CONTROL);
            
            // Publish online status
            esp_mqtt_client_publish(mqtt_client, TOPIC_STATUS, "{\"status\":\"online\"}", 0, 0, 0);
            break;
            
        case MQTT_EVENT_DISCONNECTED:
            ESP_LOGI(TAG, "MQTT Disconnected");
            break;
            
        case MQTT_EVENT_DATA:
            if (strncmp(event->topic, TOPIC_CONTROL, event->topic_len) == 0) {
                handle_control_message(event->data, event->data_len);
            }
            break;
            
        default:
            break;
    }
}

void init_mqtt(void) {
    esp_mqtt_client_config_t mqtt_cfg = {
        .broker.address.uri = MQTT_BROKER_URI,
        .buffer.size = 65536  // Large buffer for images
    };
    
    mqtt_client = esp_mqtt_client_init(&mqtt_cfg);
    esp_mqtt_client_register_event(mqtt_client, ESP_EVENT_ANY_ID, mqtt_event_handler, NULL);
    esp_mqtt_client_start(mqtt_client);
    
    ESP_LOGI(TAG, "MQTT client started");
}

void publish_telemetry(void) {
    cJSON *json = cJSON_CreateObject();
    
    cJSON_AddStringToObject(json, "device_id", DEVICE_ID);
    cJSON_AddStringToObject(json, "device_type", "esp32-cam");
    cJSON_AddStringToObject(json, "firmware_version", "1.0.0");
    
    cJSON_AddNumberToObject(json, "quality", g_cam_settings.quality);
    cJSON_AddNumberToObject(json, "brightness", g_cam_settings.brightness);
    cJSON_AddNumberToObject(json, "capture_interval_ms", g_cam_settings.capture_interval_ms);
    cJSON_AddBoolToObject(json, "enabled", g_cam_settings.enabled);
    cJSON_AddNumberToObject(json, "mqtt_qos", mqtt_qos);
    
    cJSON_AddNumberToObject(json, "frames_captured", metrics.frames_captured);
    cJSON_AddNumberToObject(json, "frames_sent", metrics.frames_sent);
    cJSON_AddNumberToObject(json, "frames_error", metrics.frames_error);
    cJSON_AddNumberToObject(json, "bytes_total", metrics.bytes_total);
    cJSON_AddNumberToObject(json, "last_frame_size", metrics.last_frame_size);
    cJSON_AddNumberToObject(json, "fps", metrics.fps);
    
    cJSON_AddNumberToObject(json, "wifi_reconnects", metrics.wifi_reconnects);
    cJSON_AddNumberToObject(json, "mqtt_reconnects", metrics.mqtt_reconnects);
    cJSON_AddNumberToObject(json, "uptime_ms", xTaskGetTickCount() * portTICK_PERIOD_MS);
    
    char *json_str = cJSON_PrintUnformatted(json);
    esp_mqtt_client_publish(mqtt_client, TOPIC_TELEMETRY, json_str, 0, 0, 0);
    free(json_str);
    cJSON_Delete(json);
    
    ESP_LOGI(TAG, "Telemetry published");
}

// ============================================================================
// HTTP SERVER (Metrics Endpoint)
// ============================================================================

static esp_err_t metrics_handler(httpd_req_t *req) {
    char response[2048];
    int len = snprintf(response, sizeof(response),
        "# HELP camera_frames_captured_total Total frames captured\n"
        "# TYPE camera_frames_captured_total counter\n"
        "camera_frames_captured_total{device=\"%s\"} %" PRIu32 "\n"
        "\n"
        "# HELP camera_frames_sent_total Total frames sent via MQTT\n"
        "# TYPE camera_frames_sent_total counter\n"
        "camera_frames_sent_total{device=\"%s\"} %" PRIu32 "\n"
        "\n"
        "# HELP camera_fps Frames per second\n"
        "# TYPE camera_fps gauge\n"
        "camera_fps{device=\"%s\"} %.2f\n"
        "\n"
        "# HELP camera_quality JPEG quality setting\n"
        "# TYPE camera_quality gauge\n"
        "camera_quality{device=\"%s\"} %d\n"
        "\n"
        "# HELP mqtt_qos_level MQTT QoS level\n"
        "# TYPE mqtt_qos_level gauge\n"
        "mqtt_qos_level{device=\"%s\"} %d\n"
        "\n"
        "# HELP device_uptime_seconds Device uptime\n"
        "# TYPE device_uptime_seconds counter\n"
        "device_uptime_seconds{device=\"%s\"} %lu\n",
        DEVICE_ID, metrics.frames_captured,
        DEVICE_ID, metrics.frames_sent,
        DEVICE_ID, metrics.fps,
        DEVICE_ID, g_cam_settings.quality,
        DEVICE_ID, mqtt_qos,
        DEVICE_ID, (unsigned long)((xTaskGetTickCount() * portTICK_PERIOD_MS) / 1000)
    );
    
    httpd_resp_set_type(req, "text/plain; version=0.0.4");
    httpd_resp_send(req, response, len);
    return ESP_OK;
}

static esp_err_t root_handler(httpd_req_t *req) {
    const char *response = 
        "<html><head><title>ESP32-CAM</title></head><body>"
        "<h1>ESP32-CAM - esp32-cam-1</h1>"
        "<p><a href='/metrics'>Prometheus Metrics</a></p>"
        "<h2>Status</h2>"
        "<p>Camera: Enabled</p>"
        "<p><a href='http://localhost:3000'>Grafana Dashboard</a></p>"
        "</body></html>";
    
    httpd_resp_send(req, response, strlen(response));
    return ESP_OK;
}

void init_http_server(void) {
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    config.server_port = 8080;
    
    httpd_uri_t root_uri = {
        .uri = "/",
        .method = HTTP_GET,
        .handler = root_handler
    };
    
    httpd_uri_t metrics_uri = {
        .uri = "/metrics",
        .method = HTTP_GET,
        .handler = metrics_handler
    };
    
    if (httpd_start(&http_server, &config) == ESP_OK) {
        httpd_register_uri_handler(http_server, &root_uri);
        httpd_register_uri_handler(http_server, &metrics_uri);
        ESP_LOGI(TAG, "HTTP server started on port 8080");
    }
}

// ============================================================================
// MAIN TASK
// ============================================================================

void camera_task(void *pvParameters) {
    last_capture_time = xTaskGetTickCount() * portTICK_PERIOD_MS;
    last_telemetry_time = last_capture_time;
    last_fps_calculation = last_capture_time;
    
    while (1) {
        uint32_t now = xTaskGetTickCount() * portTICK_PERIOD_MS;
        
        // Capture and publish frame
        if (now - last_capture_time >= g_cam_settings.capture_interval_ms) {
            capture_and_publish_frame();
            last_capture_time = now;
        }
        
        // Publish telemetry
        if (now - last_telemetry_time >= TELEMETRY_INTERVAL_MS) {
            publish_telemetry();
            last_telemetry_time = now;
        }
        
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}

void app_main(void) {
    ESP_LOGI(TAG, "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    ESP_LOGI(TAG, "  ESP32-CAM OV2640 - Imperium IBN Node");
    ESP_LOGI(TAG, "  Device: %s", DEVICE_ID);
    ESP_LOGI(TAG, "  Firmware: v1.0.0");
    ESP_LOGI(TAG, "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    
    // Initialize NVS
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);
    
    // Initialize subsystems
    init_wifi();
    init_camera();
    init_mqtt();
    init_http_server();
    
    ESP_LOGI(TAG, "Initialization complete");
    ESP_LOGI(TAG, "Ready for operation");
    ESP_LOGI(TAG, "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
    
    // Start camera task
    xTaskCreate(camera_task, "camera_task", 8192, NULL, 5, NULL);
}
