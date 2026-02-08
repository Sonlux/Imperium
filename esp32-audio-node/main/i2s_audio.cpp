/**
 * I2S Audio Capture Implementation
 */
#include "i2s_audio.h"
#include "config.h"
#include <string.h>
#include <math.h>
#include "driver/i2s.h"
#include "esp_log.h"
#include "freertos/task.h"

static const char *TAG = "I2S_AUDIO";

I2SAudio g_audio;

I2SAudio::I2SAudio() 
    : initialized_(false)
    , running_(false)
    , sample_rate_(I2S_SAMPLE_RATE)
    , sequence_counter_(0)
    , audio_task_handle_(nullptr)
    , config_mutex_(nullptr)
    , audio_gain_(DEFAULT_AUDIO_GAIN)
    , frame_queue_(nullptr)
{
    memset(&stats_, 0, sizeof(stats_));
    for (int i = 0; i < AUDIO_BUFFER_COUNT; i++) {
        frame_pool_[i] = nullptr;
    }
    
    // Create mutex for thread-safe reconfiguration
    config_mutex_ = xSemaphoreCreateMutex();
}

I2SAudio::~I2SAudio() {
    stop();
    if (frame_queue_) {
        vQueueDelete(frame_queue_);
    }
    if (config_mutex_) {
        vSemaphoreDelete(config_mutex_);
    }
    for (int i = 0; i < AUDIO_BUFFER_COUNT; i++) {
        if (frame_pool_[i] && frame_pool_[i]->samples) {
            free(frame_pool_[i]->samples);
        }
        if (frame_pool_[i]) {
            free(frame_pool_[i]);
        }
    }
}

bool I2SAudio::init() {
    if (initialized_) {
        ESP_LOGW(TAG, "Already initialized");
        return true;
    }
    
    ESP_LOGI(TAG, "Initializing I2S (SCK=%d, WS=%d, SD=%d, Rate=%lu Hz)", 
             I2S_SCK_PIN, I2S_WS_PIN, I2S_SD_PIN, sample_rate_);
    
    // Configure I2S peripheral
    i2s_config_t i2s_config = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
        .sample_rate = sample_rate_,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
        .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,  // Mono
        .communication_format = I2S_COMM_FORMAT_STAND_I2S,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = 4,
        .dma_buf_len = AUDIO_FRAME_SAMPLES,
        .use_apll = false,
        .tx_desc_auto_clear = false,
        .fixed_mclk = 0
    };
    
    i2s_pin_config_t pin_config = {
        .bck_io_num = I2S_SCK_PIN,
        .ws_io_num = I2S_WS_PIN,
        .data_out_num = I2S_PIN_NO_CHANGE,
        .data_in_num = I2S_SD_PIN
    };
    
    esp_err_t err = i2s_driver_install(I2S_NUM, &i2s_config, 0, NULL);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to install I2S driver: %s", esp_err_to_name(err));
        return false;
    }
    
    err = i2s_set_pin(I2S_NUM, &pin_config);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to set I2S pins: %s", esp_err_to_name(err));
        i2s_driver_uninstall(I2S_NUM);
        return false;
    }
    
    // Allocate frame buffers
    for (int i = 0; i < AUDIO_BUFFER_COUNT; i++) {
        frame_pool_[i] = (AudioFrame*)malloc(sizeof(AudioFrame));
        if (!frame_pool_[i]) {
            ESP_LOGE(TAG, "Failed to allocate frame struct %d", i);
            return false;
        }
        frame_pool_[i]->samples = (int16_t*)malloc(AUDIO_BUFFER_SIZE);
        if (!frame_pool_[i]->samples) {
            ESP_LOGE(TAG, "Failed to allocate frame buffer %d", i);
            return false;
        }
        frame_pool_[i]->sample_count = AUDIO_FRAME_SAMPLES;
    }
    
    // Create frame queue
    frame_queue_ = xQueueCreate(AUDIO_BUFFER_COUNT, sizeof(AudioFrame*));
    if (!frame_queue_) {
        ESP_LOGE(TAG, "Failed to create frame queue");
        return false;
    }
    
    initialized_ = true;
    ESP_LOGI(TAG, "I2S initialized successfully");
    return true;
}

