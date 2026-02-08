/**
 * ESP32 Audio Node - Configuration Header
 * Imperium IBN Framework Integration
 */
#ifndef CONFIG_H
#define CONFIG_H

#include <string>

// ============== Network Configuration ==============
#define WIFI_SSID                "Galaxy A56 5G A76A"
#define WIFI_PASSWORD            "12345678"
#define MQTT_BROKER_URI          "mqtt://10.218.189.192:1883"  // Raspberry Pi IP
#define MQTT_USERNAME            ""  // Leave empty if no auth
#define MQTT_PASSWORD            ""

// ============== Device Identity ==============
#define DEVICE_ID                "esp32-audio-1"
#define DEVICE_TYPE              "audio_sensor"
#define FIRMWARE_VERSION         "1.0.0"

// ============== MQTT Topics ==============
#define TOPIC_AUDIO_DATA         "iot/" DEVICE_ID "/audio"
#define TOPIC_TELEMETRY          "iot/" DEVICE_ID "/telemetry"
#define TOPIC_CONTROL            "iot/" DEVICE_ID "/control"
#define TOPIC_STATUS             "iot/" DEVICE_ID "/status"
#define TOPIC_METADATA           "iot/" DEVICE_ID "/metadata"

// ============== I2S Configuration ==============
#define I2S_NUM                  I2S_NUM_0
#define I2S_SAMPLE_RATE          16000      // 16 kHz
#define I2S_BITS_PER_SAMPLE      16
#define I2S_CHANNELS             1          // Mono

// Pin Configuration (adjust for your board)
#define I2S_SCK_PIN              25         // Serial Clock
#define I2S_WS_PIN               33         // Word Select (LRCK)
#define I2S_SD_PIN               32         // Serial Data

// ============== Audio Processing ==============
#define AUDIO_FRAME_MS           30         // 30ms frames
#define AUDIO_FRAME_SAMPLES      (I2S_SAMPLE_RATE * AUDIO_FRAME_MS / 1000)  // 480 samples
#define AUDIO_BUFFER_SIZE        (AUDIO_FRAME_SAMPLES * 2)  // 16-bit samples
#define AUDIO_BUFFER_COUNT       4          // Ping-pong + overflow buffers

// ============== MQTT Settings ==============
#define DEFAULT_MQTT_QOS         1          // QoS 1 (at least once)
#define MQTT_KEEPALIVE_SEC       60
#define MQTT_RECONNECT_DELAY_MS  5000
#define DEFAULT_PUBLISH_INTERVAL_MS  10000  // Default telemetry rate: 10 seconds

// ============== Audio Processing Settings ==============
#define DEFAULT_AUDIO_GAIN       1.0f       // Default audio amplification (1.0 = no gain)
#define MIN_AUDIO_GAIN           0.1f       // Minimum 10% gain
#define MAX_AUDIO_GAIN           10.0f      // Maximum 10x amplification

// ============== Metrics Server ==============
#define METRICS_HTTP_PORT        8080
#define METRICS_ENABLED          true

// ============== Performance Tuning ==============
#define TASK_PRIORITY_AUDIO      5
#define TASK_PRIORITY_MQTT       4
#define TASK_PRIORITY_METRICS    2
#define WATCHDOG_TIMEOUT_SEC     30

// ============== Debug Settings ==============
#define DEBUG_SERIAL             true
#define LOG_LEVEL                ESP_LOG_INFO  // ESP_LOG_DEBUG for verbose

#endif // CONFIG_H
