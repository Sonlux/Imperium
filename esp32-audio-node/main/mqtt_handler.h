/**
 * MQTT Handler Module
 * Manages MQTT connection and message publishing/subscription
 */
#ifndef MQTT_HANDLER_H
#define MQTT_HANDLER_H

#include <string>
#include <functional>
#include "mqtt_client.h"

// Callback for control messages
typedef std::function<void(const char* topic, const char* data, int len)> MqttCallback;

class MqttHandler {
public:
    MqttHandler();
    ~MqttHandler();
    
    // Initialize MQTT client
    bool init();
    
    // Connection management
    bool connect();
    void disconnect();
    bool isConnected();
    
    // Publishing
    bool publishAudio(const uint8_t* data, size_t len, int qos);
    bool publishTelemetry(const char* json_data);
    bool publishStatus(const char* status);
    bool publishMetadata(const char* json_data);
    
    // Subscribe to control topic
    bool subscribeControl(MqttCallback callback);
    
    // QoS management
    void setQoS(int qos);
    int getQoS();
    
    // Statistics
    uint32_t getPublishCount();
    uint32_t getPublishErrorCount();
    uint32_t getControlMessageCount();
    
private:
    static void eventHandler(void *handler_args, esp_event_base_t base, 
                            int32_t event_id, void *event_data);
    void handleEvent(esp_mqtt_event_handle_t event);
    
    esp_mqtt_client_handle_t client_;
    bool connected_;
    int qos_;
    
    MqttCallback control_callback_;
    
    // Statistics
    uint32_t publish_count_;
    uint32_t publish_error_count_;
    uint32_t control_msg_count_;
};

// Global instance
extern MqttHandler g_mqtt;

#endif // MQTT_HANDLER_H