bool I2SAudio::start() {
    if (!initialized_) {
        ESP_LOGE(TAG, "Not initialized");
        return false;
    }
    
    if (running_) {
        ESP_LOGW(TAG, "Already running");
        return true;
    }
    
    // Start I2S
    i2s_zero_dma_buffer(I2S_NUM);
    i2s_start(I2S_NUM);
    
    // Set running flag BEFORE creating task to avoid race condition
    running_ = true;
    
    // Create audio capture task
    BaseType_t ret = xTaskCreate(
        audioTaskWrapper,
        "audio_task",
        4096,
        this,
        TASK_PRIORITY_AUDIO,
        &audio_task_handle_
    );
    
    if (ret != pdPASS) {
        ESP_LOGE(TAG, "Failed to create audio task");
        running_ = false;
        return false;
    }
    
    ESP_LOGI(TAG, "Audio capture started");
    return true;
}

bool I2SAudio::stop() {
    if (!running_) {
        return true;
    }
    
    ESP_LOGI(TAG, "Stopping audio capture...");
    
    // Stop I2S first to unblock any pending reads
    i2s_stop(I2S_NUM);
    
    // Then signal task to exit
    running_ = false;
    
    // Wait for task to exit (max 1 second)
    if (audio_task_handle_) {
        for (int i = 0; i < 100; i++) {
            if (eTaskGetState(audio_task_handle_) == eDeleted) {
                break;
            }
            vTaskDelay(pdMS_TO_TICKS(10));
        }
        audio_task_handle_ = nullptr;
    }
    
    ESP_LOGI(TAG, "Audio capture stopped");
    return true;
}

bool I2SAudio::isRunning() {
    return running_;
}

void I2SAudio::audioTaskWrapper(void *param) {
    ((I2SAudio*)param)->audioTask();
}

void I2SAudio::audioTask() {
    ESP_LOGI(TAG, "Audio capture task started");
    
    int current_buffer_idx = 0;
    size_t bytes_read = 0;
    
    while (running_) {
        AudioFrame *frame = frame_pool_[current_buffer_idx];
        
        // Read from I2S
        esp_err_t err = i2s_read(
            I2S_NUM,
            frame->samples,
            AUDIO_BUFFER_SIZE,
            &bytes_read,
            portMAX_DELAY
        );
        
        if (err != ESP_OK) {
            ESP_LOGE(TAG, "I2S read error: %s", esp_err_to_name(err));
            stats_.i2s_read_errors++;
            vTaskDelay(pdMS_TO_TICKS(10));
            continue;
        }
        
        if (bytes_read == 0) {
            continue;
        }
        
        // Fill frame metadata
        frame->sample_count = bytes_read / sizeof(int16_t);
        frame->timestamp_ms = xTaskGetTickCount() * portTICK_PERIOD_MS;
        frame->sequence_number = sequence_counter_++;
        
        // Calculate audio statistics (RMS level) and apply gain
        int64_t sum_squares = 0;
        int16_t peak = 0;
        
        // Apply gain to samples
        for (size_t i = 0; i < frame->sample_count; i++) {
            // Apply gain
            float amplified = frame->samples[i] * audio_gain_;
            // Clamp to prevent overflow
            if (amplified > 32767.0f) amplified = 32767.0f;
            if (amplified < -32768.0f) amplified = -32768.0f;
            frame->samples[i] = (int16_t)amplified;
            
            // Calculate statistics
            int16_t sample = frame->samples[i];
            sum_squares += (int64_t)sample * sample;
            if (abs(sample) > peak) {
                peak = abs(sample);
            }
        }
        float rms = sqrt((double)sum_squares / frame->sample_count);
        stats_.rms_level_db = 20.0f * log10f(rms / 32768.0f);
        stats_.peak_amplitude = peak / 32768.0f;
        
        stats_.frames_captured++;
        
        // Send frame to queue (non-blocking)
        if (xQueueSend(frame_queue_, &frame, 0) != pdTRUE) {
            // Queue full - buffer overrun
            stats_.buffer_overruns++;
            ESP_LOGW(TAG, "Frame queue full, dropping frame %lu", frame->sequence_number);
        } else {
            // Move to next buffer
            current_buffer_idx = (current_buffer_idx + 1) % AUDIO_BUFFER_COUNT;
        }
    }
    
    ESP_LOGI(TAG, "Audio capture task exiting");
    vTaskDelete(nullptr);
}

