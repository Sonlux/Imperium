/**
 * @file mqtt_handler.c
 * @brief MQTT communication implementation
 */

#include "mqtt_handler.h"
#include "config.h"
#include "wifi_handler.h"
#include "mqtt_client.h"
#include "esp_log.h"
#include "cJSON.h"
#include <string.h>

static const char *TAG = TAG_MQTT;
static esp_mqtt_client_handle_t mqtt_client = NULL;
static bool mqtt_connected = false;
static uint32_t publish_interval_ms = DEFAULT_PUBLISH_INTERVAL_MS;

// Forward declaration
extern void handle_mqtt_command(const mqtt_command_t *cmd);

static void mqtt_event_handler(void *handler_args, esp_event_base_t base,
                               int32_t event_id, void *event_data) {
    esp_mqtt_event_handle_t event = event_data;
    
    switch ((esp_mqtt_event_id_t)event_id) {
        case MQTT_EVENT_CONNECTED:
            ESP_LOGI(TAG, "MQTT connected");
            mqtt_connected = true;
            
            // Subscribe to control topics
            esp_mqtt_client_subscribe(mqtt_client, TOPIC_CONFIG, 1);
            esp_mqtt_client_subscribe(mqtt_client, TOPIC_CONTROL, 1);
            
            // Publish online status
            mqtt_publish_status("online");
            break;
            
        case MQTT_EVENT_DISCONNECTED:
            ESP_LOGW(TAG, "MQTT disconnected");
            mqtt_connected = false;
            break;
            
        case MQTT_EVENT_DATA:
            ESP_LOGI(TAG, "MQTT data received: topic=%.*s", 
                     event->topic_len, event->topic);
            
            // Parse JSON command
            cJSON *json = cJSON_ParseWithLength(event->data, event->data_len);
            if (json != NULL) {
                mqtt_command_t cmd = {0};
                
                cJSON *command = cJSON_GetObjectItem(json, "command");
                if (command && cJSON_IsString(command)) {
                    strncpy(cmd.command, command->valuestring, sizeof(cmd.command) - 1);
                }
                
                cJSON *interval = cJSON_GetObjectItem(json, "interval_ms");
                if (interval && cJSON_IsNumber(interval)) {
                    cmd.interval_ms = interval->valueint;
                }
                
                cJSON *range = cJSON_GetObjectItem(json, "range_ppm");
                if (range && cJSON_IsNumber(range)) {
                    cmd.range_ppm = range->valueint;
                }
                
                cJSON *enabled = cJSON_GetObjectItem(json, "enabled");
                if (enabled && cJSON_IsBool(enabled)) {
                    cmd.enabled = cJSON_IsTrue(enabled);
                }
                
                cJSON *qos = cJSON_GetObjectItem(json, "qos");
                if (qos && cJSON_IsNumber(qos)) {
                    cmd.qos_level = qos->valueint;
                }
                
                handle_mqtt_command(&cmd);
                cJSON_Delete(json);
            }
            break;
            
        case MQTT_EVENT_ERROR:
            ESP_LOGE(TAG, "MQTT error");
            break;
            
        default:
            break;
    }
}

esp_err_t mqtt_init(void) {
    ESP_LOGI(TAG, "Initializing MQTT client");
    
    // Generate client ID
    char client_id[64];
    snprintf(client_id, sizeof(client_id), "%s%s", MQTT_CLIENT_ID_PREFIX, DEVICE_ID);
    
    esp_mqtt_client_config_t mqtt_cfg = {
        .broker.address.uri = MQTT_BROKER_URL,
        .credentials.client_id = client_id,
    };
    
    mqtt_client = esp_mqtt_client_init(&mqtt_cfg);
    if (mqtt_client == NULL) {
        ESP_LOGE(TAG, "Failed to initialize MQTT client");
        return ESP_FAIL;
    }
    
    esp_mqtt_client_register_event(mqtt_client, ESP_EVENT_ANY_ID, 
                                    mqtt_event_handler, NULL);
    esp_mqtt_client_start(mqtt_client);
    
    ESP_LOGI(TAG, "MQTT client started");
    return ESP_OK;
}

esp_err_t mqtt_publish_telemetry(const mhz19_data_t *data) {
    if (!mqtt_connected || data == NULL) {
        return ESP_ERR_INVALID_STATE;
    }
    
    // Build JSON telemetry
    cJSON *json = cJSON_CreateObject();
    cJSON_AddStringToObject(json, "device_id", DEVICE_ID);
    cJSON_AddNumberToObject(json, "timestamp", data->timestamp);
    cJSON_AddNumberToObject(json, "co2_ppm", data->co2_ppm);
    cJSON_AddNumberToObject(json, "temperature", data->temperature);
    cJSON_AddStringToObject(json, "sensor_status", 
                             mhz19_is_warmed_up() ? "ready" : "warming_up");
    cJSON_AddNumberToObject(json, "rssi", wifi_get_rssi());
    
    char *json_str = cJSON_PrintUnformatted(json);
    if (json_str == NULL) {
        cJSON_Delete(json);
        return ESP_ERR_NO_MEM;
    }
    
    int msg_id = esp_mqtt_client_publish(mqtt_client, TOPIC_TELEMETRY, 
                                          json_str, 0, 1, 0);
    
    free(json_str);
    cJSON_Delete(json);
    
    if (msg_id < 0) {
        ESP_LOGE(TAG, "Failed to publish telemetry");
        return ESP_FAIL;
    }
    
    ESP_LOGD(TAG, "Telemetry published (msg_id=%d)", msg_id);
    return ESP_OK;
}

esp_err_t mqtt_publish_status(const char *status) {
    if (!mqtt_connected || status == NULL) {
        return ESP_ERR_INVALID_STATE;
    }
    
    cJSON *json = cJSON_CreateObject();
    cJSON_AddStringToObject(json, "device_id", DEVICE_ID);
    cJSON_AddStringToObject(json, "status", status);
    cJSON_AddStringToObject(json, "firmware_version", FIRMWARE_VERSION);
    cJSON_AddNumberToObject(json, "uptime_ms", xTaskGetTickCount() * portTICK_PERIOD_MS);
    
    char *json_str = cJSON_PrintUnformatted(json);
    if (json_str == NULL) {
        cJSON_Delete(json);
        return ESP_ERR_NO_MEM;
    }
    
    int msg_id = esp_mqtt_client_publish(mqtt_client, TOPIC_STATUS, 
                                          json_str, 0, 1, 1);  // Retain
    
    free(json_str);
    cJSON_Delete(json);
    
    return (msg_id >= 0) ? ESP_OK : ESP_FAIL;
}

bool mqtt_is_connected(void) {
    return mqtt_connected;
}

uint32_t mqtt_get_publish_interval(void) {
    return publish_interval_ms;
}
