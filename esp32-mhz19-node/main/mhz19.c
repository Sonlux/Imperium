/**
 * @file mhz19.c
 * @brief MH-Z19 CO2 Sensor Driver Implementation
 */

#include "mhz19.h"
#include "config.h"
#include "driver/uart.h"
#include "driver/gpio.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <string.h>

static const char *TAG = TAG_MHZ19;
static mhz19_config_t sensor_config = {0};
static bool initialized = false;

// ============================================================================
// Internal Helper Functions
// ============================================================================

/**
 * @brief Send command to MH-Z19 sensor
 */
static esp_err_t mhz19_send_command(uint8_t cmd, uint8_t byte3, uint8_t byte4, 
                                     uint8_t byte5, uint8_t byte6, uint8_t byte7) {
    uint8_t command[9] = {
        0xFF, 0x01,    // Start bytes
        cmd,           // Command
        byte3, byte4, byte5, byte6, byte7,
        0x00           // Checksum (calculated below)
    };
    
    // Calculate checksum
    command[8] = mhz19_calculate_checksum(command);
    
    int written = uart_write_bytes(MHZ19_UART_NUM, (const char*)command, sizeof(command));
    if (written != sizeof(command)) {
        ESP_LOGE(TAG, "Failed to write command 0x%02X", cmd);
        return ESP_FAIL;
    }
    
    return ESP_OK;
}

/**
 * @brief Read response from MH-Z19 sensor
 */
static esp_err_t mhz19_read_response(uint8_t *response, size_t len, uint32_t timeout_ms) {
    int received = uart_read_bytes(MHZ19_UART_NUM, response, len, 
                                    pdMS_TO_TICKS(timeout_ms));
    
    if (received != len) {
        ESP_LOGE(TAG, "Read timeout or incomplete response (%d/%d bytes)", received, len);
        return ESP_ERR_TIMEOUT;
    }
    
    // Verify start bytes
    if (response[0] != 0xFF || response[1] != 0x86) {
        ESP_LOGE(TAG, "Invalid response header: 0x%02X 0x%02X", response[0], response[1]);
        return ESP_ERR_INVALID_RESPONSE;
    }
    
    // Verify checksum
    if (!mhz19_verify_checksum(response)) {
        ESP_LOGE(TAG, "Checksum verification failed");
        return ESP_ERR_INVALID_CRC;
    }
    
    return ESP_OK;
}

// ============================================================================
// Public API Implementation
// ============================================================================

esp_err_t mhz19_init(void) {
    if (initialized) {
        ESP_LOGW(TAG, "Already initialized");
        return ESP_OK;
    }
    
    ESP_LOGI(TAG, "Initializing MH-Z19 sensor");
    
    // Configure UART
    uart_config_t uart_config = {
        .baud_rate = MHZ19_BAUD_RATE,
        .data_bits = UART_DATA_8_BITS,
        .parity = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        .source_clk = UART_SCLK_APB,
    };
    
    ESP_ERROR_CHECK(uart_driver_install(MHZ19_UART_NUM, MHZ19_BUF_SIZE * 2, 0, 0, NULL, 0));
    ESP_ERROR_CHECK(uart_param_config(MHZ19_UART_NUM, &uart_config));
    ESP_ERROR_CHECK(uart_set_pin(MHZ19_UART_NUM, MHZ19_TX_PIN, MHZ19_RX_PIN, 
                                   UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE));
    
    // Initialize configuration
    sensor_config.detection_range = MHZ19_DEFAULT_RANGE;
    sensor_config.abc_enabled = MHZ19_ABC_ENABLED;
    sensor_config.is_warmed_up = false;
    sensor_config.warmup_start = xTaskGetTickCount() * portTICK_PERIOD_MS;
    
    // Set default detection range
    esp_err_t ret = mhz19_set_detection_range(MHZ19_DEFAULT_RANGE);
    if (ret != ESP_OK) {
        ESP_LOGW(TAG, "Failed to set detection range, continuing anyway");
    }
    
    // Enable ABC by default
    ret = mhz19_set_abc(MHZ19_ABC_ENABLED);
    if (ret != ESP_OK) {
        ESP_LOGW(TAG, "Failed to set ABC mode, continuing anyway");
    }
    
    initialized = true;
    ESP_LOGI(TAG, "MH-Z19 initialized successfully (warm-up: 3 minutes)");
    
    return ESP_OK;
}

