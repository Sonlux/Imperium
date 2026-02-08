/**
 * Policy Handler Implementation
 */
#include "policy_handler.h"
#include "config.h"
#include "mqtt_handler.h"
#include "i2s_audio.h"
#include "esp_log.h"
#include "cJSON.h"
#include <string.h>

static const char *TAG = "POLICY";

PolicyHandler g_policy;

PolicyHandler::PolicyHandler()
    : current_qos_(DEFAULT_MQTT_QOS)
    , current_sample_rate_(I2S_SAMPLE_RATE)
    , enabled_(true)
    , publish_interval_ms_(DEFAULT_PUBLISH_INTERVAL_MS)
    , audio_gain_(DEFAULT_AUDIO_GAIN)
{
}

void PolicyHandler::processControlMessage(const char* data, int len) {
    if (!data || len == 0) {
        return;
    }
    
    ESP_LOGI(TAG, "Processing control message: %.*s", len, data);
    
    // Parse JSON command
    cJSON *root = cJSON_ParseWithLength(data, len);
    if (!root) {
        ESP_LOGE(TAG, "Failed to parse JSON");
        return;
    }
    
    // Extract command type
    cJSON *cmd = cJSON_GetObjectItem(root, "command");
    if (!cmd || !cJSON_IsString(cmd)) {
        ESP_LOGE(TAG, "No command field in message");
        cJSON_Delete(root);
        return;
    }
    
    const char *command = cmd->valuestring;
    ESP_LOGI(TAG, "Command: %s", command);
    
    // Process commands
    if (strcmp(command, "SET_QOS") == 0) {
        cJSON *qos = cJSON_GetObjectItem(root, "qos");
        if (qos && cJSON_IsNumber(qos)) {
            handleSetQoS(qos->valueint);
        }
    }
    else if (strcmp(command, "SET_SAMPLE_RATE") == 0) {
        cJSON *rate = cJSON_GetObjectItem(root, "sample_rate");
        if (rate && cJSON_IsNumber(rate)) {
            handleSetSampleRate(rate->valueint);
        }
    }
    else if (strcmp(command, "ENABLE") == 0) {
        handleEnable();
    }
    else if (strcmp(command, "DISABLE") == 0) {
        handleDisable();
    }
    else if (strcmp(command, "RESET") == 0) {
        handleReset();
    }
    else if (strcmp(command, "SET_PUBLISH_INTERVAL") == 0) {
        cJSON *interval = cJSON_GetObjectItem(root, "interval_ms");
        if (interval && cJSON_IsNumber(interval)) {
            handleSetPublishInterval(interval->valueint);
        }
    }
    else if (strcmp(command, "SET_AUDIO_GAIN") == 0) {
        cJSON *gain = cJSON_GetObjectItem(root, "gain");
        if (gain && cJSON_IsNumber(gain)) {
            handleSetAudioGain((float)gain->valuedouble);
        }
    }
    else if (strcmp(command, "SET_BANDWIDTH") == 0) {
        // Bandwidth limiting is handled by Raspberry Pi network layer
        ESP_LOGI(TAG, "Bandwidth policy acknowledged (enforced by gateway)");
    }
    else if (strcmp(command, "SET_PRIORITY") == 0) {
        cJSON *priority = cJSON_GetObjectItem(root, "priority");
        if (priority && cJSON_IsString(priority)) {
            ESP_LOGI(TAG, "Priority set to: %s", priority->valuestring);
            // Could adjust local buffering/QoS based on priority
        }
    }
    else {
        ESP_LOGW(TAG, "Unknown command: %s", command);
    }
    
    cJSON_Delete(root);
}

void PolicyHandler::handleSetQoS(int qos) {
    if (qos < 0 || qos > 2) {
        ESP_LOGE(TAG, "Invalid QoS: %d", qos);
        return;
    }
    
    current_qos_ = qos;
    g_mqtt.setQoS(qos);
    ESP_LOGI(TAG, "QoS set to %d", qos);
}

void PolicyHandler::handleSetSampleRate(uint32_t sample_rate) {
    // Validate sample rate (common values: 8000, 16000, 44100, 48000)
    if (sample_rate != 8000 && sample_rate != 16000 && 
        sample_rate != 44100 && sample_rate != 48000) {
        ESP_LOGE(TAG, "Invalid sample rate: %lu", sample_rate);
        return;
    }
    
    ESP_LOGI(TAG, "Processing sample rate change request: %lu Hz", sample_rate);
    
    current_sample_rate_ = sample_rate;
    
    // setSampleRate now handles full driver reconfiguration internally
    g_audio.setSampleRate(sample_rate);
    
    ESP_LOGI(TAG, "Sample rate change completed: %lu Hz", sample_rate);
    
    // Give system time to stabilize before publishing
    vTaskDelay(pdMS_TO_TICKS(200));
    
    // Publish metadata update
    char metadata[256];
    snprintf(metadata, sizeof(metadata), 
             "{\"device_id\":\"%s\",\"sample_rate\":%lu,\"channels\":1,\"bits\":16}",
             DEVICE_ID, sample_rate);
    g_mqtt.publishMetadata(metadata);
    
    ESP_LOGI(TAG, "Sample rate policy applied successfully");
}

void PolicyHandler::handleEnable() {
    if (!enabled_) {
        enabled_ = true;
        g_audio.start();
        ESP_LOGI(TAG, "Device enabled");
    }
}

void PolicyHandler::handleDisable() {
    if (enabled_) {
        enabled_ = false;
        g_audio.stop();
        ESP_LOGI(TAG, "Device disabled");
    }
}

void PolicyHandler::handleReset() {
    ESP_LOGI(TAG, "Resetting to default configuration");
    
    // Reset to defaults
    current_qos_ = DEFAULT_MQTT_QOS;
    current_sample_rate_ = I2S_SAMPLE_RATE;
    enabled_ = true;
    publish_interval_ms_ = DEFAULT_PUBLISH_INTERVAL_MS;
    audio_gain_ = DEFAULT_AUDIO_GAIN;
    
    g_mqtt.setQoS(DEFAULT_MQTT_QOS);
    g_audio.setSampleRate(I2S_SAMPLE_RATE);
    g_audio.setGain(DEFAULT_AUDIO_GAIN);
    
    if (!g_audio.isRunning()) {
        g_audio.start();
    }
}

void PolicyHandler::handleSetPublishInterval(uint32_t interval_ms) {
    // Validate interval (1 second to 60 seconds)
    if (interval_ms < 1000 || interval_ms > 60000) {
        ESP_LOGE(TAG, "Invalid publish interval: %lu ms (must be 1000-60000)", interval_ms);
        return;
    }
    
    publish_interval_ms_ = interval_ms;
    ESP_LOGI(TAG, "Publish interval set to %lu ms", interval_ms);
}

void PolicyHandler::handleSetAudioGain(float gain) {
    // Validate gain (0.1x to 10x)
    if (gain < MIN_AUDIO_GAIN || gain > MAX_AUDIO_GAIN) {
        ESP_LOGE(TAG, "Invalid audio gain: %.2f (must be %.1f-%.1f)", gain, MIN_AUDIO_GAIN, MAX_AUDIO_GAIN);
        return;
    }
    
    audio_gain_ = gain;
    g_audio.setGain(gain);
    ESP_LOGI(TAG, "Audio gain set to %.2fx", gain);
}
