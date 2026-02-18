/**
 * @file mqtt_handler.h
 * @brief MQTT communication handling
 */

#ifndef MQTT_HANDLER_H
#define MQTT_HANDLER_H

#include "esp_err.h"
#include "mhz19.h"
#include <stdbool.h>

/**
 * @brief MQTT command structure
 */
typedef struct {
    char command[32];
    int interval_ms;
    int range_ppm;
    int qos_level;
    bool enabled;
} mqtt_command_t;

/**
 * @brief Initialize MQTT client
 * @return ESP_OK on success
 */
esp_err_t mqtt_init(void);

/**
 * @brief Publish sensor telemetry
 * @param data Sensor data to publish
 * @return ESP_OK on success
 */
esp_err_t mqtt_publish_telemetry(const mhz19_data_t *data);

/**
 * @brief Publish device status
 * @param status Status message
 * @return ESP_OK on success
 */
esp_err_t mqtt_publish_status(const char *status);

/**
 * @brief Check if MQTT is connected
 * @return true if connected
 */
bool mqtt_is_connected(void);

/**
 * @brief Get current publish interval
 * @return Interval in milliseconds
 */
uint32_t mqtt_get_publish_interval(void);

#endif // MQTT_HANDLER_H