esp_err_t mhz19_read_data(mhz19_data_t *data) {
    if (!initialized) {
        ESP_LOGE(TAG, "Sensor not initialized");
        return ESP_ERR_INVALID_STATE;
    }
    
    if (data == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    
    // Clear any pending data in UART buffer
    uart_flush_input(MHZ19_UART_NUM);
    
    // Send read command
    esp_err_t ret = mhz19_send_command(MHZ19_CMD_READ_CO2, 0x00, 0x00, 0x00, 0x00, 0x00);
    if (ret != ESP_OK) {
        return ret;
    }
    
    // Read response (9 bytes)
    uint8_t response[9];
    ret = mhz19_read_response(response, sizeof(response), MHZ19_RESPONSE_TIMEOUT);
    if (ret != ESP_OK) {
        data->valid = false;
        return ret;
    }
    
    // Parse response
    data->co2_ppm = (response[2] << 8) | response[3];
    data->temperature = (int8_t)response[4] - 40;  // Temperature offset
    data->status = response[5];
    data->valid = true;
    data->timestamp = xTaskGetTickCount() * portTICK_PERIOD_MS;
    
    // Check if sensor is warmed up
    if (!sensor_config.is_warmed_up) {
        uint32_t elapsed = data->timestamp - sensor_config.warmup_start;
        if (elapsed >= MHZ19_WARMUP_TIME_MS) {
            sensor_config.is_warmed_up = true;
            ESP_LOGI(TAG, "Sensor warm-up complete");
        }
    }
    
    ESP_LOGD(TAG, "CO2: %u ppm, Temp: %d°C, Status: 0x%02X", 
             data->co2_ppm, data->temperature, data->status);
    
    return ESP_OK;
}

esp_err_t mhz19_calibrate_zero(void) {
    if (!initialized) {
        return ESP_ERR_INVALID_STATE;
    }
    
    ESP_LOGI(TAG, "Calibrating zero point (400 ppm)");
    
    esp_err_t ret = mhz19_send_command(MHZ19_CMD_CALIBRATE_ZERO, 0x00, 0x00, 0x00, 0x00, 0x00);
    if (ret == ESP_OK) {
        ESP_LOGI(TAG, "Zero calibration command sent");
        vTaskDelay(pdMS_TO_TICKS(2000));  // Wait for calibration
    }
    
    return ret;
}

esp_err_t mhz19_calibrate_span(uint16_t span_ppm) {
    if (!initialized) {
        return ESP_ERR_INVALID_STATE;
    }
    
    ESP_LOGI(TAG, "Calibrating span point (%u ppm)", span_ppm);
    
    uint8_t high = (span_ppm >> 8) & 0xFF;
    uint8_t low = span_ppm & 0xFF;
    
    esp_err_t ret = mhz19_send_command(MHZ19_CMD_CALIBRATE_SPAN, high, low, 0x00, 0x00, 0x00);
    if (ret == ESP_OK) {
        ESP_LOGI(TAG, "Span calibration command sent");
        vTaskDelay(pdMS_TO_TICKS(2000));
    }
    
    return ret;
}

esp_err_t mhz19_set_detection_range(uint16_t range_ppm) {
    if (!initialized) {
        return ESP_ERR_INVALID_STATE;
    }
    
    // Validate range
    if (range_ppm != MHZ19_RANGE_2000 && 
        range_ppm != MHZ19_RANGE_5000 && 
        range_ppm != MHZ19_RANGE_10000) {
        ESP_LOGE(TAG, "Invalid detection range: %u (must be 2000, 5000, or 10000)", range_ppm);
        return ESP_ERR_INVALID_ARG;
    }
    
    ESP_LOGI(TAG, "Setting detection range to %u ppm", range_ppm);
    
    uint8_t high = (range_ppm >> 8) & 0xFF;
    uint8_t low = range_ppm & 0xFF;
    
    esp_err_t ret = mhz19_send_command(MHZ19_CMD_DETECTION_RANGE, high, low, 0x00, 0x00, 0x00);
    if (ret == ESP_OK) {
        sensor_config.detection_range = range_ppm;
        ESP_LOGI(TAG, "Detection range set successfully");
    }
    
    return ret;
}

esp_err_t mhz19_set_abc(bool enabled) {
    if (!initialized) {
        return ESP_ERR_INVALID_STATE;
    }
    
    ESP_LOGI(TAG, "%s Automatic Baseline Correction (ABC)", enabled ? "Enabling" : "Disabling");
    
    uint8_t abc_value = enabled ? 0xA0 : 0x00;
    
    esp_err_t ret = mhz19_send_command(MHZ19_CMD_ABC_LOGIC, abc_value, 0x00, 0x00, 0x00, 0x00);
    if (ret == ESP_OK) {
        sensor_config.abc_enabled = enabled;
        ESP_LOGI(TAG, "ABC %s successfully", enabled ? "enabled" : "disabled");
    }
    
    return ret;
}

bool mhz19_is_warmed_up(void) {
    if (!initialized) {
        return false;
    }
    
    if (sensor_config.is_warmed_up) {
        return true;
    }
    
    uint32_t now = xTaskGetTickCount() * portTICK_PERIOD_MS;
    uint32_t elapsed = now - sensor_config.warmup_start;
    
    if (elapsed >= MHZ19_WARMUP_TIME_MS) {
        sensor_config.is_warmed_up = true;
        return true;
    }
    
    return false;
}

esp_err_t mhz19_get_config(mhz19_config_t *config) {
    if (!initialized || config == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    
    memcpy(config, &sensor_config, sizeof(mhz19_config_t));
    return ESP_OK;
}

uint8_t mhz19_calculate_checksum(const uint8_t *data) {
    uint8_t sum = 0;
    for (int i = 1; i < 8; i++) {
        sum += data[i];
    }
    return 0xFF - sum + 1;
}

bool mhz19_verify_checksum(const uint8_t *data) {
    uint8_t calculated = mhz19_calculate_checksum(data);
    return calculated == data[8];
}
