/**
 * @file wifi_handler.h
 * @brief WiFi connection management
 */

#ifndef WIFI_HANDLER_H
#define WIFI_HANDLER_H

#include "esp_err.h"
#include <stdbool.h>

/**
 * @brief Initialize WiFi and connect to AP
 * @return ESP_OK on success
 */
esp_err_t wifi_init_sta(void);

/**
 * @brief Check if WiFi is connected
 * @return true if connected
 */
bool wifi_is_connected(void);

/**
 * @brief Get WiFi RSSI
 * @return RSSI value in dBm
 */
int8_t wifi_get_rssi(void);

#endif // WIFI_HANDLER_H