bool I2SAudio::getFrame(AudioFrame *frame, uint32_t timeout_ms) {
    if (!frame_queue_) {
        return false;
    }
    
    // Acquire mutex with timeout to avoid deadlock during reconfiguration
    if (xSemaphoreTake(config_mutex_, pdMS_TO_TICKS(100)) != pdTRUE) {
        return false;  // Reconfiguration in progress
    }
    
    AudioFrame *frame_ptr = nullptr;
    bool result = false;
    
    if (xQueueReceive(frame_queue_, &frame_ptr, pdMS_TO_TICKS(timeout_ms)) == pdTRUE) {
        memcpy(frame, frame_ptr, sizeof(AudioFrame));
        result = true;
    }
    
    xSemaphoreGive(config_mutex_);
    return result;
}

void I2SAudio::releaseFrame(AudioFrame *frame) {
    // Frame buffer is managed by pool, no action needed
    // In a more complex implementation, this would return buffer to free pool
}

void I2SAudio::setSampleRate(uint32_t sample_rate) {
    if (sample_rate == sample_rate_) {
        ESP_LOGI(TAG, "Sample rate already %lu Hz", sample_rate);
        return;
    }
    
    // Acquire mutex to prevent concurrent getFrame() calls
    ESP_LOGI(TAG, "Acquiring configuration lock...");
    if (xSemaphoreTake(config_mutex_, pdMS_TO_TICKS(2000)) != pdTRUE) {
        ESP_LOGE(TAG, "Failed to acquire config mutex - timeout");
        return;
    }
    
    ESP_LOGI(TAG, "Changing sample rate from %lu to %lu Hz", sample_rate_, sample_rate);
    
    bool was_running = running_;
    
    // Stop audio capture cleanly
    if (was_running) {
        ESP_LOGI(TAG, "Stopping audio for reconfiguration...");
        stop();
    }
    
    // Uninstall I2S driver
    ESP_LOGI(TAG, "Uninstalling I2S driver...");
    i2s_driver_uninstall(I2S_NUM);
    
    // Update sample rate
    sample_rate_ = sample_rate;
    
    // Reconfigure and reinstall I2S driver with new sample rate
    ESP_LOGI(TAG, "Reinstalling I2S driver with new sample rate...");
    i2s_config_t i2s_config = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
        .sample_rate = sample_rate_,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
        .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
        .communication_format = I2S_COMM_FORMAT_STAND_I2S,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = 4,
        .dma_buf_len = AUDIO_FRAME_SAMPLES,
        .use_apll = false,
        .tx_desc_auto_clear = false,
        .fixed_mclk = 0
    };
    
    i2s_pin_config_t pin_config = {
        .bck_io_num = I2S_SCK_PIN,
        .ws_io_num = I2S_WS_PIN,
        .data_out_num = I2S_PIN_NO_CHANGE,
        .data_in_num = I2S_SD_PIN
    };
    
    esp_err_t err = i2s_driver_install(I2S_NUM, &i2s_config, 0, nullptr);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to reinstall I2S driver: %s", esp_err_to_name(err));
        return;
    }
    
    err = i2s_set_pin(I2S_NUM, &pin_config);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to set I2S pins: %s", esp_err_to_name(err));
        return;
    }
    
    ESP_LOGI(TAG, "I2S driver reconfigured successfully");
    
    // Restart audio capture if it was running
    if (was_running) {
        ESP_LOGI(TAG, "Restarting audio capture...");
        vTaskDelay(pdMS_TO_TICKS(100)); // Give driver time to stabilize
        start();
    }
    
    // Release mutex
    xSemaphoreGive(config_mutex_);
    
    ESP_LOGI(TAG, "Sample rate changed to %lu Hz successfully", sample_rate);
}

uint32_t I2SAudio::getSampleRate() {
    return sample_rate_;
}

void I2SAudio::setGain(float gain) {
    // Clamp to valid range
    if (gain < MIN_AUDIO_GAIN) gain = MIN_AUDIO_GAIN;
    if (gain > MAX_AUDIO_GAIN) gain = MAX_AUDIO_GAIN;
    
    audio_gain_ = gain;
    ESP_LOGI(TAG, "Audio gain set to %.2fx", gain);
}

float I2SAudio::getGain() {
    return audio_gain_;
}


AudioStats I2SAudio::getStats() {
    return stats_;
}

void I2SAudio::resetStats() {
    stats_.frames_captured = 0;
    stats_.buffer_overruns = 0;
    stats_.i2s_read_errors = 0;
}
