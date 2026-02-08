/**
 * MQTT Handler Implementation
 */
#include "mqtt_handler.h"
#include "config.h"
#include "esp_log.h"
#include <string.h>

static const char *TAG = "MQTT";

MqttHandler g_mqtt;

MqttHandler::MqttHandler()
    : client_(nullptr)
    , connected_(false)
    , qos_(DEFAULT_MQTT_QOS)
    , control_callback_(nullptr)
    , publish_count_(0)
    , publish_error_count_(0)
    , control_msg_count_(0)
{
}

MqttHandler::~MqttHandler() {
    disconnect();
}

bool MqttHandler::init() {
    ESP_LOGI(TAG, "Initializing MQTT client (Broker: %s)", MQTT_BROKER_URI);
    
    esp_mqtt_client_config_t mqtt_cfg = {};
    mqtt_cfg.broker.address.uri = MQTT_BROKER_URI;
    
    if (strlen(MQTT_USERNAME) > 0) {
        mqtt_cfg.credentials.username = MQTT_USERNAME;
        mqtt_cfg.credentials.authentication.password = MQTT_PASSWORD;
    }
    
    mqtt_cfg.session.keepalive = MQTT_KEEPALIVE_SEC;
    mqtt_cfg.network.reconnect_timeout_ms = MQTT_RECONNECT_DELAY_MS;
    mqtt_cfg.buffer.size = 4096;  // Large buffer for audio chunks
    
    client_ = esp_mqtt_client_init(&mqtt_cfg);
    if (!client_) {
        ESP_LOGE(TAG, "Failed to initialize MQTT client");
        return false;
    }
    
    esp_mqtt_client_register_event(client_, MQTT_EVENT_ANY, eventHandler, this);
    
    ESP_LOGI(TAG, "MQTT client initialized");
    return true;
}

bool MqttHandler::connect() {
    if (!client_) {
        ESP_LOGE(TAG, "Client not initialized");
        return false;
    }
    
    ESP_LOGI(TAG, "Connecting to MQTT broker...");
    esp_err_t err = esp_mqtt_client_start(client_);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to start MQTT client: %s", esp_err_to_name(err));
        return false;
    }
    
    return true;
}

void MqttHandler::disconnect() {
    if (client_) {
        esp_mqtt_client_stop(client_);
        esp_mqtt_client_destroy(client_);
        client_ = nullptr;
    }
    connected_ = false;
}

bool MqttHandler::isConnected() {
    return connected_;
}

void MqttHandler::eventHandler(void *handler_args, esp_event_base_t base, 
                               int32_t event_id, void *event_data) {
    MqttHandler *handler = static_cast<MqttHandler*>(handler_args);
    handler->handleEvent(static_cast<esp_mqtt_event_handle_t>(event_data));
}

void MqttHandler::handleEvent(esp_mqtt_event_handle_t event) {
    switch (event->event_id) {
        case MQTT_EVENT_CONNECTED:
            ESP_LOGI(TAG, "MQTT connected");
            connected_ = true;
            
            // Subscribe to control topic
            esp_mqtt_client_subscribe(client_, TOPIC_CONTROL, qos_);
            
            // Publish online status
            publishStatus("online");
            break;
            
        case MQTT_EVENT_DISCONNECTED:
            ESP_LOGW(TAG, "MQTT disconnected");
            connected_ = false;
            break;
            
        case MQTT_EVENT_SUBSCRIBED:
            ESP_LOGI(TAG, "Subscribed to topic, msg_id=%d", event->msg_id);
            break;
            
        case MQTT_EVENT_DATA:
            ESP_LOGD(TAG, "MQTT data received: topic=%.*s, len=%d", 
                     event->topic_len, event->topic, event->data_len);
            
            if (strncmp(event->topic, TOPIC_CONTROL, event->topic_len) == 0) {
                control_msg_count_++;
                if (control_callback_) {
                    control_callback_(event->topic, event->data, event->data_len);
                }
            }
            break;
            
        case MQTT_EVENT_ERROR:
            ESP_LOGE(TAG, "MQTT error occurred");
            publish_error_count_++;
            break;
            
        default:
            break;
    }
}

bool MqttHandler::publishAudio(const uint8_t* data, size_t len, int qos) {
    if (!connected_ || !client_) {
        return false;
    }
    
    int msg_id = esp_mqtt_client_publish(client_, TOPIC_AUDIO_DATA, 
                                         (const char*)data, len, qos, 0);
    if (msg_id < 0) {
        publish_error_count_++;
        return false;
    }
    
    publish_count_++;
    return true;
}

bool MqttHandler::publishTelemetry(const char* json_data) {
    if (!connected_ || !client_) {
        return false;
    }
    
    int msg_id = esp_mqtt_client_publish(client_, TOPIC_TELEMETRY, 
                                         json_data, 0, qos_, 0);
    if (msg_id < 0) {
        publish_error_count_++;
        return false;
    }
    
    return true;
}

bool MqttHandler::publishStatus(const char* status) {
    if (!client_) {
        return false;
    }
    
    int msg_id = esp_mqtt_client_publish(client_, TOPIC_STATUS, 
                                         status, 0, 1, 0);  // QoS 1 for status
    return msg_id >= 0;
}

bool MqttHandler::publishMetadata(const char* json_data) {
    if (!connected_ || !client_) {
        return false;
    }
    
    int msg_id = esp_mqtt_client_publish(client_, TOPIC_METADATA, 
                                         json_data, 0, 1, 1);  // QoS 1, retain
    return msg_id >= 0;
}

bool MqttHandler::subscribeControl(MqttCallback callback) {
    control_callback_ = callback;
    if (connected_) {
        esp_mqtt_client_subscribe(client_, TOPIC_CONTROL, qos_);
    }
    return true;
}

void MqttHandler::setQoS(int qos) {
    if (qos >= 0 && qos <= 2) {
        qos_ = qos;
        ESP_LOGI(TAG, "QoS set to %d", qos);
    }
}

int MqttHandler::getQoS() {
    return qos_;
}

uint32_t MqttHandler::getPublishCount() {
    return publish_count_;
}

uint32_t MqttHandler::getPublishErrorCount() {
    return publish_error_count_;
}

uint32_t MqttHandler::getControlMessageCount() {
    return control_msg_count_;
}
