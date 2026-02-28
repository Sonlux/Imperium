/**
 * @file config.h
 * @brief Configuration for ESP32 MH-Z19 CO2 Sensor Node
 */

#ifndef CONFIG_H
#define CONFIG_H

// ============================================================================
// WiFi Configuration
// ============================================================================
#define WIFI_SSID               "Galaxy A56 5G A76A"
#define WIFI_PASSWORD           "12345678"
#define WIFI_MAX_RETRY          5
#define WIFI_CONNECTED_BIT      BIT0
#define WIFI_FAIL_BIT           BIT1

// ============================================================================
// MQTT Configuration
// ============================================================================
#define MQTT_BROKER_URL         "mqtt://10.218.189.192"
#define MQTT_BROKER_PORT        1883
#define MQTT_USERNAME           ""
#define MQTT_PASSWORD           ""
#define MQTT_CLIENT_ID_PREFIX   "esp32-mhz19-"

// ============================================================================
// Device Configuration
// ============================================================================
#define DEVICE_ID               "esp32-mhz19-1"
#define DEVICE_TYPE             "co2_sensor"
#define FIRMWARE_VERSION        "1.0.0"

// ============================================================================
// MQTT Topics
// ============================================================================
#define TOPIC_TELEMETRY         "imperium/devices/" DEVICE_ID "/telemetry"
#define TOPIC_STATUS            "imperium/devices/" DEVICE_ID "/status"
#define TOPIC_CONFIG            "imperium/devices/" DEVICE_ID "/config"
#define TOPIC_CONTROL           "imperium/devices/" DEVICE_ID "/control"

// ============================================================================
// MH-Z19 Sensor Configuration
// ============================================================================
#define MHZ19_UART_NUM          UART_NUM_2
#define MHZ19_TX_PIN            GPIO_NUM_17
#define MHZ19_RX_PIN            GPIO_NUM_16
#define MHZ19_BAUD_RATE         9600
#define MHZ19_BUF_SIZE          256

// Timing
#define MHZ19_WARMUP_TIME_MS    180000  // 3 minutes
#define MHZ19_RESPONSE_TIMEOUT  1000    // 1 second
#define MHZ19_READ_INTERVAL_MS  2000    // Minimum 2 seconds between reads

// Detection ranges (ppm)
#define MHZ19_RANGE_2000        2000
#define MHZ19_RANGE_5000        5000
#define MHZ19_RANGE_10000       10000

// Default settings
#define MHZ19_DEFAULT_RANGE     MHZ19_RANGE_5000
#define MHZ19_ABC_ENABLED       true

// ============================================================================
// Telemetry Configuration
// ============================================================================
#define DEFAULT_PUBLISH_INTERVAL_MS     5000    // 5 seconds
#define MIN_PUBLISH_INTERVAL_MS         1000    // 1 second
#define MAX_PUBLISH_INTERVAL_MS         300000  // 5 minutes

// ============================================================================
// GPIO Configuration
// ============================================================================
#define LED_GPIO                GPIO_NUM_2      // Built-in LED
#define LED_BLINK_NORMAL        500             // Normal operation blink rate (ms)
#define LED_BLINK_ERROR         100             // Error blink rate (ms)

// ============================================================================
// System Configuration
// ============================================================================
#define TELEMETRY_QUEUE_SIZE    10
#define COMMAND_QUEUE_SIZE      5
#define MAX_JSON_SIZE           512

// HTTP Metrics Server (Prometheus)
#define METRICS_HTTP_PORT       8080
#define METRICS_HTTP_STACK      8192

// Task priorities
#define SENSOR_TASK_PRIORITY    5
#define MQTT_TASK_PRIORITY      4
#define LED_TASK_PRIORITY       2

// Task stack sizes
#define SENSOR_TASK_STACK       4096
#define MQTT_TASK_STACK         6144
#define LED_TASK_STACK          2048

// ============================================================================
// Logging Tags
// ============================================================================
#define TAG_MAIN                "MAIN"
#define TAG_WIFI                "WIFI"
#define TAG_MQTT                "MQTT"
#define TAG_MHZ19               "MHZ19"
#define TAG_SENSOR              "SENSOR"

#endif // CONFIG_H
