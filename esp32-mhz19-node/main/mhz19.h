/**
 * @file mhz19.h
 * @brief MH-Z19 CO2 Sensor Driver for ESP32
 */

#ifndef MHZ19_H
#define MHZ19_H

#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"

// ============================================================================
// MH-Z19 Commands
// ============================================================================
#define MHZ19_CMD_READ_CO2          0x86
#define MHZ19_CMD_CALIBRATE_ZERO    0x87
#define MHZ19_CMD_CALIBRATE_SPAN    0x88
#define MHZ19_CMD_ABC_LOGIC         0x79
#define MHZ19_CMD_DETECTION_RANGE   0x99

// ============================================================================
// Data Structures
// ============================================================================

/**
 * @brief MH-Z19 sensor data
 */
typedef struct {
    uint16_t co2_ppm;           // CO2 concentration (ppm)
    int8_t temperature;         // Temperature (°C)
    uint8_t status;             // Sensor status byte
    bool valid;                 // Data validity flag
    uint32_t timestamp;         // Last read timestamp (ms)
} mhz19_data_t;

/**
 * @brief MH-Z19 configuration
 */
typedef struct {
    uint16_t detection_range;   // Detection range (2000, 5000, 10000)
    bool abc_enabled;           // Automatic Baseline Correction
    bool is_warmed_up;          // Warm-up status
    uint32_t warmup_start;      // Warm-up start time (ms)
} mhz19_config_t;

// ============================================================================
// Function Declarations
// ============================================================================

/**
 * @brief Initialize MH-Z19 sensor
 * @return ESP_OK on success
 */
esp_err_t mhz19_init(void);

/**
 * @brief Read CO2 concentration and temperature
 * @param data Pointer to store sensor data
 * @return ESP_OK on success
 */
esp_err_t mhz19_read_data(mhz19_data_t *data);

/**
 * @brief Calibrate zero point (400 ppm)
 * @note Sensor must be in fresh air for 20+ minutes
 * @return ESP_OK on success
 */
esp_err_t mhz19_calibrate_zero(void);

/**
 * @brief Calibrate span point
 * @param span_ppm Span point concentration (e.g., 2000)
 * @return ESP_OK on success
 */
esp_err_t mhz19_calibrate_span(uint16_t span_ppm);

/**
 * @brief Set detection range
 * @param range_ppm Range in ppm (2000, 5000, or 10000)
 * @return ESP_OK on success
 */
esp_err_t mhz19_set_detection_range(uint16_t range_ppm);

/**
 * @brief Enable or disable Automatic Baseline Correction (ABC)
 * @param enabled true to enable, false to disable
 * @return ESP_OK on success
 */
esp_err_t mhz19_set_abc(bool enabled);

/**
 * @brief Check if sensor is warmed up
 * @return true if warmed up (3+ minutes since init)
 */
bool mhz19_is_warmed_up(void);

/**
 * @brief Get current configuration
 * @param config Pointer to store configuration
 * @return ESP_OK on success
 */
esp_err_t mhz19_get_config(mhz19_config_t *config);

/**
 * @brief Calculate checksum for MH-Z19 command
 * @param data Command data (8 bytes)
 * @return Checksum byte
 */
uint8_t mhz19_calculate_checksum(const uint8_t *data);

/**
 * @brief Verify response checksum
 * @param data Response data (9 bytes)
 * @return true if checksum valid
 */
bool mhz19_verify_checksum(const uint8_t *data);

#endif // MHZ19_H
